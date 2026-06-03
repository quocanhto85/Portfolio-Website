"""Application configuration via pydantic-settings.

Replaces Django's ``settings.py``. Environment variable names are unchanged
from the Django version (``ALFRED_*``, ``LANGFUSE_*``, ``REDIS_URL``) and are
matched case-insensitively to the fields below. ``.env`` is loaded both into
the ``Settings`` object (pydantic) and into ``os.environ`` (via python-dotenv)
so libraries that read the environment directly still see the values.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Alfred (LLM serving) -------------------------------------------------
    # ALFRED_OLLAMA_URL is the OpenAI-compatible base URL. Point it at a local
    # Ollama (default) or a cloud provider such as Groq for production:
    #   ALFRED_OLLAMA_URL=https://api.groq.com/openai
    #   ALFRED_API_KEY=gsk_...
    #   ALFRED_MODEL=llama-3.1-8b-instant
    alfred_model: str = "llama3.2:3b"
    alfred_ollama_url: str = "http://localhost:11434"
    alfred_api_key: str = ""
    alfred_rate_limit_max: int = 10
    alfred_rate_limit_window: int = 60
    alfred_request_timeout: float = 60.0
    alfred_cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )

    # --- Persistence / cache --------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./db.sqlite3"
    redis_url: str = ""

    # --- Langfuse (LLM observability; leave keys empty to disable) ------------
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_release: str = ""
    langfuse_environment: str = "local"

    # --- RAG: embeddings (the only API key the pipeline needs) ----------------
    # Every provider is called through the OpenAI-shaped POST {base}/embeddings
    # contract, so switching providers is just these four values + the key.
    # Default is Jina (free tier, 1024-dim, multilingual). For OpenAI/Voyage,
    # set the matching base/model/dim and CLEAR the *_task fields below.
    embedding_provider: str = "jina"
    embedding_api_base: str = "https://api.jina.ai/v1"
    embedding_model: str = "jina-embeddings-v3"
    embedding_dim: int = 1024
    embedding_api_key: str = ""
    embedding_timeout: float = 30.0
    embedding_batch_size: int = 64
    # Jina v3 task hints sharpen retrieval (asymmetric query/passage). Only sent
    # when non-empty; leave blank for providers that reject an unknown "task".
    embedding_query_task: str = "retrieval.query"
    embedding_passage_task: str = "retrieval.passage"

    # --- RAG: vector store (self-hosted LanceDB — NO API key) -----------------
    # Dev: a local directory. Prod: an S3-compatible bucket, e.g. Cloudflare R2
    #   LANCEDB_URI=s3://my-bucket/alfred
    #   LANCEDB_S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com
    # plus the access key/secret below. Creds are passed to LanceDB as
    # storage_options; they are only consulted when the URI is s3://.
    lancedb_uri: str = "./.lancedb"
    lancedb_table: str = "alfred_chunks"
    lancedb_s3_endpoint: str = ""
    lancedb_s3_region: str = "auto"
    lancedb_aws_access_key_id: str = ""
    lancedb_aws_secret_access_key: str = ""

    # --- RAG: retrieval -------------------------------------------------------
    # RAG augments Alfred's always-on resume with the most relevant chunks for a
    # given question. It self-disables when no embedding key is set, so chat
    # keeps working with just the resume.
    rag_enabled: bool = True
    rag_top_k: int = 5
    # Cosine-similarity floor in [-1, 1]; drop weaker matches so an off-topic
    # question doesn't drag in noise. 0 keeps everything the search returns.
    rag_min_score: float = 0.30
    rag_rerank_enabled: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.alfred_cors_origins.split(",") if o.strip()]

    @property
    def rag_active(self) -> bool:
        """RAG only runs when explicitly enabled *and* an embedding key exists."""
        return self.rag_enabled and bool(self.embedding_api_key)


settings = Settings()
