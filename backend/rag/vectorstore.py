"""Thin Milvus wrapper for Alfred's single chunk collection.

Self-hosted Milvus exposes a gRPC/REST endpoint, so the same client serves
every environment: in dev a local standalone server (Docker, browsable with the
Attu console), in prod a network-reachable Milvus you host or Zilliz Cloud. The
endpoint and optional token come from ``MILVUS_URI`` / ``MILVUS_TOKEN`` — a blank
token suits a local Docker server, which has auth disabled.

The content corpus is tiny, so the collection is rebuilt wholesale on each
ingest and searched with a cosine metric over an ``AUTOINDEX`` (exact for small
N). Scalar fields are stored as typed columns and metadata as a native JSON
field, so the whole chunk is legible in the Attu console — the reason we host
the vectors here rather than in opaque object storage.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)

OUTPUT_FIELDS = ["id", "source_type", "source_id", "title", "text", "metadata"]


def connect() -> "MilvusClient":
    # Imported lazily (not at module top) so importing this module — which the
    # Alfred router pulls in at startup via rag.retrieval — doesn't drag
    # pymilvus's heavy gRPC/protobuf stack into every serverless cold start.
    # Content and resume requests never touch Milvus, so they shouldn't pay the
    # ~1-3s it takes to import it. RAG/chat pays it lazily on first use instead.
    from pymilvus import MilvusClient

    return MilvusClient(
        uri=settings.milvus_uri,
        token=settings.milvus_token or None,
        db_name=settings.milvus_db_name or "default",
    )


class VectorStore:
    def __init__(
        self, table_name: Optional[str] = None, dim: Optional[int] = None
    ) -> None:
        self.collection = table_name or settings.milvus_collection
        self.dim = dim or settings.embedding_dim
        self.client = connect()

    def schema(self):
        from pymilvus import DataType

        # Typed scalar columns (not one JSON blob) so each field is its own
        # readable column in Attu; metadata stays a native JSON field.
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=512)
        schema.add_field("source_type", DataType.VARCHAR, max_length=64)
        schema.add_field("source_id", DataType.VARCHAR, max_length=256)
        schema.add_field("title", DataType.VARCHAR, max_length=1024)
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        schema.add_field("metadata", DataType.JSON)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.dim)
        return schema

    def rebuild(self, rows: list[dict[str, Any]]) -> int:
        """Overwrite the collection with ``rows`` (full rebuild; content is small)."""
        if self.client.has_collection(self.collection):
            self.client.drop_collection(self.collection)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector", index_type="AUTOINDEX", metric_type="COSINE"
        )
        # create_collection with index_params also builds the index and loads it.
        self.client.create_collection(
            self.collection, schema=self.schema(), index_params=index_params
        )
        if rows:
            self.client.insert(self.collection, rows)
            # Best-effort: a local Milvus benefits from an explicit flush, but
            # some managed/serverless backends (e.g. Zilliz Cloud) auto-flush and
            # may reject the call — never let that fail the rebuild.
            try:
                self.client.flush(self.collection)
            except Exception:  # pragma: no cover - backend-specific
                logger.debug("flush skipped (backend auto-flushes)", exc_info=True)
        return len(rows)

    def search(self, query_vector: list[float], top_k: int) -> list[dict[str, Any]]:
        if not self.client.has_collection(self.collection):
            logger.warning(
                "Milvus collection '%s' missing; run `python -m backend.rag.ingest`",
                self.collection,
            )
            return []

        # Idempotent: a fast no-op once the server already has it loaded.
        self.client.load_collection(self.collection)
        hits = self.client.search(
            collection_name=self.collection,
            data=[query_vector],
            anns_field="vector",
            limit=top_k,
            search_params={"metric_type": "COSINE"},
            output_fields=OUTPUT_FIELDS,
        )[0]

        results: list[dict[str, Any]] = []
        for h in hits:
            entity = h.get("entity", {})
            results.append(
                {
                    "id": entity.get("id"),
                    "source_type": entity.get("source_type"),
                    "source_id": entity.get("source_id"),
                    "title": entity.get("title"),
                    "text": entity.get("text"),
                    "metadata": entity.get("metadata") or {},
                    # COSINE metric: Milvus returns the similarity directly
                    # (higher = better), so there's no 1 - distance conversion.
                    "score": float(h.get("distance", 0.0)),
                }
            )
        return results
