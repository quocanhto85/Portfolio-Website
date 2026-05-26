"""Langfuse instrumentation for Alfred.

We log LLM-shaped data (traces, generations, token usage, scores) instead of
generic ops metrics. When Langfuse is not configured (no public/secret keys),
this module exposes a no-op client so the request path doesn't break in dev
or in environments where observability is intentionally off.

Public API:
    get_client() -> Langfuse-like object with at least:
        - start_observation(name, as_type, input, metadata) -> Observation
        - flush()
    Observation:
        - start_observation(name, as_type, model, input) -> Observation
        - update(output=, usage_details=, level=, status_message=, metadata=)
        - end()  # in SDK v3+ end() only marks completion; attributes go via update()
        - create_event(name, input=, level=, metadata=)
        - score_trace(name, value, comment=)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_client: Any = None
_initialized = False


# ---------------------------------------------------------------- no-op shim
class _NoopObservation:
    def start_observation(self, *args: Any, **kwargs: Any) -> "_NoopObservation":
        return self

    def update(self, *args: Any, **kwargs: Any) -> None:
        return None

    def end(self, *args: Any, **kwargs: Any) -> None:
        return None

    def create_event(self, *args: Any, **kwargs: Any) -> None:
        return None

    def score_trace(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NoopClient:
    enabled = False

    def start_observation(self, *args: Any, **kwargs: Any) -> _NoopObservation:
        return _NoopObservation()

    def flush(self) -> None:
        return None


# ---------------------------------------------------------------- bootstrap
def get_client() -> Any:
    """Return a singleton Langfuse client, or a no-op when keys aren't set."""
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()

    if not public_key or not secret_key:
        logger.info(
            "Langfuse credentials not set — using no-op observability client."
        )
        _client = _NoopClient()
        return _client

    try:
        from langfuse import Langfuse  # type: ignore

        _client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            release=os.environ.get("LANGFUSE_RELEASE"),
            environment=os.environ.get("LANGFUSE_ENVIRONMENT", "local"),
        )
        # The SDK reports init lazily; force a quick auth probe so misconfig
        # surfaces in logs once at startup rather than per request.
        try:
            _client.auth_check()
        except Exception:  # pragma: no cover - best effort
            logger.exception("Langfuse auth_check failed; continuing anyway")
        logger.info("Langfuse client initialised against %s", host)
        return _client
    except Exception:  # pragma: no cover - SDK import / init failure
        logger.exception(
            "Failed to initialise Langfuse — falling back to no-op client"
        )
        _client = _NoopClient()
        return _client


def flush() -> None:
    client = get_client()
    if hasattr(client, "flush"):
        try:
            client.flush()
        except Exception:  # pragma: no cover
            logger.exception("Langfuse flush failed")


def trace_url(observation: Any) -> Optional[str]:
    """Best-effort: return a Langfuse UI URL for the current trace, if any."""
    try:
        client = get_client()
        if hasattr(client, "get_trace_url"):
            return client.get_trace_url()
    except Exception:  # pragma: no cover
        return None
    return None
