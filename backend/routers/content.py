"""Portfolio content endpoints (Flow 1: database -> UI).

Serves the resume and articles straight from the content tables so the Next.js
pages render from the database instead of importing ``src/data``. Response
shapes intentionally match the old TypeScript/JSON shapes (camelCase keys,
``content`` as a ``{type, ...}`` block list) so the existing UI renderers need
only swap their data source, not their markup.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from ..content_models import Article
from ..content_service import get_resume_data
from ..database import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content")


def serialize_article_summary(a: Article) -> dict:
    return {
        "slug": a.slug,
        "title": a.title,
        "date": a.date,
        "description": a.description,
        "imageSrc": a.image_src,
        "tags": a.tags or [],
    }


def serialize_article(a: Article) -> dict:
    summary = serialize_article_summary(a)
    summary["githubUrl"] = a.github_url
    summary["paperUrl"] = a.paper_url
    summary["content"] = [{"type": b.type, **(b.data or {})} for b in a.blocks]
    return summary


@router.get("/resume/")
@router.get("/resume", include_in_schema=False)
async def get_resume():
    """GET /api/content/resume — the full resume in resume.json's shape."""
    try:
        async with AsyncSessionLocal() as db:
            resume = await get_resume_data(db)
    except SQLAlchemyError as exc:
        logger.warning("Resume content unavailable: %s", exc)
        return JSONResponse({"error": "content unavailable"}, status_code=503)

    if resume is None:
        return JSONResponse({"error": "resume not seeded"}, status_code=404)

    return resume


@router.get("/projects/")
@router.get("/projects", include_in_schema=False)
async def list_projects():
    """GET /api/content/projects — article summaries for the home grid."""
    try:
        async with AsyncSessionLocal() as db:
            articles = (
                await db.scalars(select(Article).order_by(Article.date.desc()))
            ).all()
    except SQLAlchemyError as exc:
        logger.warning("Projects list unavailable: %s", exc)
        return JSONResponse({"error": "content unavailable"}, status_code=503)
    return {"projects": [serialize_article_summary(a) for a in articles]}


@router.get("/projects/{slug}/")
@router.get("/projects/{slug}", include_in_schema=False)
async def get_project(slug: str):
    """GET /api/content/projects/{slug} — one full article incl. content blocks."""
    try:
        async with AsyncSessionLocal() as db:
            article = await db.scalar(
                select(Article)
                .where(Article.slug == slug)
                .options(selectinload(Article.blocks))
            )
    except SQLAlchemyError as exc:
        logger.warning("Project '%s' unavailable: %s", slug, exc)
        return JSONResponse({"error": "content unavailable"}, status_code=503)

    if article is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return serialize_article(article)
