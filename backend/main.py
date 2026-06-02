"""FastAPI application entry point.

Replaces Django's ``urls.py`` + ``asgi.py``/``wsgi.py``. The ASGI ``app`` is
what both local dev (uvicorn) and Vercel run. CORS is handled globally by
``CORSMiddleware`` (the Django version set the same headers by hand on each
endpoint); the schema is bootstrapped once on startup via the lifespan hook.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import alfred, portfolio

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Batcave Portfolio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=86400,
)

app.include_router(portfolio.router)
app.include_router(alfred.router)
