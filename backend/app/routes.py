"""API routes for the full scout pipeline."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Response

from . import gemini, packet as packet_mod, places, routing
from .config import get_settings
from .schemas import (
    AnalyzeRequest,
    CandidatesRequest,
    Packet,
    PacketRequest,
    RouteRequest,
    RouteResult,
)

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
    return {"base_city": base_city, "demo_mode": settings.demo_mode, "briefs": briefs}


def _sv_url(cand) -> str:
    return f"/api/streetview?lat={cand.lat}&lng={cand.lng}&name={quote(cand.name)}"


@router.post("/candidates")
def candidates(req: CandidatesRequest) -> dict:
    """For each brief, find candidate locations and score them against the brief."""
    base_city = req.base_city or settings.default_base_city
    center = places.geocode(base_city)
    out = []
    for brief in req.briefs:
        cands = places.search_candidates(brief, center, req.max_per_brief)
        for cand in cands:
            if settings.has_maps and settings.has_gemini:
                image = places.street_view_image(cand.lat, cand.lng)
                if image is not None:
                    vs = gemini.score_candidate(brief, image)
                    cand.match_score = vs.match_score
                    cand.rationale = vs.rationale
                    cand.flags = vs.flags
            cand.street_view_url = _sv_url(cand)
        cands.sort(key=lambda c: c.match_score, reverse=True)
        out.extend(cands)
    return {
        "base_city": base_city,
        "center": {"lat": center[0], "lng": center[1]},
        "demo_mode": settings.demo_mode,
        "candidates": out,
    }


@router.post("/route", response_model=RouteResult)
def route(req: RouteRequest) -> RouteResult:
    """Optimize a scout-day route across the shortlisted candidates."""
    base_city = req.base_city or settings.default_base_city
    center = places.geocode(base_city)
    return routing.optimize(center, base_city, req.candidates)


@router.post("/packet", response_model=Packet)
def packet(req: PacketRequest) -> Packet:
    """Generate the shoot-day logistics packet for the shortlisted candidates."""
    base_city = req.base_city or settings.default_base_city
    return packet_mod.build_packet(
        req.candidates, req.briefs, base_city, req.shoot_date, req.production_title
    )


@router.get("/streetview")
def streetview(lat: float, lng: float, name: str = "") -> Response:
    """Proxy a Street View image (key stays server-side), or a placeholder in demo mode."""
    if settings.has_maps:
        image = places.street_view_image(lat, lng)
        if image is not None:
            return Response(content=image, media_type="image/jpeg")
    svg = places.placeholder_svg(name or "Location", "Street View preview in demo mode")
    return Response(content=svg, media_type="image/svg+xml")
