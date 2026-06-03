"""Query-time retrieval: embed the question, fetch top-k, drop weak matches.

This is additive grounding. ``retrieve`` never raises — any failure (no key,
missing table, provider error) is logged and yields an empty list, so Alfred
falls back to his always-on resume context instead of erroring the chat.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from ..config import settings
from .embeddings import EmbeddingError, get_embedder
from .reranker import get_reranker
from .vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    title: str
    text: str
    score: float
    source_type: str
    source_id: str
    metadata: dict[str, Any]


async def retrieve(
    query: str,
    *,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
) -> list[RetrievedChunk]:
    if not settings.rag_active or not query.strip():
        return []

    top_k = top_k or settings.rag_top_k
    min_score = settings.rag_min_score if min_score is None else min_score

    try:
        embedder = get_embedder()
        query_vector = await embedder.embed_query(query)
        store = VectorStore()
        rows = await asyncio.to_thread(store.search, query_vector, top_k)
    except EmbeddingError as exc:
        logger.warning("RAG retrieval skipped: %s", exc)
        return []
    except Exception:
        logger.exception("RAG retrieval failed; continuing without context")
        return []

    rows = [r for r in rows if r["score"] >= min_score]
    rows = await get_reranker().rerank(query, rows)

    return [
        RetrievedChunk(
            title=r["title"],
            text=r["text"],
            score=r["score"],
            source_type=r["source_type"],
            source_id=r["source_id"],
            metadata=r["metadata"],
        )
        for r in rows
    ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as labelled context for the system prompt."""
    return "\n\n".join(f"[{c.title}]\n{c.text}" for c in chunks)
