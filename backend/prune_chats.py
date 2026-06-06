"""Prune old chat logs so the one unbounded table can't fill the database.

Content tables (resume + articles) and the Milvus vector store are bounded by
how much you publish. The chat log (``chat_sessions`` + ``chat_messages``) is the
only table that grows with traffic, so this CLI trims it to a retention window.

Pruning is **session-centric**: a chat happens in one sitting, so a session
older than the window is expired and removed in full — its messages first (we
delete them explicitly rather than leaning on ``ON DELETE CASCADE``, which
SQLite ignores unless ``PRAGMA foreign_keys=ON``), then the session row. Because
whole sessions go away, no ``total_messages`` counter is left stale.

Runs against whatever ``DATABASE_URL`` points at (SQLite in dev, Neon Postgres
in prod). Safe to run repeatedly, e.g. from a scheduled job::

    python -m backend.prune_chats                 # delete logs older than 90d
    python -m backend.prune_chats --older-than 30d
    python -m backend.prune_chats --older-than 12w --dry-run   # preview only
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from .database import AsyncSessionLocal
from .models import ChatMessage, ChatSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prune_chats")

DURATION_RE = re.compile(r"^\s*(\d+)\s*([wdh])\s*$", re.IGNORECASE)
UNIT_SECONDS = {"w": 7 * 86400, "d": 86400, "h": 3600}


def parse_duration(raw: str) -> timedelta:
    """Parse a retention window like ``90d``, ``12w`` or ``48h`` into a timedelta."""
    match = DURATION_RE.match(raw)
    if not match:
        raise argparse.ArgumentTypeError(
            f"invalid duration {raw!r}; use forms like 48h, 90d, 12w"
        )
    value = int(match.group(1))
    if value <= 0:
        raise argparse.ArgumentTypeError("duration must be a positive number")
    return timedelta(seconds=value * UNIT_SECONDS[match.group(2).lower()])


async def prune(older_than: timedelta, *, dry_run: bool = False) -> dict[str, int]:
    """Delete chat sessions (and their messages) created before the cutoff.

    Returns a ``{"sessions": n, "messages": m}`` count of what was (or, for
    ``dry_run``, would be) removed.
    """
    cutoff = datetime.now(timezone.utc) - older_than
    expired = select(ChatSession.id).where(ChatSession.created_at < cutoff)

    async with AsyncSessionLocal() as db:
        session_count = await db.scalar(
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.created_at < cutoff)
        )
        message_count = await db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.session_id.in_(expired))
        )
        counts = {"sessions": session_count or 0, "messages": message_count or 0}

        if dry_run:
            logger.info(
                "[dry-run] would delete %d sessions and %d messages older than %s",
                counts["sessions"],
                counts["messages"],
                cutoff.isoformat(),
            )
            return counts

        # Children first, then parents — independent of DB-level FK cascade.
        await db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(expired)))
        await db.execute(delete(ChatSession).where(ChatSession.created_at < cutoff))
        await db.commit()

    logger.info(
        "Pruned %d sessions and %d messages older than %s",
        counts["sessions"],
        counts["messages"],
        cutoff.isoformat(),
    )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m backend.prune_chats",
        description="Delete chat logs older than a retention window.",
    )
    parser.add_argument(
        "--older-than",
        type=parse_duration,
        default="90d",
        metavar="DURATION",
        help="retention window; sessions older than this are deleted "
        "(default: 90d). Forms: 48h, 90d, 12w.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be deleted without deleting anything.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(prune(args.older_than, dry_run=args.dry_run))
    except SQLAlchemyError as exc:
        logger.error("Prune failed (is DATABASE_URL reachable?): %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
