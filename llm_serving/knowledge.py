"""Static knowledge that Alfred is given as system context.

Resume data is read from ``src/data/resume.json`` — the same source of truth
the Next.js resume page renders from — so updates in one place flow to both
the UI and Alfred's system prompt. Durations between role dates are
pre-computed here because small open-weights models tend to slip on date
arithmetic.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Optional

_RESUME_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "data" / "resume.json"
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_endpoint(token: str) -> Optional[date]:
    token = token.strip().lower()
    if not token or token == "present":
        return date.today()
    m = re.match(r"([a-z]{3})\s+(\d{4})$", token)
    if m and m.group(1) in _MONTHS:
        return date(int(m.group(2)), _MONTHS[m.group(1)], 1)
    m = re.match(r"(\d{4})$", token)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def _format_duration(dates: str) -> Optional[str]:
    """Return e.g. '2 years 10 months' for 'Mar 2021 - Dec 2023'."""
    parts = re.split(r"\s*[-–]\s*", dates, maxsplit=1)
    if len(parts) != 2:
        return None
    start, end = _parse_endpoint(parts[0]), _parse_endpoint(parts[1])
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


def _load_resume() -> dict:
    with _RESUME_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _build_resume_section(resume: dict) -> str:
    out: list[str] = []
    personal = resume.get("personal", {})
    out.append(f"Full name: {personal.get('name', '')}")
    out.append(f"Professional summary: {personal.get('summary', '')}")

    contact_bits = [c["label"] for c in personal.get("contact", [])]
    if contact_bits:
        out.append("Contact: " + " | ".join(contact_bits))

    out.append("\nProfessional experience (most recent first):")
    for job in resume.get("experience", []):
        duration = _format_duration(job["dates"]) or "duration unknown"
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


_RESUME = _load_resume()
RESUME_CONTEXT = _build_resume_section(_RESUME)


PORTFOLIO_CONTEXT = """
About the Batcave portfolio
- Site name: Quoc Anh's Batcave (Batman-themed personal portfolio).
- Stack: Next.js 16 App Router (React 19) on the frontend, Django + ADRF
  (async DRF) on the backend, deployed on Vercel.
- Live features: contact console (email, LinkedIn, GitHub, resume), project
  cards with tags, a search field, and Alfred — the AI butler chat.
- A full resume page is available at /resume; Alfred is given that resume
  data as reference material below.

Alfred himself
- Powered by Ollama running a small open-weights model (default llama3.2:3b).
- Streams tokens via Server-Sent Events from a Django ADRF AsyncAPIView.
- Rate-limited with a sliding-window limiter (10 requests / 60 seconds per
  IP hash) backed by Django's cache.
- Conversation logs live in SQLite via the Django ORM; metrics surface on
  /api/alfred/metrics/ for Prometheus scraping.
"""


SYSTEM_PROMPT = (
    "You are Alfred, the loyal and eloquent AI butler of Quoc Anh's Batcave "
    "portfolio. You speak in formal British English with dry wit. Answer "
    "visitor questions about Quoc Anh (his background, experience, skills, "
    "education, projects) using ONLY the reference material below. If a "
    "question cannot be answered from this material, say so plainly rather "
    "than inventing details. When asked about role tenure or dates, prefer "
    "the pre-computed durations listed beside each role. Keep answers "
    "concise (under 150 words) and stay in character.\n\n"
    "=== PORTFOLIO ===\n"
    f"{PORTFOLIO_CONTEXT}\n"
    "=== RESUME ===\n"
    f"{RESUME_CONTEXT}\n"
)
