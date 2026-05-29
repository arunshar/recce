"""Shoot-day packet builder: deterministic golden-hour math plus Gemini (or canned)
production notes for each shortlisted location."""

from datetime import date, timedelta
from typing import Optional

from . import gemini
from .astro import golden_windows, tz_for
from .config import get_settings
from .schemas import Candidate, LocationNotes, Packet, PacketLocation, SceneBrief

settings = get_settings()


def _default_shoot_date() -> str:
    return (date.today() + timedelta(days=14)).isoformat()


def _brief_for(briefs: list[SceneBrief], scene_id: str) -> Optional[SceneBrief]:
    for b in briefs:
        if b.scene_id == scene_id:
            return b
    return None


def _canned_notes(brief: Optional[SceneBrief], cand: Candidate) -> LocationNotes:
    needs = brief.practical_needs if brief else []
    tod = (brief.time_of_day if brief else "").title()
    shotlist: list[str] = []
    if brief:
        shotlist.append(f"Establishing wide of the {brief.location_type}")
        if brief.key_visual_elements:
            shotlist.append(f"Coverage featuring {brief.key_visual_elements[0]}")
        shotlist.append(f"{tod} mood insert" if tod else "Atmosphere detail insert")
    return LocationNotes(
        parking=["Scout a nearby lot or street parking for grip and lighting trucks"],
        nearest_hospital="Confirm the nearest emergency room during the tech scout",
        power_note="Plan a generator unless verified house power is sufficient",
        permit_note=(
            "File a film permit with the local film office; allow lead time for "
            + (", ".join(needs[:2]) if needs else "access and parking")
        ),
        shotlist=[s for s in shotlist if s],
    )


def build_packet(
    candidates: list[Candidate],
    briefs: list[SceneBrief],
    base_city: str,
    shoot_date: Optional[str] = None,
    production_title: Optional[str] = None,
) -> Packet:
    title = production_title or "Untitled Production"
    tz = tz_for(base_city)
    try:
        on = date.fromisoformat(shoot_date) if shoot_date else date.today() + timedelta(days=14)
    except ValueError:
        on = date.today() + timedelta(days=14)
    shoot_date = on.isoformat()

    locations: list[PacketLocation] = []
    for c in candidates:
        gw = golden_windows(c.lat, c.lng, on, tz)
        brief = _brief_for(briefs, c.scene_id)
        notes = gemini.generate_location_notes(brief, c) if settings.has_gemini else _canned_notes(brief, c)
        locations.append(
            PacketLocation(
                name=c.name,
                address=c.address,
                lat=c.lat,
                lng=c.lng,
                golden_hour_am=gw["golden_hour_am"],
                golden_hour_pm=gw["golden_hour_pm"],
                sun_note=gw["sun_note"],
                parking=notes.parking,
                nearest_hospital=notes.nearest_hospital,
                power_note=notes.power_note,
                permit_note=notes.permit_note,
                shotlist=notes.shotlist,
            )
        )

    return Packet(
        production_title=title,
        shoot_date=shoot_date,
        base_city=base_city,
        locations=locations,
        notes=(
            "Golden-hour times are computed from each location's coordinates and the shoot "
            "date. Production notes are AI-generated starting points; confirm permits and "
            "access with the relevant film office."
        ),
    )
