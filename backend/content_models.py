"""Portfolio content models — the source of truth for resume + articles.

These tables replace the old static ``src/data/resume.json`` and
``src/data/projects.ts``. Both flows read from here:

* Flow 1 (display): ``routers/content.py`` serves these rows to the Next.js UI.
* Flow 2 (RAG): ``backend/rag/ingest.py`` reads these rows, chunks + embeds
  them, and writes vectors to Milvus.

The running application never imports the ``src/data`` files again; those
survive only as one-time seed input under ``backend/seed_data`` (see
``backend/seed_content.py``).

Schema notes:
- The resume's list sections (experience/education/skills/...) are stored as
  rows rather than one JSON blob, because each row maps cleanly to one
  retrievable chunk during ingestion.
- Small leaf data that always travels with its parent chunk (a role's bullet
  list, a contact list, a reference card) stays as a ``JSON`` column instead of
  a child table — it never needs to be queried independently.
- ``Article.content`` is modelled as ordered ``ArticleBlock`` rows that mirror
  the ``ContentBlock`` union from the old TypeScript: ``type`` + a ``data`` blob
  carrying that type's fields. This keeps the UI renderer and the chunker on a
  single ``{type, ...data}`` contract.
- The generic ``JSON`` type is portable across SQLite (dev) and Postgres (prod).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# --- Resume ------------------------------------------------------------------

class ResumeProfile(Base):
    """Singleton header block (one row): name, summary, contact links."""

    __tablename__ = "resume_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text)
    # list[{"label": str, "href": str}]
    contact: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ResumeExperience(Base):
    __tablename__ = "resume_experience"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    company: Mapped[str] = mapped_column(String(256))
    company_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    location: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(256))
    dates: Mapped[str] = mapped_column(String(128))
    bullets: Mapped[list[str]] = mapped_column(JSON, default=list)
    # {"name", "profileUrl", "role", "email"} | None
    reference: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ResumeEducation(Base):
    __tablename__ = "resume_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    school: Mapped[str] = mapped_column(String(256))
    location: Mapped[str] = mapped_column(String(256))
    degree: Mapped[str] = mapped_column(String(256))
    details: Mapped[str] = mapped_column(String(512))
    dates: Mapped[str] = mapped_column(String(128))
    reference: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ResumeSkill(Base):
    __tablename__ = "resume_skill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    label: Mapped[str] = mapped_column(String(128))
    value: Mapped[str] = mapped_column(Text)


class ResumeCertification(Base):
    __tablename__ = "resume_certification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    title: Mapped[str] = mapped_column(Text)
    issued: Mapped[str] = mapped_column(String(128))
    href: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)


class ResumeProject(Base):
    """The resume's compact project list (distinct from full Articles)."""

    __tablename__ = "resume_project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    name: Mapped[str] = mapped_column(String(512))
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bullets: Mapped[list[str]] = mapped_column(JSON, default=list)


# --- Articles ----------------------------------------------------------------

class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    # Kept as the original display string (e.g. "2025-12-07"), not a date type.
    date: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    image_src: Mapped[str] = mapped_column(String(512))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    github_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    paper_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    blocks: Mapped[list["ArticleBlock"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleBlock.sort_order",
    )


class ArticleBlock(Base):
    """One ordered content block: ``type`` + a type-specific ``data`` blob.

    Mirrors the old ``ContentBlock`` union (paragraph/heading/list/video/
    image/report). ``data`` holds whatever that type carries — e.g. a video
    block's ``{"src", "caption", "poster"}`` — so a row reassembles to
    ``{"type": type, **data}`` for both the UI and the chunker.
    """

    __tablename__ = "article_block"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(32))
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    article: Mapped["Article"] = relationship(back_populates="blocks")

    __table_args__ = (
        Index("ix_article_block_article_order", "article_id", "sort_order"),
    )
