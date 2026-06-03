"""Thin LanceDB wrapper for Alfred's single chunk table.

Self-hosted LanceDB has no API key: in dev it reads/writes a local directory,
in prod an S3-compatible bucket (Cloudflare R2). Remote credentials are passed
as ``storage_options`` and consulted only when ``LANCEDB_URI`` is an ``s3://``
URI, so local dev needs no configuration.

The content corpus is tiny, so the table is rebuilt wholesale on each ingest
and searched exhaustively (no ANN index — exact and simplest for small N).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import lancedb
import pyarrow as pa

from ..config import settings

logger = logging.getLogger(__name__)


def _storage_options() -> Optional[dict[str, str]]:
    if not settings.lancedb_uri.startswith("s3://"):
        return None
    opts: dict[str, str] = {
        "aws_region": settings.lancedb_s3_region,
        # R2 (and most S3-compat stores) use path-style addressing.
        "aws_virtual_hosted_style_request": "false",
    }
    if settings.lancedb_s3_endpoint:
        opts["aws_endpoint"] = settings.lancedb_s3_endpoint
    if settings.lancedb_aws_access_key_id:
        opts["aws_access_key_id"] = settings.lancedb_aws_access_key_id
    if settings.lancedb_aws_secret_access_key:
        opts["aws_secret_access_key"] = settings.lancedb_aws_secret_access_key
    return opts


def _schema(dim: int) -> pa.Schema:
    return pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("source_type", pa.string()),
            pa.field("source_id", pa.string()),
            pa.field("title", pa.string()),
            pa.field("text", pa.string()),
            pa.field("metadata", pa.string()),  # JSON-encoded blob
            pa.field("vector", pa.list_(pa.float32(), dim)),
        ]
    )


def connect():
    return lancedb.connect(
        settings.lancedb_uri, storage_options=_storage_options()
    )


class VectorStore:
    def __init__(
        self, table_name: Optional[str] = None, dim: Optional[int] = None
    ) -> None:
        self.table_name = table_name or settings.lancedb_table
        self.dim = dim or settings.embedding_dim
        self.db = connect()

    def rebuild(self, rows: list[dict[str, Any]]) -> int:
        """Overwrite the table with ``rows`` (full rebuild; content is small)."""
        table = self.db.create_table(
            self.table_name, schema=_schema(self.dim), mode="overwrite"
        )
        if rows:
            table.add(rows)
        return len(rows)

    def search(self, query_vector: list[float], top_k: int) -> list[dict[str, Any]]:
        try:
            table = self.db.open_table(self.table_name)
        except Exception:
            logger.warning(
                "LanceDB table '%s' missing; run `python -m backend.rag.ingest`",
                self.table_name,
            )
            return []

        hits = (
            table.search(query_vector).distance_type("cosine").limit(top_k).to_list()
        )
        results: list[dict[str, Any]] = []
        for h in hits:
            results.append(
                {
                    "id": h.get("id"),
                    "source_type": h.get("source_type"),
                    "source_id": h.get("source_id"),
                    "title": h.get("title"),
                    "text": h.get("text"),
                    "metadata": json.loads(h.get("metadata") or "{}"),
                    # LanceDB cosine "distance" is 1 - similarity.
                    "score": 1.0 - float(h.get("_distance", 1.0)),
                }
            )
        return results
