"""Alfred's retrieval-augmented generation (RAG) pipeline.

Flow 2 of the content architecture (Flow 1 is database -> UI in
``routers/content.py``). The database is the single source of truth; this
package derives vectors from it:

    Postgres content  ->  chunking  ->  embeddings  ->  Milvus   (ingest.py)
    user question     ->  embeddings ->  Milvus top-k -> Alfred  (retrieval.py)

Pieces:
- ``chunking``   turn resume rows + article blocks into retrievable text chunks
                 (media is described by its caption + neighbours, never the raw
                 binary/URL — those live in metadata only).
- ``embeddings`` pluggable, OpenAI-shaped embedder (Jina by default).
- ``vectorstore``thin Milvus wrapper (Docker standalone in dev; hosted in prod).
- ``ingest``     CLI that rebuilds the vector table from the database.
- ``retrieval``  embed a query, fetch top-k, apply a relevance floor.
- ``reranker``   Phase-5 seam; a no-op today.

Milvus is self-hosted (local Docker in dev; a hosted/Zilliz endpoint in prod)
and needs no provider key — just ``MILVUS_URI`` (and ``MILVUS_TOKEN`` when the
endpoint requires auth). The only credential the pipeline needs is the
embedding provider's key (``EMBEDDING_API_KEY``).
"""
