"""Reranking seam (Phase 5). A no-op today.

Vector search alone ranks by embedding similarity; a cross-encoder reranker
(e.g. Jina's rerank API) usually sharpens the top results. That's deferred, so
``get_reranker`` returns an identity reranker. It's wired into the retrieval
path so swapping in a real one is a one-line change here, gated on
``RAG_RERANK_ENABLED``.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


class NoopReranker:
    async def rerank(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return results


def get_reranker() -> NoopReranker:
    if settings.rag_rerank_enabled:
        logger.warning(
            "RAG_RERANK_ENABLED is set but no reranker is configured; "
            "preserving vector-search order."
        )
    return NoopReranker()
