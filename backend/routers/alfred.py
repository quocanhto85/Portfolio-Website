"""Alfred SSE streaming endpoint and stats endpoint (FastAPI).

Implementation notes:
- ``chat`` is a native async FastAPI endpoint. It ``await``s httpx and returns
  a ``StreamingResponse`` whose async generator re-encodes Ollama's chunks as
  our own (smaller, JSON-shaped) SSE protocol, so the frontend never has to
  know about Ollama internals.
- Observability is LLM-shaped via Langfuse: one parent span per HTTP request,
  one nested ``generation`` for the Ollama call (model id, input messages,
  token usage, end-to-end latency). When Langfuse credentials are not set the
  client is a no-op so dev still works.
- Persistence is SQLAlchemy async. When the DB is unwritable (Vercel's
  read-only filesystem, missing schema) we fall back to an ephemeral session;
  Langfuse remains the durable conversation log.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from typing import AsyncIterator, Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from ..config import settings
from ..database import AsyncSessionLocal
from ..knowledge import build_system_prompt
from ..models import ChatMessage, ChatSession
from ..observability import flush as lf_flush, get_client as get_lf_client
from ..rag.retrieval import format_context, retrieve
from ..rate_limiter import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alfred")


class EphemeralSession:
    """In-memory stand-in for ChatSession when the DB isn't writable.

    Carries the bare minimum the streaming path needs: a stringifiable id and
    an ip_hash. Langfuse remains the durable conversation log.
    """

    __slots__ = ("id", "ip_hash", "total_messages")

    def __init__(self, ip_hash: str) -> None:
        self.id = str(uuid.uuid4())
        self.ip_hash = ip_hash
        self.total_messages = 0


# --- helpers ----------------------------------------------------------------

def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


async def get_or_create_session(session_id: Optional[str], ip_hash: str):
    """Return a ChatSession from the DB if reachable, else an EphemeralSession.

    Vercel's filesystem is read-only outside /tmp, so SQLite writes fail there.
    We log once and fall through; the request continues unaffected.
    """
    try:
        async with AsyncSessionLocal() as db:
            if session_id:
                existing = await db.get(ChatSession, str(session_id))
                if existing is not None:
                    return existing
            obj = ChatSession(ip_hash=ip_hash)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
    except SQLAlchemyError as exc:
        logger.warning("DB unavailable; using ephemeral session (%s)", exc)
        return EphemeralSession(ip_hash)


async def save_user_message(session, content: str) -> None:
    if isinstance(session, EphemeralSession):
        return
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                ChatMessage(
                    session_id=session.id,
                    role=ChatMessage.ROLE_USER,
                    content=content,
                )
            )
            await db.execute(
                update(ChatSession)
                .where(ChatSession.id == session.id)
                .values(total_messages=ChatSession.total_messages + 1)
            )
            await db.commit()
    except SQLAlchemyError as exc:
        logger.warning("Skipping user-message persistence: %s", exc)


async def save_assistant_message(
    session, content: str, tokens: int, latency_ms: int
) -> None:
    if isinstance(session, EphemeralSession):
        return
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                ChatMessage(
                    session_id=session.id,
                    role=ChatMessage.ROLE_ASSISTANT,
                    content=content,
                    tokens_generated=tokens,
                    latency_ms=latency_ms,
                )
            )
            await db.execute(
                update(ChatSession)
                .where(ChatSession.id == session.id)
                .values(total_messages=ChatSession.total_messages + 1)
            )
            await db.commit()
    except SQLAlchemyError as exc:
        logger.warning("Skipping assistant-message persistence: %s", exc)


# --- streaming generator ----------------------------------------------------

async def alfred_stream(
    user_message: str,
    session,
    parent_span,
    system_prompt: str,
) -> AsyncIterator[bytes]:
    """Open an Ollama streaming completion and re-emit it as SSE.

    Always yields a terminal ``done`` event, even on failure, so the frontend
    can cleanly close its reader without timing out.

    Token usage and latency are reported to Langfuse as a ``generation``
    observation under ``parent_span``.
    """
    start = time.perf_counter()
    collected: list[str] = []
    tokens = 0
    first_token_at: Optional[float] = None
    status_message: Optional[str] = None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    generation = parent_span.start_observation(
        name="ollama.chat",
        as_type="generation",
        model=settings.alfred_model,
        input=messages,
        model_parameters={"stream": True},
        metadata={"provider": "ollama", "endpoint": settings.alfred_ollama_url},
    )

    payload = {
        "model": settings.alfred_model,
        "stream": True,
        "messages": messages,
    }

    headers: dict[str, str] = {}
    if settings.alfred_api_key:
        # Same Bearer-token shape works for Groq, OpenAI, Together, Fireworks,
        # and anything else that speaks the OpenAI chat-completions protocol.
        headers["Authorization"] = f"Bearer {settings.alfred_api_key}"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.alfred_request_timeout, connect=5.0),
        ) as client:
            url = f"{settings.alfred_ollama_url.rstrip('/')}/v1/chat/completions"
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    logger.warning(
                        "Ollama returned %s: %s", resp.status_code, body[:200]
                    )
                    status_message = f"ollama_http_{resp.status_code}"
                    yield sse(
                        {
                            "error": "Alfred is temporarily unavailable",
                            "done": True,
                        }
                    )
                    return

                async for raw in resp.aiter_lines():
                    if not raw or not raw.startswith("data:"):
                        continue
                    data = raw[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if not delta:
                        continue
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    tokens += 1
                    collected.append(delta)
                    yield sse({"token": delta, "done": False})
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
        logger.warning("Ollama unreachable: %s", exc)
        status_message = f"ollama_unreachable: {type(exc).__name__}"
        yield sse({"error": "Alfred is temporarily unavailable", "done": True})
        return
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error during Alfred stream")
        status_message = f"unexpected: {type(exc).__name__}"
        yield sse({"error": "Alfred is temporarily indisposed", "done": True})
        return
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        ttft_ms = (
            int((first_token_at - start) * 1000) if first_token_at else None
        )
        full_text = "".join(collected)

        # Always close the generation so Langfuse doesn't leak open observations.
        gen_kwargs = {
            "output": full_text or None,
            "usage_details": {
                "input": len(system_prompt.split()) + len(user_message.split()),
                "output": tokens,
            },
            "metadata": {
                "latency_ms": latency_ms,
                "ttft_ms": ttft_ms,
                "completed": status_message is None,
            },
        }
        if status_message:
            gen_kwargs["level"] = "ERROR"
            gen_kwargs["status_message"] = status_message
        try:
            # Langfuse SDK v3+ split: attributes go through .update(), .end()
            # only marks completion (it accepts end_time at most).
            generation.update(**gen_kwargs)
            generation.end()
        except Exception:  # pragma: no cover
            logger.exception("Langfuse generation.end failed")

        if full_text:
            await save_assistant_message(session, full_text, tokens, latency_ms)

        # Latency score so it's filterable in the Langfuse UI.
        try:
            parent_span.score_trace(
                name="latency_seconds", value=latency_ms / 1000.0
            )
        except Exception:  # pragma: no cover
            pass

    yield sse(
        {
            "token": "",
            "done": True,
            "session_id": str(session.id),
            "tokens": tokens,
            "latency_ms": latency_ms,
        }
    )


# --- routes -----------------------------------------------------------------

@router.post("/chat/")
@router.post("/chat", include_in_schema=False)
async def chat(request: Request):
    """POST /api/alfred/chat/ — SSE-streamed reply from Alfred."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    message = (body.get("message") or "").strip()
    session_id = body.get("session_id")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)
    if len(message) > 2000:
        return JSONResponse(
            {"error": "message too long (2000 char max)"}, status_code=400
        )

    ip_hash = hash_ip(client_ip(request))
    limiter = SlidingWindowRateLimiter()
    decision = await limiter.check(ip_hash)

    lf = get_lf_client()
    request_span = lf.start_observation(
        name="alfred.chat",
        as_type="span",
        input={"message": message},
        metadata={
            "ip_hash_prefix": ip_hash[:8],
            "session_id_in": session_id,
            "rate_limit_remaining": decision.remaining,
        },
    )

    if not decision.allowed:
        try:
            request_span.create_event(
                name="rate_limited",
                input={"wait_seconds": decision.wait_seconds},
                level="WARNING",
            )
            request_span.update(
                output={"status": "rate_limited"},
                level="WARNING",
                status_message="rate_limit_exceeded",
            )
            request_span.end()
            lf_flush()
        except Exception:  # pragma: no cover
            logger.exception("Langfuse error during rate-limit branch")

        return JSONResponse(
            {
                "error": "Rate limit exceeded",
                "wait_seconds": decision.wait_seconds,
                "retry_after": decision.wait_seconds,
            },
            status_code=429,
            headers={"Retry-After": str(decision.wait_seconds)},
        )

    session = await get_or_create_session(session_id, ip_hash)
    await save_user_message(session, message)

    # RAG: fetch the chunks most relevant to this question (resume + articles).
    # Degrades to [] when retrieval is disabled/unconfigured, so chat still runs.
    retrieved = await retrieve(message)
    system_prompt = await build_system_prompt(format_context(retrieved))

    # Add the resolved session id once we have it so it groups in Langfuse.
    try:
        request_span.update(
            metadata={
                "session_id": str(session.id),
                "ip_hash_prefix": ip_hash[:8],
                "rag_chunks": len(retrieved),
            }
        )
    except Exception:  # pragma: no cover
        pass

    async def wrapped_stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in alfred_stream(
                message, session, request_span, system_prompt
            ):
                yield chunk
        finally:
            try:
                request_span.update(output={"status": "ok"})
                request_span.end()
            except Exception:  # pragma: no cover
                pass
            lf_flush()

    return StreamingResponse(
        wrapped_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/stats/")
@router.get("/stats", include_in_schema=False)
async def stats():
    """GET /api/alfred/stats/ — lightweight aggregated stats."""
    try:
        async with AsyncSessionLocal() as db:
            total_sessions = await db.scalar(
                select(func.count()).select_from(ChatSession)
            )
            total_messages = await db.scalar(
                select(func.count()).select_from(ChatMessage)
            )
            avg_latency = await db.scalar(
                select(func.avg(ChatMessage.latency_ms)).where(
                    ChatMessage.role == ChatMessage.ROLE_ASSISTANT,
                    ChatMessage.latency_ms.is_not(None),
                )
            )
            return {
                "total_sessions": total_sessions or 0,
                "total_messages": total_messages or 0,
                "avg_latency_ms": round(avg_latency, 2) if avg_latency else None,
                "persistence": "db",
            }
    except SQLAlchemyError as exc:
        logger.warning("Stats: DB unavailable (%s)", exc)
        return {
            "total_sessions": 0,
            "total_messages": 0,
            "avg_latency_ms": None,
            "persistence": "ephemeral",
        }
