# 🦇 Alfred — System Documentation

Alfred is the AI butler embedded in the Batcave portfolio. This document
describes the full system: every component, the technology choices behind
each one, and how they interact end-to-end.

> Goal: a production-shaped LLM serving feature that demonstrates
> async serving, rate limiting, persistence, observability, and a streaming
> UI — all integrated into a single FastAPI + Next.js project, no extra
> services.

> **Backup version.** The earlier Next.js + Django (ADRF) implementation is
> preserved on the `nextjs-django` branch. `main` is the FastAPI version
> documented here.

---

## 1. Architecture at a glance

```
Browser — Next.js 16 / React 19 / Tailwind
  src/app/components/Alfred.tsx
    • Floating bat-icon launcher → slide-up chat panel (380×520)
    • fetch() + ReadableStream → SSE frame parser
    • Per-token append, blinking cursor, rate-limit countdown
        │
        │  POST /api/alfred/chat/   (text/event-stream)
        ▼
FastAPI ASGI app — api/index.py → backend.main:app
  backend/routers/alfred.py · chat()  (native async endpoint)
    1. extract + sha256 client IP
    2. SlidingWindowRateLimiter.check(ip_hash)
    3. get-or-create ChatSession        (SQLAlchemy async)
    4. save user message
    5. httpx.AsyncClient → Ollama /v1/chat/completions (stream=True)
    6. async-iterate Ollama SSE → re-emit as our SSE frames
    7. on completion: persist assistant message + close Langfuse trace
  backend/routers/alfred.py · stats()  (async SQLAlchemy aggregate)

  supporting modules
    backend/rate_limiter.py    in-process dict, or Redis when REDIS_URL is set
    backend/observability.py   Langfuse client (no-op if keys unset)
    backend/models.py          ChatSession, ChatMessage (SQLite via SQLAlchemy)
        │
        ▼
Ollama (OpenAI-compatible) — http://localhost:11434
  Model: ALFRED_MODEL (default llama3.2:3b)

Langfuse (Cloud or local Docker) — traces, generations, token usage, scores
  • Trace per request   • Generation per Ollama call   • Latency score on trace
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

### 2.2 Backend HTTP layer — `backend/routers/alfred.py`

- **Native async FastAPI endpoint** — `chat()` is a plain `async def` handler.
  FastAPI runs it on the event loop, so we `await` the database, the rate
  limiter, and the Ollama client without spawning threads per request.
- **`StreamingResponse(async_generator, media_type="text/event-stream")`**
  — Starlette serializes the async generator chunk-by-chunk under ASGI.
  Headers `Cache-Control: no-cache` and `X-Accel-Buffering: no` defeat
  Nginx/Vercel response buffering. `Connection` is _not_ set because it's a
  hop-by-hop header and is the server's responsibility.
- **CORS** — handled globally by Starlette's `CORSMiddleware`, scoped to the
  configured Next.js origins (`ALFRED_CORS_ORIGINS`). It also answers the
  `OPTIONS` preflight automatically, so the endpoints stay free of CORS code.
- **SQLAlchemy async sessions** — each DB helper opens a short-lived
  `AsyncSession` and `await`s it, so persistence never blocks the event loop.
  The routes register both `/chat/` and `/chat` (and likewise for `/stats`)
  so a POST never trips a trailing-slash redirect.

### 2.3 Sliding-window rate limiter — `backend/rate_limiter.py`

- Storage shape: a list of float epoch timestamps under
  `rl:alfred:{sha256(ip)}`.
- On each call: prune timestamps older than `now - window`, accept iff
  `len < max`, then append `now`.
- **Pluggable store** — an in-process dict by default (dev / single instance /
  serverless), or Redis when `REDIS_URL` is set (shared across instances). The
  same algorithm runs on both because we only read/write a JSON list per key.
  A bare in-memory dict would silently break across more than one uvicorn /
  Vercel worker, which is exactly why Redis is the production path.
- IPs are **always hashed** before they touch storage or metrics — raw IPs
  are never logged, satisfying basic privacy hygiene.

### 2.4 Observability — `backend/observability.py` + Langfuse

We log **LLM-shaped** telemetry rather than generic ops metrics. The
Prometheus-style "requests / latency / saturation" tells you _whether the
service is up_; Langfuse tells you _what the model said, with what input, at
what cost_ — the thing you actually care about when debugging an LLM
feature.

**Per request, Alfred records:**

| Object | Fields | Source |
| --- | --- | --- |
| Trace (parent span `alfred.chat`) | session id, ip-hash prefix, rate-limit headroom | endpoint |
| Generation (`ollama.chat`) | model id, full input messages, streamed output, `usage_details` (input/output tokens), TTFT ms, total latency ms, error level/status | streaming generator |
| Event `rate_limited` | wait seconds, WARNING level | endpoint (denied branch) |
| Score `latency_seconds` | numeric, attached to the trace | post-stream `finally` |

The wrapper [`observability.py`](backend/observability.py) lazily
constructs the singleton client. If `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` are unset, it returns a `NoopClient` so the request
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

### 2.5 Persistence — `backend/models.py`

```
ChatSession(id=UUID, ip_hash, created_at, total_messages)
   └── ChatMessage(role, content, tokens_generated, latency_ms, created_at)
```

- String UUID primary key on session so it's safe to surface in the SSE
  response and portable across SQLite and Postgres.
- IP is hashed once and stored on the session, never on the message.
- `tokens_generated` / `latency_ms` only populated for assistant rows so the
  stats endpoint can compute averages with a single `func.avg` aggregate.

### 2.6 Stats endpoint — `stats()`

`GET /api/alfred/stats/` returns

```json
{ "total_sessions": int, "total_messages": int, "avg_latency_ms": float|null, "persistence": "db"|"ephemeral" }
```

Computed by a single async SQLAlchemy aggregate. `persistence` reports whether
the DB was reachable (`db`) or the request fell back to ephemeral mode
(`ephemeral`). CORS is handled by the same shared `CORSMiddleware` as the
streaming endpoint.

### 2.7 Knowledge — `backend/knowledge.py`

The system prompt is a static string built from `src/data/resume.json` (the
same source the resume page renders from). Static is the right call here
because the whole portfolio fits comfortably under the context window of a 3B
model; swapping in retrieval would be premature. If the corpus grows, replace
with embeddings + pgvector / FAISS.

---

## 3. End-to-end request flow

1. User types a message and hits **TRANSMIT**.
2. The component appends a user bubble + a pending assistant bubble, then
   `fetch`s `POST /api/alfred/chat/` with `{message, session_id}`.
3. Next.js dev rewrites (or Vercel's `vercel.json` rewrite in prod) forward
   to the FastAPI ASGI app.
4. The `chat()` endpoint:
   - extracts the IP from `X-Forwarded-For`, sha256s it,
   - opens a Langfuse parent span `alfred.chat`,
   - asks the limiter — if denied, attaches a `rate_limited` event + ends
     the span at WARNING level, then returns `429` with `wait_seconds`,
   - otherwise `get_or_create_session` + `save_user_message` (async SQLAlchemy),
   - returns a `StreamingResponse` whose body is `alfred_stream(...)`.
5. `alfred_stream`:
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
6. The wrapping `wrapped_stream` ends the parent span and calls
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
| DB unwritable (read-only FS) | Falls back to an ephemeral session; the stream is unaffected and Langfuse stays the durable log. |
| Langfuse unreachable | Wrapper falls back to no-op silently — the user-facing request is unaffected. |

---

## 4. Production considerations

- **ASGI on Vercel.** `api/index.py` exposes the FastAPI ASGI `app`. Vercel's
  Python runtime auto-detects ASGI, which is required for `StreamingResponse`
  to flush incrementally to the client.
- **Rate-limit store.** Set `REDIS_URL` in production so the sliding-window
  state is shared across instances. Without it, the in-process dict is
  per-instance and the limit is effectively N × `ALFRED_RATE_LIMIT_MAX`.
- **Database.** SQLite is fine for a single Vercel function; for multi-worker
  durability switch `DATABASE_URL` to managed Postgres
  (`postgresql+asyncpg://...`). On Vercel the bundled SQLite file is read-only,
  so writes degrade to ephemeral automatically.
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
api/index.py                      # Vercel ASGI entry → backend.main:app
backend/
  __init__.py
  config.py                       # pydantic-settings (env config)
  database.py                     # SQLAlchemy async engine + session + init_db
  models.py                       # ChatSession, ChatMessage
  rate_limiter.py                 # SlidingWindowRateLimiter (in-proc / Redis)
  observability.py                # Langfuse client + no-op shim
  knowledge.py                    # system prompt (from src/data/resume.json)
  main.py                         # FastAPI app: CORS, lifespan, routers
  routers/
    portfolio.py                  # /api/health, /api/projects
    alfred.py                     # /api/alfred/chat/, /api/alfred/stats/
src/app/components/Alfred.tsx     # client component
src/app/page.tsx                  # mounts <Alfred />
next.config.ts                    # dev rewrites + slash handling
docker-compose.langfuse.yml       # local Langfuse self-host
requirements.txt                  # fastapi, uvicorn, sqlalchemy, langfuse, httpx
README.md                         # quickstart + Alfred section
ALFRED.md                         # this document
```

---

## 6. Smoke tests

```bash
# Start the backend first:  uvicorn backend.main:app --reload --port 8000

# Health
curl http://localhost:8000/api/health

# Stats (SQLAlchemy aggregate)
curl http://localhost:8000/api/alfred/stats/

# Streaming chat (without Ollama → graceful fallback frame; without Langfuse
# keys → no traces, endpoint still works)
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
