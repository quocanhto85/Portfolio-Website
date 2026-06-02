"""SQLAlchemy 2.0 models — the FastAPI equivalent of the old Django ORM models.

``ChatSession``/``ChatMessage`` keep the same shape so the ``/stats`` aggregate
and message persistence behave identically. The primary key is a string UUID
for portability across SQLite (no native UUID type) and Postgres alike.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    total_messages: Mapped[int] = mapped_column(Integer, default=0)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return f"ChatSession({self.id})"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    tokens_generated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:40]}"
