"""Trivial JSON endpoints — the FastAPI equivalent of the old ``portfolio_api``."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health_check() -> dict:
    return {"status": "ok", "message": "Batcave backend online"}


@router.get("/api/projects")
async def get_projects() -> dict:
    return {
        "projects": [
            {
                "title": "Futuristic Autonomous Tram Technology in Smart Cities",
                "date": "2025-07-12",
                "category": "AI",
            }
        ]
    }
