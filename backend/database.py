"""SQLAlchemy 2.0 async engine, session factory, and schema bootstrap.

Mirrors the Django ORM's graceful degradation: on Vercel the filesystem is
read-only outside ``/tmp``, so SQLite writes (including ``create_all``) fail.
``init_db`` swallows that error and logs once; the request path then falls
back to ephemeral sessions (see ``routers/alfred.py``). Langfuse remains the
durable conversation log in that mode.
"""

from __future__ import annotations

import logging

from sqlalchemy import make_url
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)


def normalize_db_url(raw: str) -> tuple[URL, dict]:
    """Make a pasted Neon connection string work with our async stack.

    Neon hands out libpq-style URLs (``postgresql://…?sslmode=require``) that the
    sync psycopg2 driver expects. We run on asyncpg, which needs a different
    driver name and rejects ``sslmode``/``channel_binding`` as keyword args. This
    rewrites the URL so the value copied verbatim from the Neon dashboard — into
    ``.env`` or Vercel — just works, instead of silently selecting psycopg2.

    Returns the normalized URL plus ``connect_args`` for ``create_async_engine``.
    """
    url = make_url(raw)
    connect_args: dict = {}

    # Bare "postgresql://" / "postgres://" selects sync psycopg2; force asyncpg.
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+asyncpg")

    if url.drivername == "postgresql+asyncpg":
        query = dict(url.query)
        # asyncpg.connect() takes `ssl=`, not libpq's `sslmode=`; translate it
        # and drop channel_binding (asyncpg negotiates that on its own).
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        url = url.set(query=query)
        if sslmode:
            connect_args["ssl"] = sslmode
        # Neon's pooled (PgBouncer) endpoint can't retain server-side prepared
        # statements; disabling the cache avoids "prepared statement does not
        # exist" and costs nothing on this low-traffic, serverless workload.
        connect_args["statement_cache_size"] = 0

    return url, connect_args


db_url, connect_args = normalize_db_url(settings.database_url)
engine = create_async_engine(db_url, future=True, connect_args=connect_args)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create tables if the DB is writable; degrade quietly otherwise."""
    # Import here so models are registered on Base.metadata before create_all.
    from . import content_models, models  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as exc:
        logger.warning(
            "DB schema bootstrap skipped (read-only/unavailable): %s", exc
        )
