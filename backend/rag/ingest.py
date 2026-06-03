"""Rebuild Alfred's LanceDB vector table from the content database.

    python -m backend.rag.ingest

Reads the same DB that serves the UI (resume rows + article blocks), chunks
it, embeds the chunks with the configured provider, and overwrites the vector
table. Idempotent — a full rebuild each run, mirroring ``seed_content.py``.

Requires ``EMBEDDING_API_KEY``. LanceDB itself needs no key: a local directory
in dev, or R2/S3 in prod via ``LANCEDB_URI``.
"""

from __future__ import annotations

import asyncio
import json
import logging

from ..database import AsyncSessionLocal
from .chunking import build_chunks
from .embeddings import get_embedder
from .vectorstore import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag.ingest")


async def ingest() -> dict:
    embedder = get_embedder()  # fails fast with guidance if the key is missing

    async with AsyncSessionLocal() as db:
        chunks = await build_chunks(db)

    if not chunks:
        logger.warning("No content to ingest — is the DB seeded?")
        VectorStore().rebuild([])
        return {"chunks": 0}

    logger.info(
        "Embedding %d chunks via %s (%s) ...",
        len(chunks),
        embedder.api_base,
        embedder.model,
    )
    vectors = await embedder.embed_documents([c.text for c in chunks])

    rows = [
        {
            "id": c.chunk_id,
            "source_type": c.source_type,
            "source_id": c.source_id,
            "title": c.title,
            "text": c.text,
            "metadata": json.dumps(c.metadata, ensure_ascii=False),
            "vector": vector,
        }
        for c, vector in zip(chunks, vectors)
    ]

    count = VectorStore(dim=embedder.dim).rebuild(rows)

    by_type: dict[str, int] = {}
    for c in chunks:
        by_type[c.source_type] = by_type.get(c.source_type, 0) + 1
    logger.info("Ingest complete: %d vectors %s", count, by_type)
    return {"chunks": count, **by_type}


if __name__ == "__main__":
    asyncio.run(ingest())
