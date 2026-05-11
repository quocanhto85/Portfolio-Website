# 🦇 Alfred — System Documentation

Alfred is the AI butler embedded in the Batcave portfolio. This document
describes the full system: every component, the technology choices behind
each one, and how they interact end-to-end.

> Goal: a small but production-shaped LLM serving feature that demonstrates
> async serving, rate limiting, persistence, observability, and a streaming
> UI — all integrated into a single Django + Next.js project, no extra
> services.

---

## 1. Architecture at a glance

```
┌──────────────────────────────────────────────────────────────────────┐
│  Browser (Next.js 16, React 19, Tailwind)                            │
│                                                                      │
│   src/app/components/Alfred.tsx                                      │
│     • Floating bat-icon launcher                                     │
│     • Slide-up chat panel (380×520)                                  │
│     • fetch() + ReadableStream → SSE frame parser                    │
│     • Per-token append, blinking cursor, typing dots                 │
│     • Rate-limit countdown UI                                        │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ POST /api/alfred/chat/   (text/event-stream)
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Django ASGI app  (api/index.py → django_portfolio.asgi)             │
│                                                                      │
│   ┌────────────────────────────────────────────────────────────┐     │
│   │  llm_serving/views.py                                      │     │
│   │   AlfredStreamView (adrf.views.APIView, async)             │     │
│   │     1. extract + sha256 IP                                 │     │
│   │     2. SlidingWindowRateLimiter.check(ip_hash)             │     │
│   │     3. get_or_create ChatSession (sync_to_async ORM)       │     │
│   │     4. save user message                                   │     │
│   │     5. open httpx.AsyncClient → Ollama /v1/chat/...        │     │
│   │     6. async-iterate Ollama SSE → re-emit as our SSE       │     │
│   │     7. on completion: persist assistant msg + close trace  │     │
│   │   AlfredStatsView (async ORM aggregate)                    │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌──────────────────────┐   ┌────────────────────────────────┐      │
│   │ rate_limiter.py      │   │ observability.py               │      │
│   │ Django cache-backed  │   │ Langfuse client (no-op if unset)│     │
│   │ (LocMem or Redis)    │   │ trace + generation + score     │      │
│   └──────────────────────┘   └────────────────────────────────┘      │
│                                                                      │
│   ┌────────────────────────────┐                                     │
│   │ models.py: ChatSession,    │                                     │
│   │ ChatMessage  (SQLite)      │                                     │
│   └────────────────────────────┘                                     │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Ollama (OpenAI-compatible) — http://localhost:11434                 │
│  Model: ALFRED_MODEL (default llama3.2:3b)                           │
└──────────────────────────────────────────────────────────────────────┘

           ┌─────────────────────────────────────┐
           │ Langfuse (Cloud or local Docker)    │  traces, generations,
           │  • Trace per request                │  token usage, scores,
           │  • Generation per Ollama call       │  filtered by session,
           │  • Latency score on trace           │  model, environment
           └─────────────────────────────────────┘
```

---

## 2. Component deep-dive

### 2.1 Frontend — `src/app/components/Alfred.tsx`

| Choice | Rationale |
| --- | --- |
| **Client component** (`"use client"`) | Needs state, effects, and `fetch` streaming — pure React; no SSR. |
| **`fetch` + `ReadableStream`** instead of `EventSource` | `EventSource` only supports GET; we POST a JSON body, so we manually parse SSE frames from the response body. |
| **Manual SSE framing** | We split the buffered text on `\n\n`, take the first `data:` line, JSON-parse the payload. This is robust to Ollama-side chunking. |
| **Per-token `setMessages`** | React batches the updates; the user sees streaming token-by-token. |
| **`AbortController`** | Lets us tear down a stream cleanly if the panel closes mid-flight. |
| **Rate-limit ticker via `setInterval`** | One interval that decrements until zero, then nulls the state — single source of truth, no cascading effects. |
| **`crypto.randomUUID()` w/ fallback** | Stable session id per visitor without a backend round-trip. |

### 2.2 Backend HTTP layer — `llm_serving/views.py`

- **ADRF (`adrf.views.APIView`)** — thin wrapper over DRF that lets `post()`
  be `async def`. Lets us `await` the database, the rate limiter, and the
  Ollama client without spawning threads per request.
- **`StreamingHttpResponse(async_generator, content_type="text/event-stream")`**
  — Django 5 serializes the async generator chunk-by-chunk under ASGI.
  Headers `Cache-Control: no-cache` and `X-Accel-Buffering: no` defeat
  Nginx/Vercel response buffering. `Connection` is _not_ set because it's a
  hop-by-hop header and is the server's responsibility.
- **CORS** — small inline helper allows just the configured Next.js origins.
  No `django-cors-headers` dependency since the surface is one endpoint.
- **`sync_to_async`** — Django 5 ORM has limited native async; we wrap the
  read/write helpers so they don't block the event loop. The `.acreate` /
  `.aget` shortcuts are used where they're already async.

### 2.3 Sliding-window rate limiter — `llm_serving/rate_limiter.py`

- Storage shape: a list of float epoch timestamps under
  `rl:alfred:{sha256(ip)}` in the Django cache.
- On each call: prune timestamps older than `now - window`, accept iff
  `len < max`, then append `now`.
- Backed by **Django's cache framework** so the same code runs against
  `LocMemCache` (default for dev) or `RedisCache` (production / multi-worker).
  An in-memory dict would silently break when more than one Gunicorn /
  Vercel worker is in play.
- IPs are **always hashed** before they touch storage or metrics — raw IPs
  are never logged, satisfying basic privacy hygiene.

### 2.4 Observability — `llm_serving/observability.py` + Langfuse

We log **LLM-shaped** telemetry rather than generic ops metrics. The
Prometheus-style "requests / latency / saturation" tells you _whether the
service is up_; Langfuse tells you _what the model said, with what input, at
what cost_ — the thing you actually care about when debugging an LLM
feature.

**Per request, Alfred records:**

| Object | Fields | Source |
| --- | --- | --- |
| Trace (parent span `alfred.chat`) | session id, ip-hash prefix, rate-limit headroom | view |
| Generation (`ollama.chat`) | model id, full input messages, streamed output, `usage_details` (input/output tokens), TTFT ms, total latency ms, error level/status | streaming generator |
| Event `rate_limited` | wait seconds, WARNING level | view (denied branch) |
| Score `latency_seconds` | numeric, attached to the trace | post-stream `finally` |

The wrapper [`observability.py`](llm_serving/observability.py) lazily
constructs the singleton client. If `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` are unset, it returns a `_NoopClient` so the request
path keeps working in dev / CI / on Vercel preview branches without exposing
keys.

**Why this beats Prometheus for Alfred specifically:**

- Each row in the Langfuse UI is one user interaction with the model — you
  can read the prompt, the streamed answer, and the token counts together.
  In Prometheus that data is splintered across counters and histograms and
  isn't replayable.
- Token usage and latency are surfaced as first-class fields rather than
  custom labels — Langfuse already has dashboards for them.
- Errors (Ollama down, model returning gibberish) surface as ERROR-level
  observations on the same trace as the prompt, which is exactly what you
  want when triaging.
- No scrape endpoint required — the SDK batches and ships over HTTPS, so
  Vercel serverless functions can ship traces without a long-lived
  scraper.

### 2.5 Persistence — `llm_serving/models.py`

```
ChatSession(id=UUID, ip_hash, created_at, total_messages)
   └── ChatMessage(role, content, tokens_generated, latency_ms, created_at)
```

- UUID primary key on session so it's safe to surface in the SSE response.
- IP is hashed once and stored on the session, never on the message.
- `tokens_generated` / `latency_ms` only populated for assistant rows so
  `AlfredStatsView` can compute averages with a single ORM `Avg` aggregate.

### 2.6 Stats endpoint — `AlfredStatsView`

`GET /api/alfred/stats/` returns

```json
{ "total_sessions": int, "total_messages": int, "avg_latency_ms": float|null }
```

Computed by a single async ORM aggregate; not particularly large, but
demonstrates async ORM + JSON response wrapped in CORS headers identical to
the streaming endpoint.

### 2.7 Knowledge — `llm_serving/knowledge.py`

The system prompt is a static string. Static is the right call here because
the whole portfolio fits comfortably under the context window of a 3B model;
swapping in retrieval would be premature. If the corpus grows, replace with
embeddings + pgvector / FAISS.

---

## 3. End-to-end request flow

1. User types a message and hits **TRANSMIT**.
2. The component appends a user bubble + a pending assistant bubble, then
   `fetch`s `POST /api/alfred/chat/` with `{message, session_id}`.
3. Next.js dev rewrites (or Vercel's `vercel.json` rewrite in prod) forward
   to Django ASGI.
4. `AlfredStreamView.post`:
   - extracts the IP from `X-Forwarded-For`, sha256s it,
   - opens a Langfuse parent span `alfred.chat`,
   - asks the limiter — if denied, attaches a `rate_limited` event + ends
     the span at WARNING level, then returns `429` with `wait_seconds`,
   - otherwise `_get_or_create_session` + `_save_user_message` (async ORM),
   - returns a `StreamingHttpResponse` whose body is `_alfred_stream(...)`.
5. `_alfred_stream`:
   - opens a child `generation` observation on the parent span with
     `model=ALFRED_MODEL` and the full input messages,
   - opens an `httpx.AsyncClient` POST to Ollama with `stream=True`,
   - parses `data: {...}` JSON deltas from Ollama's OpenAI-compat stream,
   - yields our own SSE frames `{"token": "...", "done": false}`,
   - on completion yields `{"token": "", "done": true, "session_id": ..., "tokens": N, "latency_ms": L}`,
   - persists the assistant message,
   - in `finally`: closes the generation with the accumulated output, token
     `usage_details`, and TTFT/latency metadata; attaches a `latency_seconds`
     score on the trace.
6. The wrapping `_wrapped_stream` ends the parent span and calls
   `langfuse.flush()` once the response is fully drained.
7. The browser reads the body, splits on `\n\n`, and appends each token to
   the current assistant bubble; on `done` it locks the bubble and unlocks
   the input.

### Failure paths

| Condition | Behavior |
| --- | --- |
| Ollama refused / timed out | One terminal SSE frame: `{"error": "Alfred is temporarily unavailable", "done": true}`. Generation closes at ERROR level with `status_message=ollama_unreachable: ...`. |
| Ollama returned non-200 | Same as above; `status_message=ollama_http_{code}`. |
| Rate limit hit | HTTP `429` JSON `{error, wait_seconds, retry_after}` + `Retry-After` header; parent span ends at WARNING with a `rate_limited` event. |
| Network drop mid-stream | Browser `AbortError` → terminal in-character message; generation + parent span still close in `finally`. |
| Empty / oversized message | HTTP `400` before any Langfuse work happens. |
| Langfuse unreachable | Wrapper falls back to no-op silently — the user-facing request is unaffected. |

---

## 4. Production considerations

- **ASGI on Vercel.** `api/index.py` exposes both ASGI (`app`) and WSGI
  (`application`). Vercel's Python runtime auto-detects ASGI from the
  signature, which is required for `StreamingHttpResponse` to flush
  incrementally to the client.
- **Cache backend.** Set `REDIS_URL` in production so the sliding-window
  state is shared across workers. Without it, `LocMemCache` is per-worker
  and the limit is effectively N × `ALFRED_RATE_LIMIT_MAX`.
- **Database.** SQLite is fine for a single Vercel function; for multi-worker
  durability switch `DATABASES` to managed Postgres.
- **Buffering.** `X-Accel-Buffering: no` defeats Nginx; on Vercel, the
  Python runtime streams unbuffered when the response is `text/event-stream`.
- **Privacy.** IPs are hashed before storage. Only the first 8 chars of the
  hash are attached to Langfuse traces (as `ip_hash_prefix`), so even the
  trace database never sees a recoverable identifier.
- **Langfuse keys.** In production, set `LANGFUSE_PUBLIC_KEY` and
  `LANGFUSE_SECRET_KEY` as Vercel environment variables. Without them the
  observability layer is a safe no-op.
- **Cost / abuse.** The rate limiter is the first line of defense; the
  next step would be a token-budget per session.

---

## 5. Files added or changed

```
api/index.py                                        # ASGI + WSGI
django_portfolio/asgi.py                            # ASGI module
django_portfolio/settings.py                        # apps, cache, Alfred config
portfolio_api/urls.py                               # mount /api/alfred/
llm_serving/                                        # new app
  __init__.py
  apps.py
  knowledge.py                                      # system prompt
  models.py                                         # ChatSession, ChatMessage
  rate_limiter.py                                   # SlidingWindowRateLimiter
  observability.py                                  # Langfuse client + no-op shim
  urls.py                                           # /chat /stats
  views.py                                          # AlfredStreamView, AlfredStatsView
  migrations/0001_initial.py
src/app/components/Alfred.tsx                       # client component
src/app/page.tsx                                    # mounts <Alfred />
next.config.ts                                      # dev rewrites + slash handling
docker-compose.langfuse.yml                         # local Langfuse self-host
requirements.txt                                    # adrf, drf, langfuse, redis, httpx
README.md                                           # quickstart + Alfred section
ALFRED.md                                           # this document
```

---

## 6. Smoke tests

```bash
# Health (existing)
curl http://localhost:8000/api/health

# Stats (ORM aggregate)
curl http://localhost:8000/api/alfred/stats/

# Streaming chat (without Ol`lama → graceful fallback frame; without Langfuse keys
# → no traces, view still works)
curl -N -X POST http://localhost:8000/api/alfred/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello Alfred"}'

# Rate limit (>10 within 60s)
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST http://localhost:8000/api/alfred/chat/ \
    -H "Content-Type: application/json" -d '{"message":"hi"}';
done
echo
# → 200 200 200 200 200 200 200 200 200 200 429 429
```
