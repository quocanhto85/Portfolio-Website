"""Turn database content into retrievable text chunks (structural chunking).

The content is already well-structured and small, so we chunk by semantic unit
(a role, a degree, an article section) rather than by a fixed token window —
each chunk maps to something a visitor might ask about.

Media rule (per the architecture): never embed a binary or a raw URL. A
video/image contributes only its caption/alt text to the embedded text; its
URL and type are recorded in the chunk's ``metadata`` so Alfred can cite or
link it without the URL polluting the vector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..content_models import Article
from ..content_service import get_resume_data
from ..knowledge import format_duration

MEDIA_TYPES = {"video", "image"}


@dataclass
class Chunk:
    chunk_id: str
    source_type: str  # "resume" | "article"
    source_id: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_resume(resume: dict[str, Any]) -> list[Chunk]:
    chunks: list[Chunk] = []
    personal = resume.get("personal", {})
    name = personal.get("name", "")

    contact = " | ".join(c.get("label", "") for c in personal.get("contact", []))
    summary = [f"{name} — professional summary.", personal.get("summary", "")]
    if contact:
        summary.append(f"Contact: {contact}")
    chunks.append(
        Chunk(
            chunk_id="resume:profile",
            source_type="resume",
            source_id="profile",
            title=f"{name} — Summary",
            text="\n".join(p for p in summary if p),
            metadata={"section": "summary"},
        )
    )

    for i, job in enumerate(resume.get("experience", [])):
        duration = format_duration(job.get("dates", "")) or "duration unknown"
        lines = [
            f"{name}'s professional experience:",
            f"{job.get('role', '')} at {job.get('company', '')} "
            f"({job.get('location', '')}), {job.get('dates', '')} ({duration}).",
        ]
        lines += [f"- {b}" for b in job.get("bullets", [])]
        chunks.append(
            Chunk(
                chunk_id=f"resume:experience:{i}",
                source_type="resume",
                source_id=f"experience:{i}",
                title=f"{job.get('role', '')} @ {job.get('company', '')}",
                text="\n".join(lines),
                metadata={
                    "section": "experience",
                    "company": job.get("company"),
                    "dates": job.get("dates"),
                    "duration": duration,
                },
            )
        )

    for i, edu in enumerate(resume.get("education", [])):
        chunks.append(
            Chunk(
                chunk_id=f"resume:education:{i}",
                source_type="resume",
                source_id=f"education:{i}",
                title=edu.get("school", "Education"),
                text=(
                    f"{name}'s education: {edu.get('degree', '')} at "
                    f"{edu.get('school', '')} ({edu.get('location', '')}), "
                    f"{edu.get('details', '')}, {edu.get('dates', '')}."
                ),
                metadata={"section": "education"},
            )
        )

    skills = resume.get("skills", [])
    if skills:
        lines = [f"{name}'s skills:"]
        lines += [f"- {s.get('label', '')}: {s.get('value', '')}" for s in skills]
        chunks.append(
            Chunk(
                chunk_id="resume:skills",
                source_type="resume",
                source_id="skills",
                title="Skills",
                text="\n".join(lines),
                metadata={"section": "skills"},
            )
        )

    for i, proj in enumerate(resume.get("projects", [])):
        lines = [f"{name}'s personal project: {proj.get('name', '')}."]
        lines += [f"- {b}" for b in proj.get("bullets", [])]
        chunks.append(
            Chunk(
                chunk_id=f"resume:project:{i}",
                source_type="resume",
                source_id=f"project:{i}",
                title=proj.get("name", "Project"),
                text="\n".join(lines),
                metadata={"section": "projects"},
            )
        )

    certs = resume.get("certifications", [])
    if certs:
        lines = [f"{name}'s courses & certifications:"]
        lines += [
            f"- {c.get('title', '')} ({c.get('issued', '')})." for c in certs
        ]
        chunks.append(
            Chunk(
                chunk_id="resume:certifications",
                source_type="resume",
                source_id="certifications",
                title="Courses & Certifications",
                text="\n".join(lines),
                metadata={"section": "certifications"},
            )
        )

    return chunks


def chunk_article(article: dict[str, Any]) -> list[Chunk]:
    slug = article["slug"]
    title = article["title"]
    base_meta = {"date": article.get("date"), "tags": article.get("tags", [])}
    chunks: list[Chunk] = []

    lead = [f"Article: {title}."]
    if article.get("date"):
        lead.append(f"Date: {article['date']}.")
    if article.get("description"):
        lead.append(article["description"])
    if article.get("tags"):
        lead.append("Tags: " + ", ".join(article["tags"]) + ".")
    chunks.append(
        Chunk(
            chunk_id=f"article:{slug}:lead",
            source_type="article",
            source_id=slug,
            title=title,
            text="\n".join(lead),
            metadata={**base_meta, "section": "lead"},
        )
    )

    # Walk blocks, opening a new section chunk at each heading.
    state = {"idx": 0, "heading": title, "buf": [], "media": []}

    def flush() -> None:
        if not state["buf"] and not state["media"]:
            return
        body = "\n".join(state["buf"]).strip()
        if state["media"]:
            kinds = ", ".join(sorted({m["type"] for m in state["media"]}))
            body = f"{body}\n[Includes {kinds} media.]".strip()
        heading = state["heading"]
        chunks.append(
            Chunk(
                chunk_id=f"article:{slug}:{state['idx']}",
                source_type="article",
                source_id=slug,
                title=f"{title} — {heading}" if heading != title else title,
                text=f"From the article '{title}', section '{heading}':\n{body}",
                metadata={
                    **base_meta,
                    "section": heading,
                    "media": state["media"] or None,
                },
            )
        )
        state["idx"] += 1
        state["buf"] = []
        state["media"] = []

    for block in article.get("content", []):
        btype = block.get("type")
        if btype == "heading":
            flush()
            state["heading"] = block.get("text", "")
        elif btype == "list":
            state["buf"].extend(f"- {item}" for item in block.get("items", []))
        elif btype in MEDIA_TYPES:
            caption = block.get("caption") or block.get("alt") or ""
            if caption:
                state["buf"].append(caption)
            state["media"].append(
                {"type": btype, "src": block.get("src"), "poster": block.get("poster")}
            )
        elif btype == "report":
            paper = block.get("paper", {})
            bits = [
                paper.get("title", ""),
                paper.get("subtitle", ""),
                f"Venue: {paper['venue']}" if paper.get("venue") else "",
                f"Supervisor: {paper['supervisor']}" if paper.get("supervisor") else "",
            ]
            state["buf"].append("Report — " + ". ".join(b for b in bits if b) + ".")
            state["media"].append({"type": "report", "src": paper.get("url")})
        elif block.get("text"):  # paragraph or any future text-bearing block
            state["buf"].append(block["text"])

    flush()
    return chunks


async def build_chunks(db) -> list[Chunk]:
    """Assemble every chunk from the content DB (resume rows + article blocks)."""
    chunks: list[Chunk] = []

    resume = await get_resume_data(db)
    if resume:
        chunks.extend(chunk_resume(resume))

    articles = (
        await db.scalars(
            select(Article)
            .options(selectinload(Article.blocks))
            .order_by(Article.date.desc())
        )
    ).all()
    for art in articles:
        chunks.extend(
            chunk_article(
                {
                    "slug": art.slug,
                    "title": art.title,
                    "date": art.date,
                    "description": art.description,
                    "tags": art.tags or [],
                    "content": [
                        {"type": b.type, **(b.data or {})} for b in art.blocks
                    ],
                }
            )
        )
    return chunks
