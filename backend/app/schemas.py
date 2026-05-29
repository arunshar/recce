"""Pydantic models shared across the Recce pipeline."""

from typing import Optional

from pydantic import BaseModel, Field


class SceneBrief(BaseModel):
    """A structured location brief extracted from one screenplay scene."""

    scene_id: str
    slugline: str = ""
    int_ext: str = ""           # INT, EXT, or INT/EXT
    location_type: str = ""     # e.g. "roadside diner", "coastal cliff"
    time_of_day: str = ""       # DAY, NIGHT, DAWN, DUSK, GOLDEN HOUR
    period: str = "present day"
    mood: list[str] = Field(default_factory=list)
    key_visual_elements: list[str] = Field(default_factory=list)
    practical_needs: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    """A real-world location candidate matched to a scene brief."""

    id: str
    scene_id: str = ""
    name: str
    address: str = ""
    lat: float
    lng: float
    place_id: str = ""
    rating: Optional[float] = None
    types: list[str] = Field(default_factory=list)
    street_view_url: Optional[str] = None
    photo_url: Optional[str] = None
    match_score: int = 0        # 0 to 100
    rationale: str = ""
    flags: list[str] = Field(default_factory=list)


class VisionScore(BaseModel):
    """Gemini's verdict on one candidate's Street View image vs. the brief."""

    match_score: int = 0        # 0 to 100
    rationale: str = ""
    flags: list[str] = Field(default_factory=list)


class RouteStop(BaseModel):
    order: int
    candidate_id: str
    name: str
    lat: float
    lng: float
    drive_minutes_from_prev: float = 0.0
    arrive_local: str = ""
    window_note: str = ""


class RouteResult(BaseModel):
    base_name: str
    base_lat: float
    base_lng: float
    stops: list[RouteStop] = Field(default_factory=list)
    total_distance_km: float = 0.0
    total_drive_minutes: float = 0.0


class PacketLocation(BaseModel):
    name: str
    address: str = ""
    lat: float
    lng: float
    golden_hour_am: str = ""
    golden_hour_pm: str = ""
    sun_note: str = ""
    parking: list[str] = Field(default_factory=list)
    nearest_hospital: str = ""
    power_note: str = ""
    permit_note: str = ""
    shotlist: list[str] = Field(default_factory=list)


class Packet(BaseModel):
    production_title: str = "Untitled Production"
    shoot_date: str = ""
    base_city: str = ""
    locations: list[PacketLocation] = Field(default_factory=list)
    notes: str = ""


class LocationNotes(BaseModel):
    """AI-generated (or canned) production notes for one location in the packet."""

    parking: list[str] = Field(default_factory=list)
    nearest_hospital: str = ""
    power_note: str = ""
    permit_note: str = ""
    shotlist: list[str] = Field(default_factory=list)


# ---- Request bodies ----

class AnalyzeRequest(BaseModel):
    scene_text: str
    base_city: Optional[str] = None
    era: Optional[str] = None
    budget: Optional[str] = None


class CandidatesRequest(BaseModel):
    briefs: list[SceneBrief]
    base_city: Optional[str] = None
    max_per_brief: int = 4


class RouteRequest(BaseModel):
    candidates: list[Candidate]
    base_city: Optional[str] = None
    shoot_date: Optional[str] = None


class PacketRequest(BaseModel):
    candidates: list[Candidate]
    briefs: list[SceneBrief] = Field(default_factory=list)
    production_title: Optional[str] = "Untitled Production"
    shoot_date: Optional[str] = None
    base_city: Optional[str] = None
