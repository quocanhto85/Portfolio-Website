"""Static knowledge that Alfred is given as system context.

Resume data is read from the content database (via ``content_service``) — the
same single source of truth the Next.js resume page renders from — so updates
in one place flow to both the UI and Alfred's system prompt. Durations between
role dates are pre-computed here because small open-weights models tend to slip
on date arithmetic.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from .content_service import get_resume_data
from .database import AsyncSessionLocal

logger = logging.getLogger(__name__)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_endpoint(token: str) -> Optional[date]:
    token = token.strip().lower()
    if not token or token == "present":
        return date.today()
    m = re.match(r"([a-z]{3})\s+(\d{4})$", token)
    if m and m.group(1) in MONTHS:
        return date(int(m.group(2)), MONTHS[m.group(1)], 1)
    m = re.match(r"(\d{4})$", token)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def format_duration(dates: str) -> Optional[str]:
    """Return e.g. '2 years 10 months' for 'Mar 2021 - Dec 2023'."""
    parts = re.split(r"\s*[-–]\s*", dates, maxsplit=1)
    if len(parts) != 2:
        return None
    start, end = parse_endpoint(parts[0]), parse_endpoint(parts[1])
    if not start or not end:
        return None
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    if months <= 0:
        return None
    years, rem = divmod(months, 12)
    bits = []
    if years:
        bits.append(f"{years} year{'s' if years != 1 else ''}")
    if rem:
        bits.append(f"{rem} month{'s' if rem != 1 else ''}")
    return " ".join(bits) or "less than 1 month"


def build_resume_section(resume: dict) -> str:
    out: list[str] = []
    personal = resume.get("personal", {})
    out.append(f"Full name: {personal.get('name', '')}")
    out.append(f"Professional summary: {personal.get('summary', '')}")

    contact_bits = [c["label"] for c in personal.get("contact", [])]
    if contact_bits:
        out.append("Contact: " + " | ".join(contact_bits))

    out.append("\nProfessional experience (most recent first):")
    for job in resume.get("experience", []):
        duration = format_duration(job["dates"]) or "duration unknown"
        out.append(
            f"- {job['company']} ({job['location']}) — {job['role']}, "
            f"{job['dates']} ({duration})."
        )
        for bullet in job.get("bullets", []):
            out.append(f"    * {bullet}")

    out.append("\nEducation:")
    for edu in resume.get("education", []):
        out.append(
            f"- {edu['school']} ({edu['location']}) — {edu['degree']}, "
            f"{edu['details']}, {edu['dates']}."
        )

    out.append("\nSkills:")
    for skill in resume.get("skills", []):
        out.append(f"- {skill['label']}: {skill['value']}")

    out.append("\nPersonal projects:")
    for proj in resume.get("projects", []):
        out.append(f"- {proj['name']}")
        for bullet in proj.get("bullets", []):
            out.append(f"    * {bullet}")

    out.append("\nCourses & certifications:")
    for cert in resume.get("certifications", []):
        out.append(f"- {cert['title']} ({cert['issued']}).")

    return "\n".join(out)


PORTFOLIO_CONTEXT = """
About the Batcave portfolio
- Site name: Quoc Anh's Batcave (Batman-themed personal portfolio).
- Stack: Next.js 16 App Router (React 19) on the frontend, FastAPI (async
  Python) on the backend, deployed on Vercel.
- Live features: contact console (email, LinkedIn, GitHub, resume), project
  cards with tags, a search field, and Alfred — the AI butler chat.
- A full resume page is available at /resume; Alfred is given that resume
  data as reference material below.

Alfred himself
- Powered by Ollama running a small open-weights model (default llama3.2:3b).
- Streams tokens via Server-Sent Events from a FastAPI async endpoint.
- Rate-limited with a sliding-window limiter (10 requests / 60 seconds per
  IP hash) backed by an in-process store (or Redis when configured).
- Conversation logs live in SQLite via SQLAlchemy; lightweight usage stats
  surface on /api/alfred/stats/.
"""


SYSTEM_PROMPT_PREAMBLE = (
    "You are Alfred, the loyal and eloquent AI butler of Quoc Anh's Batcave "
    "portfolio. You speak in formal British English with dry wit. Answer "
    "visitor questions about Quoc Anh (his background, experience, skills, "
    "education, projects) using ONLY the reference material below. If a "
    "question cannot be answered from this material, say so plainly rather "
    "than inventing details. When asked about role tenure or dates, prefer "
    "the pre-computed durations listed beside each role. Keep answers "
    "concise (under 150 words) and stay in character."
)


async def build_system_prompt(retrieved_context: str = "") -> str:
    """Assemble Alfred's system prompt, reading the resume from the content DB.

    The resume is the same single source of truth the ``/resume`` page renders
    from and is always included (it's small and central). ``retrieved_context``
    is the optional RAG augmentation for a specific question — the most relevant
    chunks (article sections, etc.) appended as extra reference material.

    If the resume isn't seeded yet (or the DB is unreachable), Alfred still gets
    the portfolio context and stays in character — simply without resume
    specifics — rather than failing the request.
    """
    resume_context = ""
    try:
        async with AsyncSessionLocal() as db:
            resume = await get_resume_data(db)
        if resume is not None:
            resume_context = build_resume_section(resume)
    except SQLAlchemyError as exc:
        logger.warning("Resume unavailable for Alfred's system prompt: %s", exc)

    prompt = (
        f"{SYSTEM_PROMPT_PREAMBLE}\n\n"
        "=== PORTFOLIO ===\n"
        f"{PORTFOLIO_CONTEXT}\n"
    )
    if resume_context:
        prompt += "=== RESUME ===\n" f"{resume_context}\n"
    if retrieved_context:
        prompt += (
            "=== RETRIEVED CONTEXT (most relevant to the question) ===\n"
            f"{retrieved_context}\n"
        )
    return prompt
