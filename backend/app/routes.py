"""API routes. Endpoints grow phase by phase."""

from pathlib import Path

from fastapi import APIRouter

from . import gemini
from .config import get_settings
from .schemas import AnalyzeRequest

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


@router.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    """Scene text -> structured location briefs (Gemini, or demo data without a key)."""
    base_city = req.base_city or settings.default_base_city
    briefs = gemini.extract_scene_briefs(req.scene_text, base_city, req.era, req.budget)
    return {
        "base_city": base_city,
        "demo_mode": settings.demo_mode,
        "briefs": briefs,
    }
