"""Shared content reads from the database (single source of truth).

Both the public content API (Flow 1, ``routers/content.py``) and Alfred's
knowledge builder (``knowledge.py``) read the resume through here, so the DB is
queried one way and the response shape can't drift between the two callers.
"""

from __future__ import annotations

from sqlalchemy import select

from .content_models import (
    ResumeCertification,
    ResumeEducation,
    ResumeExperience,
    ResumeProfile,
    ResumeProject,
    ResumeSkill,
)


async def get_resume_data(db) -> dict | None:
    """Assemble the resume in resume.json's shape, or ``None`` if not seeded.

    Takes an open ``AsyncSession`` so the caller owns the session lifecycle and
    its own error handling.
    """
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
    projects = (
        await db.scalars(
            select(ResumeProject).order_by(ResumeProject.sort_order)
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
        "projects": [
            {"name": p.name, "bullets": p.bullets or []} for p in projects
        ],
    }
