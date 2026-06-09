"""Seed portfolio content into the database from the migration fixtures.

This is a one-time / occasional migration tool, NOT part of the request path.
It reads the JSON fixtures under ``backend/seed_data`` (snapshots of the old
``src/data/resume.json`` and ``src/data/projects.ts``) and loads them into the
content tables. After this runs, the application reads content only from the
database; the ``src/data`` files are no longer imported anywhere.

Run against whatever ``DATABASE_URL`` points at (SQLite in dev, Neon Postgres
in prod):

    python -m backend.seed_content

It is idempotent: content tables are truncated and re-inserted on every run,
so re-running simply re-syncs the DB to the fixtures. Chat tables are untouched.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import delete

from .content_models import (
    Article,
    ArticleBlock,
    ResumeCertification,
    ResumeEducation,
    ResumeExperience,
    ResumeProfile,
    ResumeProject,
    ResumeSkill,
)
from .database import AsyncSessionLocal, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_content")

SEED_DIR = Path(__file__).resolve().parent / "seed_data"


def load_fixture(name: str) -> Any:
    with (SEED_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


async def wipe_content_tables(db) -> None:
    """Clear content tables (children first) so re-seeding is idempotent."""
    await db.execute(delete(ArticleBlock))
    await db.execute(delete(Article))
    for model in (
        ResumeProfile,
        ResumeExperience,
        ResumeEducation,
        ResumeSkill,
        ResumeCertification,
        ResumeProject,
    ):
        await db.execute(delete(model))


def seed_resume(db, resume: dict[str, Any]) -> dict[str, int]:
    personal = resume.get("personal", {})
    db.add(
        ResumeProfile(
            name=personal.get("name", ""),
            summary=personal.get("summary", ""),
            contact=personal.get("contact", []),
        )
    )

    for i, job in enumerate(resume.get("experience", [])):
        db.add(
            ResumeExperience(
                sort_order=i,
                company=job["company"],
                company_url=job.get("companyUrl"),
                location=job["location"],
                role=job["role"],
                dates=job["dates"],
                bullets=job.get("bullets", []),
                reference=job.get("reference"),
            )
        )

    for i, edu in enumerate(resume.get("education", [])):
        db.add(
            ResumeEducation(
                sort_order=i,
                school=edu["school"],
                location=edu["location"],
                degree=edu["degree"],
                details=edu["details"],
                dates=edu["dates"],
                reference=edu.get("reference"),
            )
        )

    for i, skill in enumerate(resume.get("skills", [])):
        db.add(ResumeSkill(sort_order=i, label=skill["label"], value=skill["value"]))

    for i, cert in enumerate(resume.get("certifications", [])):
        db.add(
            ResumeCertification(
                sort_order=i,
                title=cert["title"],
                issued=cert["issued"],
                href=cert.get("href"),
            )
        )

    for i, proj in enumerate(resume.get("projects", [])):
        db.add(
            ResumeProject(
                sort_order=i,
                name=proj["name"],
                url=proj.get("url"),
                bullets=proj.get("bullets", []),
            )
        )

    return {
        "experience": len(resume.get("experience", [])),
        "education": len(resume.get("education", [])),
        "skills": len(resume.get("skills", [])),
        "certifications": len(resume.get("certifications", [])),
        "resume_projects": len(resume.get("projects", [])),
    }


def seed_articles(db, articles: list[dict[str, Any]]) -> dict[str, int]:
    block_total = 0
    for art in articles:
        article = Article(
            slug=art["slug"],
            title=art["title"],
            date=art["date"],
            description=art["description"],
            image_src=art["imageSrc"],
            tags=art.get("tags", []),
            github_url=art.get("githubUrl"),
            paper_url=art.get("paperUrl"),
        )
        for order, block in enumerate(art.get("content", [])):
            data = {k: v for k, v in block.items() if k != "type"}
            article.blocks.append(
                ArticleBlock(sort_order=order, type=block["type"], data=data)
            )
            block_total += 1
        db.add(article)
    return {"articles": len(articles), "article_blocks": block_total}


async def seed() -> None:
    await init_db()
    resume = load_fixture("resume.json")
    articles = load_fixture("articles.json")

    async with AsyncSessionLocal() as db:
        await wipe_content_tables(db)
        counts = seed_resume(db, resume)
        counts.update(seed_articles(db, articles))
        await db.commit()

    logger.info("Seed complete: %s", counts)


if __name__ == "__main__":
    asyncio.run(seed())
