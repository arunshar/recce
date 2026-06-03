"""Deterministic screenplay segmentation used for batch uploads and demo fallback."""

import re
from collections import Counter

from .schemas import SceneBrief, ScriptScene

SLUGLINE_RE = re.compile(
    r"^\s*((?:INT|EXT|INT/EXT|I/E)\.?\s+[-A-Z0-9'\".,/() ]+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TIME_TOKENS = ("DAWN", "MORNING", "DAY", "AFTERNOON", "DUSK", "GOLDEN HOUR", "NIGHT")
STOP_WORDS = {
    "THE",
    "A",
    "AN",
    "AND",
    "OF",
    "AT",
    "IN",
    "ON",
    "TO",
    "FROM",
    "LATER",
    "CONTINUOUS",
}


def segment_script(script_text: str) -> list[ScriptScene]:
    """Split a screenplay-like document into scene segments by slugline."""
    text = script_text.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(SLUGLINE_RE.finditer(text))
    if not matches:
        return []

    scenes: list[ScriptScene] = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(text)
        slugline = " ".join(match.group(1).strip().split())
        body = text[start:end].strip()
        scenes.append(
            ScriptScene(
                scene_id=f"S{index}",
                slugline=slugline,
                scene_text=body,
                int_ext=_extract_int_ext(slugline),
                location_type=_extract_location_type(slugline),
                time_of_day=_extract_time_of_day(slugline),
                characters=_extract_characters(body),
            )
        )
    return scenes


def briefs_from_segments(segments: list[ScriptScene], base_city: str = "") -> list[SceneBrief]:
    """Create scoutable briefs from deterministic scene segments."""
    briefs: list[SceneBrief] = []
    for scene in segments:
        location = scene.location_type or scene.slugline
        visual_words = _visual_keywords(scene.scene_text)
        mood = _mood_keywords(scene.scene_text, scene.time_of_day)
        city_suffix = f" near {base_city}" if base_city else ""
        queries = [
            f"{location}{city_suffix}",
            f"film location {location}{city_suffix}",
            f"{scene.int_ext.lower()} {location}{city_suffix}".strip(),
        ]
        briefs.append(
            SceneBrief(
                scene_id=scene.scene_id,
                slugline=scene.slugline,
                int_ext=scene.int_ext,
                location_type=location,
                time_of_day=scene.time_of_day,
                period="present day",
                mood=mood,
                key_visual_elements=visual_words[:5],
                practical_needs=_practical_needs(scene),
                search_queries=[q for q in dict.fromkeys(queries) if q],
            )
        )
    return briefs


def extract_scene_briefs(script_text: str, base_city: str = "") -> list[SceneBrief]:
    """Convenience wrapper used by non-LLM code paths."""
    return briefs_from_segments(segment_script(script_text), base_city)


def _extract_int_ext(slugline: str) -> str:
    upper = slugline.upper()
    if upper.startswith("INT/EXT") or upper.startswith("I/E"):
        return "INT/EXT"
    if upper.startswith("INT"):
        return "INT"
    if upper.startswith("EXT"):
        return "EXT"
    return ""


def _extract_time_of_day(slugline: str) -> str:
    upper = slugline.upper()
    for token in TIME_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", upper):
            return token
    return ""


def _extract_location_type(slugline: str) -> str:
    cleaned = re.sub(r"^(INT/EXT|INT|EXT|I/E)\.?\s*", "", slugline, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*[-–]\s*(DAWN|MORNING|DAY|AFTERNOON|DUSK|GOLDEN HOUR|NIGHT)\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(" - ", " ").strip(" -")
    return cleaned.title()


def _extract_characters(scene_text: str) -> list[str]:
    candidates: list[str] = []
    for line in scene_text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) > 32:
            continue
        if stripped.isupper() and re.match(r"^[A-Z][A-Z0-9 .'-]+(?:\s*\(.*\))?$", stripped):
            name = re.sub(r"\s*\(.*\)\s*$", "", stripped).strip()
            if name not in STOP_WORDS:
                candidates.append(name.title())
    return [name for name, _ in Counter(candidates).most_common(8)]


def _visual_keywords(scene_text: str) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z'-]{3,}\b", scene_text.lower())
    blocked = {w.lower() for w in STOP_WORDS} | {
        "with",
        "into",
        "over",
        "under",
        "through",
        "their",
        "there",
        "then",
        "only",
        "across",
        "inside",
        "outside",
        "camera",
        "sound",
    }
    counts = Counter(w for w in words if w not in blocked)
    return [word.replace("-", " ") for word, _ in counts.most_common(8)]


def _mood_keywords(scene_text: str, time_of_day: str) -> list[str]:
    lower = scene_text.lower()
    moods: list[str] = []
    checks = [
        ("tense", ("tense", "threat", "alarm", "run", "blood")),
        ("romantic", ("kiss", "warm", "soft", "intimate")),
        ("lonely", ("alone", "empty", "quiet", "silent")),
        ("gritty", ("dirty", "graffiti", "industrial", "concrete")),
        ("dreamlike", ("mist", "haze", "surreal", "glow")),
        ("urgent", ("rush", "sirens", "shout", "chase")),
    ]
    for label, tokens in checks:
        if any(token in lower for token in tokens):
            moods.append(label)
    if time_of_day in {"DAWN", "DUSK", "GOLDEN HOUR"}:
        moods.append("atmospheric")
    if not moods:
        moods = ["cinematic", "naturalistic", "location-forward"]
    return moods[:6]


def _practical_needs(scene: ScriptScene) -> list[str]:
    needs = ["location access", "crew parking"]
    if scene.int_ext == "EXT":
        needs.append("weather cover")
    if scene.time_of_day == "NIGHT":
        needs.append("night permit")
        needs.append("generator power")
    if scene.characters:
        needs.append("holding area")
    return needs
