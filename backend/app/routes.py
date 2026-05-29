"""API routes. Endpoints are added phase by phase; Phase 0 ships health + demo scene."""

from pathlib import Path

from fastapi import APIRouter

from .config import get_settings

router = APIRouter(prefix="/api")
settings = get_settings()
DEMO_DIR = Path(__file__).parent / "demo_data"


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "has_gemini": settings.has_gemini,
        "has_maps": settings.has_maps,
        "gemini_model": settings.gemini_model,
    }


@router.get("/demo/scene")
def demo_scene() -> dict:
    p = DEMO_DIR / "sample_screenplay.txt"
    return {"scene_text": p.read_text(encoding="utf-8") if p.exists() else ""}
