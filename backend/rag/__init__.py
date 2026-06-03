"""Alfred's retrieval-augmented generation (RAG) pipeline.

Flow 2 of the content architecture (Flow 1 is database -> UI in
``routers/content.py``). The database is the single source of truth; this
package derives vectors from it:

    Postgres content  ->  chunking  ->  embeddings  ->  LanceDB  (ingest.py)
    user question     ->  embeddings ->  LanceDB top-k -> Alfred  (retrieval.py)

Pieces:
- ``chunking``   turn resume rows + article blocks into retrievable text chunks
                 (media is described by its caption + neighbours, never the raw
                 binary/URL — those live in metadata only).
- ``embeddings`` pluggable, OpenAI-shaped embedder (Jina by default).
- ``vectorstore``thin LanceDB wrapper (local dir in dev, R2/S3 in prod).
- ``ingest``     CLI that rebuilds the vector table from the database.
- ``retrieval``  embed a query, fetch top-k, apply a relevance floor.
- ``reranker``   Phase-5 seam; a no-op today.

LanceDB is self-hosted and has no API key. The only credential the pipeline
needs is the embedding provider's key (``EMBEDDING_API_KEY``).
"""
