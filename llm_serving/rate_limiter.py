"""Sliding-window rate limiter backed by the Django cache.

Stores the timestamps (epoch seconds, float) of the most recent N requests for
each caller under the key ``rl:alfred:{ip_hash}``. Each check prunes timestamps
older than the window before deciding, so the limit slides continuously rather
than resetting on a fixed boundary.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import List, Tuple

from django.conf import settings
from django.core.cache import cache


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    wait_seconds: int


class SlidingWindowRateLimiter:
    """Token-less sliding window limiter using Django's cache as storage.

    The cache backend is pluggable: LocMemCache for local dev, Redis when
    REDIS_URL is set. The same logic works for both because we only rely on
    ``cache.get`` and ``cache.set``.
    """

    KEY_TEMPLATE = "rl:alfred:{ip_hash}"

    def __init__(self, max_requests: int | None = None, window_seconds: int | None = None) -> None:
        self.max_requests = max_requests or settings.ALFRED_RATE_LIMIT_MAX
        self.window = window_seconds or settings.ALFRED_RATE_LIMIT_WINDOW

    def _key(self, ip_hash: str) -> str:
        return self.KEY_TEMPLATE.format(ip_hash=ip_hash)

    def _load(self, ip_hash: str, now: float) -> List[float]:
        raw = cache.get(self._key(ip_hash)) or []
        cutoff = now - self.window
        return [ts for ts in raw if ts > cutoff]

    def _save(self, ip_hash: str, timestamps: List[float]) -> None:
        # TTL = window so the key expires automatically when no traffic continues.
        cache.set(self._key(ip_hash), timestamps, timeout=self.window)

    def check(self, ip_hash: str) -> RateLimitDecision:
        """Atomic-ish read-modify-write. Records the request iff allowed."""
        now = time.time()
        timestamps = self._load(ip_hash, now)

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            wait = max(1, math.ceil(self.window - (now - oldest)))
            self._save(ip_hash, timestamps)  # persist pruning
            return RateLimitDecision(
                allowed=False,
                remaining=0,
                wait_seconds=wait,
            )

        timestamps.append(now)
        self._save(ip_hash, timestamps)
        return RateLimitDecision(
            allowed=True,
            remaining=max(0, self.max_requests - len(timestamps)),
            wait_seconds=0,
        )

    def is_allowed(self, ip_hash: str) -> Tuple[bool, int]:
        decision = self.check(ip_hash)
        return decision.allowed, decision.remaining

    def get_wait_seconds(self, ip_hash: str) -> int:
        now = time.time()
        timestamps = self._load(ip_hash, now)
        if len(timestamps) < self.max_requests:
            return 0
        oldest = timestamps[0]
        return max(1, math.ceil(self.window - (now - oldest)))
