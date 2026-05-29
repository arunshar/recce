"""Gemini integration.

Phase 1 ships scene understanding. Vision scoring (Phase 2), the shoot-day packet
(Phase 4), and mood images (stretch) extend this module. When no Gemini key is set,
every function falls back to bundled demo data so the full flow works offline.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .config import get_settings
from .schemas import SceneBrief

settings = get_settings()
DEMO_DIR = Path(__file__).parent / "demo_data"


@lru_cache
def _get_client():
    """Return a cached Gemini client, or None when no key is configured."""
    if not settings.has_gemini:
        return None
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


SCENE_SYSTEM_INSTRUCTION = """You are an expert film location manager and first assistant director.
Read the screenplay text and break it into one structured location brief per distinct
filming location (one brief per scene heading / slugline).

For each brief:
- scene_id: a short id like "S1", "S2" in scene order.
- slugline: the scene heading, e.g. "INT. SALTWATER DINER - DAWN".
- int_ext: INT, EXT, or INT/EXT.
- location_type: a concise, scoutable description, e.g. "retro seaside diner".
- time_of_day: DAY, NIGHT, DAWN, DUSK, or GOLDEN HOUR.
- period: the era it must read as on camera, e.g. "present day" or "1970s".
- mood: 3 to 6 short adjectives capturing the tone.
- key_visual_elements: concrete things the location must physically have on camera.
- practical_needs: production logistics this location implies (access, power, parking,
  permits, effects, safety, crowd control).
- search_queries: 3 to 5 specific Google Places queries a scout would type to find real
  candidate places near the production base. Make them findable and specific, and include
  the base city or a nearby area in each query.

Be concrete and production-minded. Prefer real, locatable place descriptions."""


def extract_scene_briefs(
    scene_text: str,
    base_city: Optional[str] = None,
    era: Optional[str] = None,
    budget: Optional[str] = None,
) -> list[SceneBrief]:
    """Turn raw screenplay text into structured location briefs."""
    base_city = base_city or settings.default_base_city
    client = _get_client()
    if client is None or not scene_text.strip():
        return _demo_briefs()

    from google.genai import types

    context = f"Production base city: {base_city}."
    if era:
        context += f" Target era / period: {era}."
    if budget:
        context += f" Budget tier: {budget}."
    prompt = f"{context}\n\nSCREENPLAY:\n{scene_text.strip()}"

    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SCENE_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=list[SceneBrief],
                temperature=0.3,
            ),
        )
        briefs: list[SceneBrief] = []
        for i, item in enumerate(resp.parsed or [], start=1):
            brief = item if isinstance(item, SceneBrief) else SceneBrief(**item)
            if not brief.scene_id:
                brief.scene_id = f"S{i}"
            briefs.append(brief)
        if briefs:
            return briefs
    except Exception as exc:  # any API/parse error falls back to demo data
        print(f"[recce] Gemini scene extraction failed, using demo briefs: {exc}")
    return _demo_briefs()


@lru_cache
def _demo_briefs_raw() -> str:
    return (DEMO_DIR / "sample_briefs.json").read_text(encoding="utf-8")


def _demo_briefs() -> list[SceneBrief]:
    return [SceneBrief(**d) for d in json.loads(_demo_briefs_raw())]
