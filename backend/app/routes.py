"""API routes for the full scout pipeline."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, Response

from . import gemini, moodboard as moodboard_mod, packet as packet_mod, places, routing, script_analysis
from .config import get_settings
from .schemas import (
    AnalyzeRequest,
    Candidate,
    CandidatesRequest,
    Packet,
    PacketRequest,
    RouteRequest,
    RouteResult,
    SceneBrief,
    SegmentScriptRequest,
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
        "has_osrm": settings.has_osrm,
        "gemini_model": settings.gemini_model,
        "weather_provider": settings.weather_provider,
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


@router.post("/script/segments")
def script_segments(req: SegmentScriptRequest) -> dict:
    """Full script text -> deterministic scene segments for batch selection."""
    return {"scenes": script_analysis.segment_script(req.script_text)}


def _score_candidate(brief: SceneBrief, cand: Candidate) -> Candidate:
    """Score one candidate against the brief using its best available image."""
    image = places.scoring_image_bytes(cand)
    if image is not None:
        vs = gemini.score_candidate(brief, image)
        cand.match_score = vs.match_score
        cand.rationale = vs.rationale
        cand.flags = list(dict.fromkeys([*vs.flags, *cand.flags]))
    cand.street_view_url = places.best_image_url(cand)
    return cand


@router.post("/candidates")
def candidates(req: CandidatesRequest) -> dict:
    """For each brief, search a candidate pool, score each against the brief from its
    own photography, and keep the best matches. Scoring a larger pool and ranking by
    score lets brand-name false positives fall away."""
    base_city = req.base_city or settings.default_base_city
    center = places.geocode(base_city)
    live = settings.has_maps and settings.has_gemini
    out: list[Candidate] = []
    for brief in req.briefs:
        pool_size = max(8, req.max_per_brief * 2) if live else req.max_per_brief
        cands = places.search_candidates(brief, center, pool_size)
        if live and cands:
            with ThreadPoolExecutor(max_workers=6) as pool:
                cands = list(pool.map(lambda c: _score_candidate(brief, c), cands))
        else:
            for cand in cands:
                cand.street_view_url = places.best_image_url(cand)
        cands.sort(key=lambda c: c.match_score, reverse=True)
        out.extend(cands[: req.max_per_brief])
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


@router.get("/placephoto")
def placephoto(ref: str = "", name: str = "") -> Response:
    """Proxy a Places photo by resource name (key stays server-side), or a placeholder."""
    if settings.has_maps and ref:
        image = places.place_photo_bytes(ref)
        if image is not None:
            return Response(content=image, media_type="image/jpeg")
    svg = places.placeholder_svg(name or "Location", "Photo preview in demo mode")
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/moodboard")
def moodboard(brief: SceneBrief) -> Response:
    """Generate a cinematic concept frame for a scene's mood (Imagen / Gemini image)."""
    image = moodboard_mod.generate_image_bytes(brief)
    if image is not None:
        return Response(content=image, media_type="image/png")
    svg = places.placeholder_svg(
        brief.slugline or brief.location_type or "Scene", "Mood board preview in demo mode"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/moodboard/placeholder")
def moodboard_placeholder(name: str = "Scene", subtitle: str = "Concept art preview in demo mode") -> Response:
    svg = places.placeholder_svg(name or "Scene", subtitle or "Concept art preview in demo mode")
    return Response(content=svg, media_type="image/svg+xml")
