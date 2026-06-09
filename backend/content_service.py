"""Shared content reads from the database (single source of truth).

Both the public content API (Flow 1, ``routers/content.py``) and Alfred's
knowledge builder (``knowledge.py``) read the resume through here, so the DB is
queried one way and the response shape can't drift between the two callers.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .content_models import (
    ResumeCertification,
    ResumeEducation,
    ResumeExperience,
    ResumeProfile,
    ResumeProject,
    ResumeSkill,
)

logger = logging.getLogger(__name__)


async def _load_projects(db) -> list[dict]:
    """Load resume projects, tolerating a DB that predates the ``url`` column.

    ``url`` was added to ``resume_project`` after the table first shipped. On a
    database where that migration (``ALTER TABLE resume_project ADD COLUMN
    url ...``) hasn't run yet, selecting the mapped entity raises
    ``UndefinedColumn`` and would 500 the whole resume page. We fall back to the
    name+bullets columns so the resume still renders (project links just stay
    off) until the column exists. This runs before the other reads so its
    rollback can't expire rows an async session is unable to lazily reload.
    """
    try:
        rows = (
            await db.scalars(
                select(ResumeProject).order_by(ResumeProject.sort_order)
            )
        ).all()
        return [
            {"name": p.name, "url": p.url, "bullets": p.bullets or []}
            for p in rows
        ]
    except SQLAlchemyError as exc:
        logger.warning(
            "resume_project.url unavailable (%s); serving projects without "
            "links. Run: ALTER TABLE resume_project ADD COLUMN url VARCHAR(512);",
            exc,
        )
        await db.rollback()
        rows = (
            await db.execute(
                select(ResumeProject.name, ResumeProject.bullets).order_by(
                    ResumeProject.sort_order
                )
            )
        ).all()
        return [
            {"name": name, "url": None, "bullets": bullets or []}
            for name, bullets in rows
        ]


async def get_resume_data(db) -> dict | None:
    """Assemble the resume in resume.json's shape, or ``None`` if not seeded.

    Takes an open ``AsyncSession`` so the caller owns the session lifecycle and
    its own error handling.
    """
    # Resilient projects load goes first: its fallback may roll back the
    # session, which must not happen after other rows are materialized (an
    # async session can't lazily reload expired attributes).
    projects = await _load_projects(db)

    profile = await db.scalar(select(ResumeProfile).limit(1))
    if profile is None:
        return None

    skills = (
        await db.scalars(select(ResumeSkill).order_by(ResumeSkill.sort_order))
    ).all()
    education = (
        await db.scalars(
            select(ResumeEducation).order_by(ResumeEducation.sort_order)
        )
    ).all()
    certifications = (
        await db.scalars(
            select(ResumeCertification).order_by(ResumeCertification.sort_order)
        )
    ).all()
    experience = (
        await db.scalars(
            select(ResumeExperience).order_by(ResumeExperience.sort_order)
        )
    ).all()

    return {
        "personal": {
            "name": profile.name,
            "summary": profile.summary,
            "contact": profile.contact or [],
        },
        "skills": [{"label": s.label, "value": s.value} for s in skills],
        "education": [
            {
                "school": e.school,
                "location": e.location,
                "degree": e.degree,
                "details": e.details,
                "dates": e.dates,
                **({"reference": e.reference} if e.reference else {}),
            }
            for e in education
        ],
        "certifications": [
            {"title": c.title, "issued": c.issued, "href": c.href}
            for c in certifications
        ],
        "experience": [
            {
                "company": x.company,
                "companyUrl": x.company_url,
                "location": x.location,
                "role": x.role,
                "dates": x.dates,
                "bullets": x.bullets or [],
                **({"reference": x.reference} if x.reference else {}),
            }
            for x in experience
        ],
        "projects": projects,
    }
