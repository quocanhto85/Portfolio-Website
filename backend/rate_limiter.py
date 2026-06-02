"""Sliding-window rate limiter.

Stores the timestamps (epoch seconds, float) of the most recent N requests for
each caller. Each check prunes timestamps older than the window before
deciding, so the limit slides continuously rather than resetting on a fixed
boundary.

Storage is pluggable: an in-process dict for local dev / single-instance and
serverless (matches the old Django LocMemCache behaviour), or Redis when
``REDIS_URL`` is set (shared across instances). The same algorithm runs on
both because we only read and write a JSON list of timestamps per key.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass

from .config import settings

try:  # redis is a declared dependency; guard import defensively all the same
    import redis.asyncio as aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

_redis = (
    aioredis.from_url(settings.redis_url, decode_responses=True)
    if settings.redis_url and aioredis is not None
    else None
)

# Process-local fallback store: {ip_hash: [timestamp, ...]}.
_MEMORY: dict[str, list[float]] = {}


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    wait_seconds: int


class SlidingWindowRateLimiter:
    KEY_TEMPLATE = "rl:alfred:{ip_hash}"

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        self.max_requests = max_requests or settings.alfred_rate_limit_max
        self.window = window_seconds or settings.alfred_rate_limit_window

    def _key(self, ip_hash: str) -> str:
        return self.KEY_TEMPLATE.format(ip_hash=ip_hash)

    def _decide(self, timestamps: list[float], now: float) -> tuple[RateLimitDecision, list[float]]:
        """Pure decision over already-pruned timestamps; returns the list to persist."""
        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            wait = max(1, math.ceil(self.window - (now - oldest)))
            return (
                RateLimitDecision(allowed=False, remaining=0, wait_seconds=wait),
                timestamps,
            )
        timestamps.append(now)
        return (
            RateLimitDecision(
                allowed=True,
                remaining=max(0, self.max_requests - len(timestamps)),
                wait_seconds=0,
            ),
            timestamps,
        )

    async def check(self, ip_hash: str) -> RateLimitDecision:
        """Read-modify-write. Records the request iff allowed."""
        now = time.time()
        cutoff = now - self.window

        if _redis is not None:
            key = self._key(ip_hash)
            raw = await _redis.get(key)
            stored = json.loads(raw) if raw else []
            timestamps = [ts for ts in stored if ts > cutoff]
            decision, to_save = self._decide(timestamps, now)
            await _redis.set(key, json.dumps(to_save), ex=self.window)
            return decision

        # In-process path. No awaits between read and write, so the event loop
        # can't interleave another coroutine mid-update.
        stored = _MEMORY.get(ip_hash, [])
        timestamps = [ts for ts in stored if ts > cutoff]
        decision, to_save = self._decide(timestamps, now)
        _MEMORY[ip_hash] = to_save
        return decision
