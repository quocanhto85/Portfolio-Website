import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-only-secret-key-change-in-production"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "adrf",
    "llm_serving",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "django_portfolio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

WSGI_APPLICATION = "django_portfolio.wsgi.application"
ASGI_APPLICATION = "django_portfolio.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache (sliding-window rate limiter backing store) -----------------------
# Use Redis when REDIS_URL is set, otherwise fall back to a process-local cache
# that still satisfies the cache.get / cache.set contract for local dev.
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "TIMEOUT": 300,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "alfred-locmem",
            "TIMEOUT": 300,
        }
    }

# --- Alfred (LLM serving) config --------------------------------------------
# ALFRED_OLLAMA_URL is the OpenAI-compatible base URL. Set to your local
# Ollama (default), or to a cloud provider such as Groq for production:
#   ALFRED_OLLAMA_URL=https://api.groq.com/openai
#   ALFRED_API_KEY=gsk_...
#   ALFRED_MODEL=llama-3.1-8b-instant
ALFRED_MODEL = os.environ.get("ALFRED_MODEL", "llama3.2:3b")
ALFRED_OLLAMA_URL = os.environ.get("ALFRED_OLLAMA_URL", "http://localhost:11434")
ALFRED_API_KEY = os.environ.get("ALFRED_API_KEY", "")
ALFRED_RATE_LIMIT_MAX = int(os.environ.get("ALFRED_RATE_LIMIT_MAX", "10"))
ALFRED_RATE_LIMIT_WINDOW = int(os.environ.get("ALFRED_RATE_LIMIT_WINDOW", "60"))
ALFRED_REQUEST_TIMEOUT = float(os.environ.get("ALFRED_REQUEST_TIMEOUT", "60"))

# Langfuse (LLM-specific observability). Leave empty to disable.
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Comma-separated list of allowed origins for the Alfred SSE endpoint.
ALFRED_CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALFRED_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
