# Batcave Portfolio (Next.js + FastAPI)

Batman-inspired dark portfolio frontend with a FastAPI backend, designed to deploy on free Vercel.

## Stack

- Frontend: Next.js 16 App Router + Tailwind CSS
- Backend: FastAPI (async Python) — entry in `api/index.py` (ASGI), run with uvicorn
- LLM: Ollama (OpenAI-compatible) running locally
- Observability: **Langfuse** for LLM traces, generations, and token-usage scoring
- Hosting: Vercel (single project)

> **Backup version (Next.js + Django).** The previous Django + ADRF backend is
> preserved verbatim on the [`nextjs-django`](https://github.com/quocanhto85/Portfolio-Website/tree/nextjs-django)
> branch and remains fully deployable — `git checkout nextjs-django`, or point
> Vercel's Production Branch at it, to run that version instead.

## Local development

### 1) Frontend

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The dev server proxies
`/api/alfred/*`, `/api/health`, and `/api/projects` to the FastAPI backend on
`:8000`.

### 2) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The SQLite schema is created automatically on startup — no migration step.
Try:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/projects`
- `http://127.0.0.1:8000/api/alfred/stats/`
- `http://127.0.0.1:8000/docs` — auto-generated OpenAPI docs (FastAPI)

## 🦇 Alfred — AI Butler

Alfred is the in-page AI butler for the Batcave. He answers visitor questions
about Quoc Anh's projects and resume in formal British English, streaming
tokens live via Server-Sent Events.

### What's under the hood

| Concern | Implementation |
| --- | --- |
| HTTP layer | FastAPI async endpoint (`POST /api/alfred/chat/`) |
| LLM | Ollama OpenAI-compatible API at `http://localhost:11434` |
| Streaming | `StreamingResponse` + SSE (`text/event-stream`) |
| Rate limiting | Sliding-window limiter, in-process store (or Redis when `REDIS_URL` is set) |
| Persistence | SQLAlchemy async — `ChatSession`, `ChatMessage` (SQLite by default) |
| Observability | Langfuse — one trace per request, one `generation` per Ollama call (model, input, output, tokens, latency) |
| Frontend | Floating panel in `src/app/components/Alfred.tsx`, fetch + ReadableStream |

### Run Ollama locally

```bash
brew install ollama         # macOS
ollama serve                # foreground daemon
ollama pull llama3.2:3b     # default model
```

Set `ALFRED_MODEL=phi3:mini` (or any locally pulled model) to swap. If Ollama
is unreachable, Alfred returns a graceful in-character apology over SSE
instead of a 5xx.

### Observability with Langfuse

Alfred reports LLM-shaped telemetry to Langfuse: one trace per HTTP request,
one nested `generation` per Ollama call carrying the model id, input
messages, streamed output, token usage, time-to-first-token, and end-to-end
latency. Rate-limit rejections show up as `WARNING`-level events on the same
trace, so you can spot abuse patterns in the UI without a separate dashboard.

**Use Langfuse Cloud** (fastest path): create a project at
[cloud.langfuse.com](https://cloud.langfuse.com), copy the API keys, then:

```bash
export LANGFUSE_HOST=https://cloud.langfuse.com
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
uvicorn backend.main:app --reload --port 8000
```

**Or run Langfuse locally** in Docker:

```bash
docker compose -f docker-compose.langfuse.yml up -d
# UI → http://localhost:3030 (sign up, create a project, copy keys)
export LANGFUSE_HOST=http://localhost:3030
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
```

If the keys aren't set, the observability layer is a no-op — Alfred runs
exactly the same, you just don't get traces.

## Configuration

Environment variables (see `backend/config.py`):

| Var | Default | Purpose |
| --- | --- | --- |
| `ALFRED_MODEL` | `llama3.2:3b` | Ollama model id |
| `ALFRED_OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `ALFRED_RATE_LIMIT_MAX` | `10` | Requests per window |
| `ALFRED_RATE_LIMIT_WINDOW` | `60` | Window size (seconds) |
| `ALFRED_REQUEST_TIMEOUT` | `60` | Ollama request timeout |
| `ALFRED_CORS_ORIGINS` | `localhost:3000,127.0.0.1:3000` | Comma-separated allow list |
| `DATABASE_URL` | `sqlite+aiosqlite:///./db.sqlite3` | SQLAlchemy async DB URL |
| `REDIS_URL` | _unset_ | If set, swaps the in-process limiter store for Redis |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse endpoint |
| `LANGFUSE_PUBLIC_KEY` | _unset_ | Langfuse public key (disables tracing if unset) |
| `LANGFUSE_SECRET_KEY` | _unset_ | Langfuse secret key |
| `LANGFUSE_ENVIRONMENT` | `local` | Tag for filtering traces by env |

## Deploy to Vercel

`vercel.json` routes `/api/*` to `api/index.py`, which exposes the FastAPI
ASGI `app`. Vercel's Python runtime detects the ASGI callable to support
Alfred's streaming response. Rewrites in `next.config.ts` are dev only —
production traffic is shaped entirely by `vercel.json`.

For deeper architectural notes, see [`ALFRED.md`](./ALFRED.md).
