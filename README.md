# Batcave Portfolio (Next.js + FastAPI)

Batman-inspired dark portfolio frontend with a FastAPI backend, designed to deploy on free Vercel.

## Stack

- Frontend: Next.js 16 App Router + Tailwind CSS
- Backend: FastAPI (async Python) — entry in `api/index.py` (ASGI), run with uvicorn
- LLM: Ollama (OpenAI-compatible) running locally
- Observability: **Langfuse** for LLM traces, generations, and token-usage scoring
- Hosting: Vercel (single project)

> **Backup version (Next.js + Django).** The previous Django + ADRF backend is
> preserved verbatim on the `[nextjs-django](https://github.com/quocanhto85/Portfolio-Website/tree/nextjs-django)`
> branch and remains fully deployable — `git checkout nextjs-django`, or point
> Vercel's Production Branch at it, to run that version instead.

## I. Setting up

### 1) Frontend side

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The dev server proxies
`/api/alfred/*`, `/api/health`, and `/api/projects` to the FastAPI backend on
`:8000`.

### 2) Backend side

#### Django

The previous Django + ADRF backend is preserved on the `nextjs-django` branch.
Use this only when you intentionally want to run that backup version:

```bash
git checkout nextjs-django
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
uvicorn django_portfolio.asgi:application --reload
# or run the WSGI dev server:
python manage.py runserver 8000
```

#### FastAPI

The current `main` branch uses FastAPI. The ASGI app is exposed from
`backend.main:app`, and Vercel uses the same app through `api/index.py`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

FastAPI does not use `manage.py` or Django migrations. The SQLite schema is
created automatically on startup from the FastAPI lifespan hook. Try:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/projects`
- `http://127.0.0.1:8000/api/alfred/stats/`
- `http://127.0.0.1:8000/docs` — auto-generated OpenAPI docs (FastAPI)

## II. Content database (single source of truth)

The resume and articles used to live in `src/data/resume.json` and
`src/data/projects.ts`. They now live in the database, and **the running app
never imports those files again** — they survive only as one-time seed
snapshots under `backend/seed_data/`. The website and Alfred both read from
this one source, so content can't drift between them.

| Concern        | Where                                                                 |
| -------------- | --------------------------------------------------------------------- |
| Tables         | `backend/content_models.py` (resume rows, `Article`, `ArticleBlock`)  |
| Read layer     | `backend/content_service.py` (`get_resume_data`)                      |
| Public API     | `backend/routers/content.py` → `/api/content/*`                       |
| Seed snapshots | `backend/seed_data/{resume.json,articles.json}`                       |

### Seed the content

Load the snapshots into whatever `DATABASE_URL` points at (SQLite in dev, Neon
Postgres in prod). Idempotent — it truncates and re-inserts on every run, so
re-running simply re-syncs the DB to the snapshots (chat tables are untouched):

```bash
# with the venv activated
python -m backend.seed_content
```

The Next.js pages fetch these endpoints at request time (no build-time data):

- `GET /api/content/projects` — article summaries for the home grid
- `GET /api/content/projects/{slug}` — one full article (with content blocks)
- `GET /api/content/resume` — the full resume

## 🦇 Alfred — AI Butler

Alfred is the in-page AI butler for the Batcave. He answers visitor questions
about Quoc Anh's projects and resume in formal British English, streaming
tokens live via Server-Sent Events.

### What's under the hood


| Concern       | Implementation                                                                                             |
| ------------- | ---------------------------------------------------------------------------------------------------------- |
| HTTP layer    | FastAPI async endpoint (`POST /api/alfred/chat/`)                                                          |
| LLM           | Ollama OpenAI-compatible API at `http://localhost:11434`                                                   |
| Knowledge     | Always-on resume (from the content DB) **+ RAG** retrieval from LanceDB (see RAG section below)             |
| Streaming     | `StreamingResponse` + SSE (`text/event-stream`)                                                            |
| Rate limiting | Sliding-window limiter, in-process store (or Redis when `REDIS_URL` is set)                                |
| Persistence   | SQLAlchemy async — `ChatSession`, `ChatMessage` (SQLite by default)                                        |
| Observability | Langfuse — one trace per request, one `generation` per Ollama call (model, input, output, tokens, latency) |
| Frontend      | Floating panel in `src/app/components/Alfred.tsx`, fetch + ReadableStream                                  |


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

## 🧠 Alfred's knowledge — RAG pipeline (LanceDB)

Alfred grounds his answers in two layers:

1. **Always-on resume** — the full resume is read from the content DB and
   placed in every system prompt (it's small and central). See
   `backend/knowledge.py::build_system_prompt`.
2. **Retrieval-augmented context** — for each question, the most relevant
   chunks (article sections, specific roles, projects) are fetched from a
   vector database and appended as extra reference material.

### Two databases, one source of truth

| Database                    | Role                                 | API key?     |
| --------------------------- | ------------------------------------ | ------------ |
| Postgres / SQLite (content) | source of truth (resume, articles)   | `DATABASE_URL` |
| **LanceDB** (vectors)       | derived embeddings for search        | **none**     |

> **LanceDB is self-hosted and has _no_ API key.** It's a library that writes
> vector files to a local folder (`./.lancedb`) in dev, or an S3-compatible
> bucket (Cloudflare R2) in prod. The only key the pipeline needs is the
> **embedding provider** (Jina by default).

### The pipeline

```
INGEST (offline CLI) — load → chunk → embed → store
  DB content ──▶ chunk ──▶ embed (Jina) ──▶ store vectors (LanceDB)
              chunking.py  embeddings.py    vectorstore.py
              └──────────── backend/rag/ingest.py orchestrates ───────────┘

QUERY (per chat message) — embed → retrieve → ground → generate
  question ──▶ embed ──▶ LanceDB top-k ──▶ relevance floor ──▶ Alfred's prompt
            └─ backend/rag/retrieval.py ─┘                  routers/alfred.py
```

### ▶️ Run the ingestion pipeline

This single command runs the whole **load → chunk → embed → store** chain:

```bash
# with the venv activated
python -m backend.rag.ingest
```

It reads the content DB, builds chunks, embeds them with the configured
provider, and **overwrites** the LanceDB table. It's idempotent — re-run it
whenever you change resume/article content (after re-seeding).

**Prerequisites:** (1) content is seeded (`python -m backend.seed_content`),
and (2) `EMBEDDING_API_KEY` is set (next step).

### Get embedding API key (Jina — free, no credit card)

1. Go to **https://jina.ai/embeddings/**
2. Find the **API key** panel — Jina shows a usable key with a free token
   allowance immediately.
3. Sign in (Google/GitHub/email) to claim persistent key with a
   larger free allowance. It looks like `jina_xxxxxxxxxxxxxxxx`.

The defaults already target Jina v3 (1024-dim), so the key is all you add.

### Activate RAG locally

```bash
# 1. Add the key to .env
echo 'EMBEDDING_API_KEY=jina_xxxxxxxxxxxxxxxx' >> .env

# 2. Seed content (if not already done)
python -m backend.seed_content

# 3. Build the vector table
python -m backend.rag.ingest

# 4. Start the backend — Alfred now retrieves automatically
uvicorn backend.main:app --reload --port 8000
```

RAG **self-disables** when `EMBEDDING_API_KEY` is empty (`settings.rag_active`),
so chat keeps working with just the resume — a missing key, missing table, or
provider error never breaks a conversation; it simply skips retrieval.

### `backend/rag/` file map

| File             | Responsibility                                                       |
| ---------------- | -------------------------------------------------------------------- |
| `chunking.py`    | DB rows/blocks → retrievable text chunks (media as metadata only)    |
| `embeddings.py`  | Pluggable, OpenAI-shaped embedder (Jina default)                     |
| `vectorstore.py` | LanceDB wrapper (local dir in dev, R2/S3 in prod)                    |
| `ingest.py`      | CLI: orchestrates load → chunk → embed → store                       |
| `retrieval.py`   | Embed query → top-k → relevance floor → context                      |
| `reranker.py`    | Reranking seam (no-op today; gated by `RAG_RERANK_ENABLED`)          |

### RAG & content configuration

| Var                                        | Default                              | Purpose                                              |
| ------------------------------------------ | ------------------------------------ | ---------------------------------------------------- |
| `EMBEDDING_API_KEY`                        | *unset*                              | Embedding provider key (Jina). **RAG off when empty** |
| `EMBEDDING_API_BASE`                       | `https://api.jina.ai/v1`             | OpenAI-shaped `/embeddings` base URL                 |
| `EMBEDDING_MODEL`                          | `jina-embeddings-v3`                 | Embedding model id                                   |
| `EMBEDDING_DIM`                            | `1024`                               | Vector dimension (must match the model)              |
| `EMBEDDING_QUERY_TASK` / `_PASSAGE_TASK`   | `retrieval.query` / `.passage`       | Jina task hints; clear them for other providers      |
| `LANCEDB_URI`                              | `./.lancedb`                         | Local dir (dev) or `s3://bucket/...` (prod)          |
| `LANCEDB_TABLE`                            | `alfred_chunks`                      | Vector table name                                    |
| `LANCEDB_S3_ENDPOINT`                      | *unset*                              | R2 endpoint (`https://<acct>.r2.cloudflarestorage.com`) |
| `LANCEDB_AWS_ACCESS_KEY_ID` / `_SECRET..`  | *unset*                              | R2 credentials (read only when URI is `s3://`)       |
| `RAG_ENABLED`                              | `true`                               | Master switch                                        |
| `RAG_TOP_K`                                | `5`                                  | Chunks fetched per query                             |
| `RAG_MIN_SCORE`                            | `0.30`                               | Cosine-similarity floor; drops weak matches          |
| `RAG_RERANK_ENABLED`                       | `false`                              | Reranker seam (no-op today)                          |

### Production (Vercel + Neon + R2)

Vercel's filesystem is read-only, so production points at managed services:

1. **Neon Postgres** — set `DATABASE_URL` to the connection string from the Neon
   dashboard. You can paste it **verbatim** (e.g.
   `postgresql://user:pass@host/neondb?sslmode=require`); `backend/database.py`
   normalizes it for the async driver at startup (`postgresql://`→`postgresql+asyncpg://`,
   `sslmode`→asyncpg's `ssl`). For Vercel, prefer Neon's **pooled** endpoint (the
   `-pooler` host) — the prepared-statement cache is already disabled so PgBouncer
   won't throw "prepared statement does not exist".
2. **Cloudflare R2** — `LANCEDB_URI=s3://your-bucket/alfred`,
   `LANCEDB_S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com`, plus the
   R2 access key/secret.
3. Set the same `EMBEDDING_API_KEY` in Vercel's environment variables.
4. Seed + ingest **once** from your machine, with `DATABASE_URL`/`LANCEDB_*`
   pointed at Neon/R2:

   ```bash
   python -m backend.seed_content
   python -m backend.rag.ingest
   ```

At request time Vercel only **reads** vectors from R2 — it never writes, so the
read-only filesystem is a non-issue.

### Maintenance — chat-log retention

Content and vectors are bounded by what you publish; the **chat log**
(`chat_sessions` + `chat_messages`) is the only table that grows with traffic.
Trim it to a retention window so it can't fill a free-tier database:

```bash
python -m backend.prune_chats                 # delete sessions older than 90d
python -m backend.prune_chats --older-than 30d
python -m backend.prune_chats --older-than 12w --dry-run   # preview, no delete
```

Pruning is session-centric — a chat happens in one sitting, so an expired session
is removed in full (its messages first, then the row), against whatever
`DATABASE_URL` points at. It's idempotent and safe to run on a schedule (e.g. a
cron job or a Vercel scheduled function).

## Configuration

Environment variables (see `backend/config.py`). Embedding / LanceDB / RAG
variables are listed in the **RAG pipeline** section above:


| Var                        | Default                            | Purpose                                              |
| -------------------------- | ---------------------------------- | ---------------------------------------------------- |
| `ALFRED_MODEL`             | `llama3.2:3b`                      | Ollama model id                                      |
| `ALFRED_OLLAMA_URL`        | `http://localhost:11434`           | Ollama endpoint                                      |
| `ALFRED_RATE_LIMIT_MAX`    | `10`                               | Requests per window                                  |
| `ALFRED_RATE_LIMIT_WINDOW` | `60`                               | Window size (seconds)                                |
| `ALFRED_REQUEST_TIMEOUT`   | `60`                               | Ollama request timeout                               |
| `ALFRED_CORS_ORIGINS`      | `localhost:3000,127.0.0.1:3000`    | Comma-separated allow list                           |
| `DATABASE_URL`             | `sqlite+aiosqlite:///./db.sqlite3` | SQLAlchemy async DB URL — content (resume/articles) **and** chat logs |
| `REDIS_URL`                | *unset*                            | If set, swaps the in-process limiter store for Redis |
| `LANGFUSE_HOST`            | `https://cloud.langfuse.com`       | Langfuse endpoint                                    |
| `LANGFUSE_PUBLIC_KEY`      | *unset*                            | Langfuse public key (disables tracing if unset)      |
| `LANGFUSE_SECRET_KEY`      | *unset*                            | Langfuse secret key                                  |
| `LANGFUSE_ENVIRONMENT`     | `local`                            | Tag for filtering traces by env                      |


## Deploy to Vercel

`vercel.json` routes `/api/`* to `api/index.py`, which exposes the FastAPI
ASGI `app`. Vercel's Python runtime detects the ASGI callable to support
Alfred's streaming response. Rewrites in `next.config.ts` are dev only —
production traffic is shaped entirely by `vercel.json`.

For deeper architectural notes, see `[ALFRED.md](./ALFRED.md)`.
