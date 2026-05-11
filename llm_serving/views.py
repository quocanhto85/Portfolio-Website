"""Alfred SSE streaming endpoint and stats endpoint.

Implementation notes:
- ``AlfredStreamView`` is an ADRF ``AsyncAPIView``. ADRF lets DRF play nicely
  with native async views so we can ``await`` httpx and ``async for`` the
  StreamingHttpResponse generator without burning a thread per request.
- The Ollama OpenAI-compatible endpoint emits ``data: ...\\n\\n`` chunks; we
  re-encode them as our own (smaller, JSON-shaped) SSE protocol so the
  frontend never has to know about Ollama internals.
- Observability is LLM-shaped via Langfuse: one parent span per HTTP request,
  one nested ``generation`` for the Ollama call (with model id, input
  messages, token usage, and end-to-end latency). When Langfuse credentials
  are not set the client is a no-op so dev still works.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from typing import AsyncIterator, Optional

import httpx
from adrf.views import APIView as AsyncAPIView
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import DatabaseError, OperationalError
from django.db.models import Avg
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from .knowledge import SYSTEM_PROMPT
from .models import ChatMessage, ChatSession
from .observability import flush as lf_flush, get_client as get_lf_client
from .rate_limiter import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)

# Tuple of ORM exceptions we want to gracefully degrade on. Hit when the
# database is read-only (Vercel filesystem), missing (no migrations on a
# fresh serverless deploy), or otherwise unavailable.
_DB_ERRORS = (OperationalError, DatabaseError)


class _EphemeralSession:
    """In-memory stand-in for ChatSession when the DB isn't writable.

    Carries the bare minimum the streaming path needs: a stringifiable id and
    an ip_hash. Langfuse remains the durable conversation log.
    """

    __slots__ = ("id", "pk", "ip_hash", "total_messages")

    def __init__(self, ip_hash: str) -> None:
        self.id = uuid.uuid4()
        self.pk = self.id
        self.ip_hash = ip_hash
        self.total_messages = 0


# --- helpers ----------------------------------------------------------------

def _client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


def _cors_headers(request) -> dict:
    origin = request.META.get("HTTP_ORIGIN", "")
    allowed = origin if origin in settings.ALFRED_CORS_ORIGINS else ""
    headers = {
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
    }
    if allowed:
        headers["Access-Control-Allow-Origin"] = allowed
    return headers


@sync_to_async
def _get_or_create_session(session_id: Optional[str], ip_hash: str):
    """Return a ChatSession from the DB if reachable, else an EphemeralSession.

    Vercel's filesystem is read-only outside /tmp, so SQLite writes fail there.
    We log once and fall through; the request continues unaffected.
    """
    try:
        if session_id:
            try:
                return ChatSession.objects.get(id=session_id)
            except (ChatSession.DoesNotExist, ValueError):
                pass
        return ChatSession.objects.create(ip_hash=ip_hash)
    except _DB_ERRORS as exc:
        logger.warning("DB unavailable; using ephemeral session (%s)", exc)
        return _EphemeralSession(ip_hash)


@sync_to_async
def _save_user_message(session, content: str) -> None:
    if isinstance(session, _EphemeralSession):
        return
    try:
        ChatMessage.objects.create(
            session=session, role=ChatMessage.ROLE_USER, content=content
        )
        ChatSession.objects.filter(pk=session.pk).update(
            total_messages=session.total_messages + 1
        )
    except _DB_ERRORS as exc:
        logger.warning("Skipping user-message persistence: %s", exc)


@sync_to_async
def _save_assistant_message(
    session, content: str, tokens: int, latency_ms: int
) -> None:
    if isinstance(session, _EphemeralSession):
        return
    try:
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
            content=content,
            tokens_generated=tokens,
            latency_ms=latency_ms,
        )
        ChatSession.objects.filter(pk=session.pk).update(
            total_messages=session.total_messages + 1
        )
    except _DB_ERRORS as exc:
        logger.warning("Skipping assistant-message persistence: %s", exc)


# --- streaming generator ----------------------------------------------------

async def _alfred_stream(
    user_message: str,
    session: ChatSession,
    parent_span,
) -> AsyncIterator[bytes]:
    """Open an Ollama streaming completion and re-emit it as SSE.

    Always yields a terminal ``done`` event, even on failure, so the frontend
    can cleanly close its EventSource handler without timing out.

    Token usage and latency are reported to Langfuse as a ``generation``
    observation under ``parent_span``.
    """
    start = time.perf_counter()
    collected: list[str] = []
    tokens = 0
    first_token_at: Optional[float] = None
    status_message: Optional[str] = None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    generation = parent_span.start_observation(
        name="ollama.chat",
        as_type="generation",
        model=settings.ALFRED_MODEL,
        input=messages,
        model_parameters={"stream": True},
        metadata={"provider": "ollama", "endpoint": settings.ALFRED_OLLAMA_URL},
    )

    payload = {
        "model": settings.ALFRED_MODEL,
        "stream": True,
        "messages": messages,
    }

    headers: dict[str, str] = {}
    if settings.ALFRED_API_KEY:
        # Same Bearer-token shape works for Groq, OpenAI, Together, Fireworks,
        # and anything else that speaks the OpenAI chat-completions protocol.
        headers["Authorization"] = f"Bearer {settings.ALFRED_API_KEY}"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.ALFRED_REQUEST_TIMEOUT, connect=5.0),
        ) as client:
            url = f"{settings.ALFRED_OLLAMA_URL.rstrip('/')}/v1/chat/completions"
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    logger.warning(
                        "Ollama returned %s: %s", resp.status_code, body[:200]
                    )
                    status_message = f"ollama_http_{resp.status_code}"
                    yield _sse(
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
                    yield _sse({"token": delta, "done": False})
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
        logger.warning("Ollama unreachable: %s", exc)
        status_message = f"ollama_unreachable: {type(exc).__name__}"
        yield _sse({"error": "Alfred is temporarily unavailable", "done": True})
        return
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error during Alfred stream")
        status_message = f"unexpected: {type(exc).__name__}"
        yield _sse({"error": "Alfred is temporarily indisposed", "done": True})
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
                "input": len(SYSTEM_PROMPT.split()) + len(user_message.split()),
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
            generation.end(**gen_kwargs)
        except Exception:  # pragma: no cover
            logger.exception("Langfuse generation.end failed")

        if full_text:
            await _save_assistant_message(session, full_text, tokens, latency_ms)

        # Latency score so it's filterable in the Langfuse UI.
        try:
            parent_span.score_trace(
                name="latency_seconds", value=latency_ms / 1000.0
            )
        except Exception:  # pragma: no cover
            pass

    yield _sse(
        {
            "token": "",
            "done": True,
            "session_id": str(session.id),
            "tokens": tokens,
            "latency_ms": latency_ms,
        }
    )


# --- views ------------------------------------------------------------------

class AlfredStreamView(AsyncAPIView):
    """POST /api/alfred/chat/ — SSE-streamed reply from Alfred."""

    authentication_classes: list = []
    permission_classes: list = []

    async def options(self, request, *args, **kwargs):  # CORS preflight
        resp = Response(status=status.HTTP_204_NO_CONTENT)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    async def post(self, request, *args, **kwargs):
        body = request.data if isinstance(request.data, dict) else {}
        print('body: ', body)
        message = (body.get("message") or "").strip()
        session_id = body.get("session_id")

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(message) > 2000:
            return Response(
                {"error": "message too long (2000 char max)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip_hash = _hash_ip(_client_ip(request))
        limiter = SlidingWindowRateLimiter()
        decision = limiter.check(ip_hash)

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
        
        print('request_span: ', request_span)

        if not decision.allowed:
            try:
                request_span.create_event(
                    name="rate_limited",
                    input={"wait_seconds": decision.wait_seconds},
                    level="WARNING",
                )
                request_span.end(
                    output={"status": "rate_limited"},
                    level="WARNING",
                    status_message="rate_limit_exceeded",
                )
                lf_flush()
            except Exception:  # pragma: no cover
                logger.exception("Langfuse error during rate-limit branch")

            resp = JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "wait_seconds": decision.wait_seconds,
                    "retry_after": decision.wait_seconds,
                },
                status=429,
            )
            resp["Retry-After"] = str(decision.wait_seconds)
            for k, v in _cors_headers(request).items():
                resp[k] = v
            return resp

        session = await _get_or_create_session(session_id, ip_hash)
        await _save_user_message(session, message)

        # Add the resolved session id once we have it so it groups in Langfuse.
        try:
            request_span.update(
                metadata={
                    "session_id": str(session.id),
                    "ip_hash_prefix": ip_hash[:8],
                }
            )
        except Exception:  # pragma: no cover
            pass

        async def _wrapped_stream() -> AsyncIterator[bytes]:
            try:
                async for chunk in _alfred_stream(message, session, request_span):
                    yield chunk
            finally:
                try:
                    request_span.end(output={"status": "ok"})
                except Exception:  # pragma: no cover
                    pass
                lf_flush()

        response = StreamingHttpResponse(
            _wrapped_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        for k, v in _cors_headers(request).items():
            response[k] = v
        return response


class AlfredStatsView(AsyncAPIView):
    """GET /api/alfred/stats/ — lightweight ORM-aggregated stats."""

    authentication_classes: list = []
    permission_classes: list = []

    @sync_to_async
    def _gather(self) -> dict:
        try:
            total_sessions = ChatSession.objects.count()
            total_messages = ChatMessage.objects.count()
            avg_latency = ChatMessage.objects.filter(
                role=ChatMessage.ROLE_ASSISTANT, latency_ms__isnull=False
            ).aggregate(avg=Avg("latency_ms"))["avg"]
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_latency_ms": round(avg_latency, 2) if avg_latency else None,
                "persistence": "db",
            }
        except _DB_ERRORS as exc:
            logger.warning("Stats: DB unavailable (%s)", exc)
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_latency_ms": None,
                "persistence": "ephemeral",
            }

    async def get(self, request, *args, **kwargs):
        data = await self._gather()
        resp = JsonResponse(data)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp
