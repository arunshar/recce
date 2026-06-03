"""Mood-board prompt construction and packet-safe concept frame URLs."""

import base64
from functools import lru_cache
from urllib.parse import quote

from . import gemini
from .config import get_settings
from .schemas import SceneBrief

settings = get_settings()


def build_prompt(brief: SceneBrief) -> str:
    """Build a cinematic prompt from the scout brief."""
    parts = [
        "Cinematic concept frame for a film location mood board.",
        "Photographic production still, natural lensing, production-design reference.",
        "No text, no watermark, no logos.",
    ]
    scene = brief.location_type or brief.slugline
    if scene:
        parts.append(f"Location: {scene}.")
    if brief.int_ext:
        parts.append(f"Interior/exterior: {brief.int_ext}.")
    if brief.time_of_day:
        parts.append(f"Time of day: {brief.time_of_day}.")
    if brief.period:
        parts.append(f"Period: {brief.period}.")
    if brief.mood:
        parts.append(f"Mood keywords: {', '.join(brief.mood[:6])}.")
    if brief.key_visual_elements:
        parts.append(f"Key visual elements: {', '.join(brief.key_visual_elements[:6])}.")
    if brief.practical_needs:
        parts.append(f"Production constraints implied by the frame: {', '.join(brief.practical_needs[:4])}.")
    return " ".join(parts)


@lru_cache(maxsize=64)
def _generate_by_prompt(prompt: str) -> bytes | None:
    if not settings.has_gemini:
        return None
    return gemini.generate_mood_image_for_prompt(prompt)


def generate_image_bytes(brief: SceneBrief) -> bytes | None:
    """Generate a concept frame, or None in demo mode / provider failure."""
    return _generate_by_prompt(build_prompt(brief))


def packet_image_url(brief: SceneBrief) -> str:
    """Return a packet-safe image URL: live data URI when generated, demo placeholder otherwise."""
    prompt = build_prompt(brief)
    image = _generate_by_prompt(prompt)
    if image:
        encoded = base64.b64encode(image).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    name = quote(brief.slugline or brief.location_type or brief.scene_id or "Scene")
    subtitle = quote("Concept art preview in demo mode")
    return f"/api/moodboard/placeholder?name={name}&subtitle={subtitle}"


def placeholder_url(brief: SceneBrief) -> str:
    name = quote(brief.slugline or brief.location_type or brief.scene_id or "Scene")
    subtitle = quote("Concept art preview in demo mode")
    return f"/api/moodboard/placeholder?name={name}&subtitle={subtitle}"
