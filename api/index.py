"""Vercel Python entry point.

Exposes the FastAPI ASGI ``app``. Vercel's Python runtime detects the ASGI
callable and serves it directly, which gives Alfred native async streaming.

For local dev, run the same app with uvicorn:
    uvicorn backend.main:app --reload --port 8000
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app  # noqa: E402

__all__ = ["app"]
