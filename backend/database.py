"""SQLAlchemy 2.0 async engine, session factory, and schema bootstrap.

Mirrors the Django ORM's graceful degradation: on Vercel the filesystem is
read-only outside ``/tmp``, so SQLite writes (including ``create_all``) fail.
``init_db`` swallows that error and logs once; the request path then falls
back to ephemeral sessions (see ``routers/alfred.py``). Langfuse remains the
durable conversation log in that mode.
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create tables if the DB is writable; degrade quietly otherwise."""
    # Import here so models are registered on Base.metadata before create_all.
    from . import models  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as exc:
        logger.warning(
            "DB schema bootstrap skipped (read-only/unavailable): %s", exc
        )
