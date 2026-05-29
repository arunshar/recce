"""Google Places (New) + Street View, called server-side only so the Maps key
never reaches the browser. Falls back to bundled demo candidates and generated
placeholder imagery when no key is configured.
"""

import hashlib
import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx

from .config import get_settings
from .schemas import Candidate, SceneBrief

settings = get_settings()
DEMO_DIR = Path(__file__).parent / "demo_data"

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
STREETVIEW_URL = "https://maps.googleapis.com/maps/api/streetview"
STREETVIEW_META_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"

# Fallback city centers for demo mode and geocode failures.
_CITY_CENTERS = {
    "los angeles": (34.0522, -118.2437),
    "new york": (40.7128, -74.0060),
    "atlanta": (33.7490, -84.3880),
    "london": (51.5074, -0.1278),
    "vancouver": (49.2827, -123.1207),
    "new orleans": (29.9511, -90.0715),
}


def geocode(city: str) -> tuple[float, float]:
    """Resolve a base city to a (lat, lng). Uses the Geocoding API when a key is
    set, otherwise a small built-in table (default Los Angeles)."""
    city = (city or "").strip()
    if settings.has_maps and city:
        try:
            r = httpx.get(GEOCODE_URL, params={"address": city, "key": settings.maps_api_key}, timeout=15)
            j = r.json()
            if j.get("status") == "OK" and j.get("results"):
                loc = j["results"][0]["geometry"]["location"]
                return (loc["lat"], loc["lng"])
        except Exception as exc:
            print(f"[recce] geocode failed: {exc}")
    key = city.lower()
    for name, center in _CITY_CENTERS.items():
        if name in key:
            return center
    return _CITY_CENTERS["los angeles"]


def _cand_id(scene_id: str, place_id: str, name: str) -> str:
    return hashlib.sha1(f"{scene_id}:{place_id or name}".encode()).hexdigest()[:12]


def search_candidates(brief: SceneBrief, center: tuple[float, float], max_results: int = 4) -> list[Candidate]:
    """Find real-world candidates for a brief via Places text search. Falls back
    to demo candidates without a Maps key."""
    if not settings.has_maps:
        return demo_candidates_for(brief.scene_id)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.maps_api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.types"
        ),
    }
    seen: dict[str, Candidate] = {}
    for query in (brief.search_queries or [brief.location_type]):
        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": center[0], "longitude": center[1]},
                    "radius": 50000.0,
                }
            },
            "maxResultCount": max_results,
        }
        try:
            r = httpx.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=20)
            places = r.json().get("places", [])
        except Exception as exc:
            print(f"[recce] places search failed for '{query}': {exc}")
            continue
        for p in places:
            pid = p.get("id", "")
            if pid and pid in seen:
                continue
            loc = p.get("location", {})
            name = (p.get("displayName") or {}).get("text", "Unnamed location")
            cand = Candidate(
                id=_cand_id(brief.scene_id, pid, name),
                scene_id=brief.scene_id,
                name=name,
                address=p.get("formattedAddress", ""),
                lat=loc.get("latitude", center[0]),
                lng=loc.get("longitude", center[1]),
                place_id=pid,
                rating=p.get("rating"),
                types=p.get("types", []),
            )
            seen[pid or cand.id] = cand
            if len(seen) >= max_results:
                break
        if len(seen) >= max_results:
            break
    return list(seen.values())[:max_results]


def street_view_image(lat: float, lng: float, size: str = "640x420") -> Optional[bytes]:
    """Fetch a Street View Static image. Returns None without a key or imagery."""
    if not settings.has_maps:
        return None
    try:
        r = httpx.get(
            STREETVIEW_URL,
            params={"location": f"{lat},{lng}", "size": size, "fov": 90, "key": settings.maps_api_key},
            timeout=15,
        )
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            return r.content
    except Exception as exc:
        print(f"[recce] street view fetch failed: {exc}")
    return None


def placeholder_svg(name: str, subtitle: str = "") -> str:
    """A cinematic placeholder frame used when no real Street View image is available."""
    safe = html.escape(name or "Location")
    sub = html.escape(subtitle or "")
    holes = "".join(
        f'<rect x="{x}" y="9" width="24" height="11" rx="2" fill="#0b1220"/>'
        f'<rect x="{x}" y="400" width="24" height="11" rx="2" fill="#0b1220"/>'
        for x in range(36, 600, 64)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420" viewBox="0 0 640 420">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f172a"/>
      <stop offset="1" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="640" height="420" fill="url(#g)"/>
  {holes}
  <rect x="18" y="28" width="604" height="364" fill="none" stroke="#334155" stroke-width="2"/>
  <text x="320" y="205" fill="#e2e8f0" font-family="ui-sans-serif, system-ui, sans-serif" font-size="27" font-weight="600" text-anchor="middle">{safe}</text>
  <text x="320" y="240" fill="#94a3b8" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14" text-anchor="middle">{sub}</text>
</svg>"""


# ---- demo fallbacks ----

@lru_cache
def _demo_candidates_raw() -> str:
    return (DEMO_DIR / "sample_candidates.json").read_text(encoding="utf-8")


def demo_candidates_for(scene_id: str) -> list[Candidate]:
    data = json.loads(_demo_candidates_raw())
    return [Candidate(**d) for d in data if d.get("scene_id") == scene_id]
