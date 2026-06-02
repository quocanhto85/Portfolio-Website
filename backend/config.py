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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.alfred_cors_origins.split(",") if o.strip()]


settings = Settings()
