"""Shoot-day packet builder: deterministic golden-hour math plus Gemini (or canned)
production notes for each shortlisted location."""

from datetime import date, datetime, timedelta
from typing import Optional

from . import gemini, moodboard, permits, weather
from .astro import golden_windows, tz_for
from .config import get_settings
from .schemas import Candidate, LocationNotes, Packet, PacketLocation, ScheduleDay, ScheduleStop, SceneBrief

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
            permits.permit_note(cand)
            or "File a film permit with the local film office; allow lead time for "
            + (", ".join(needs[:2]) if needs else "access and parking")
        ),
        shotlist=[s for s in shotlist if s],
    )


def _merge_permit_note(candidate: Candidate, notes: LocationNotes) -> str:
    data_note = permits.permit_note(candidate)
    if not data_note:
        return notes.permit_note
    if notes.permit_note and data_note not in notes.permit_note:
        return f"{notes.permit_note} {data_note}"
    return notes.permit_note or data_note


def _build_schedule(locations: list[PacketLocation], start_date: date) -> list[ScheduleDay]:
    days: list[ScheduleDay] = []
    for index, loc in enumerate(locations):
        day_num = index // 4 + 1
        while len(days) < day_num:
            day_date = start_date + timedelta(days=len(days))
            days.append(ScheduleDay(day=len(days) + 1, date=day_date.isoformat()))
        slot = index % 4
        start = datetime(2026, 1, 1, 9, 0) + timedelta(hours=slot * 2)
        golden = loc.golden_hour_pm or loc.golden_hour_am
        days[day_num - 1].stops.append(
            ScheduleStop(
                order=index + 1,
                scene_id=loc.scene_id,
                location_name=loc.name,
                start_local=start.strftime("%-I:%M %p"),
                golden_window=golden,
                weather_summary=loc.weather.summary,
            )
        )
    return days


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
        concept_url = moodboard.packet_image_url(brief) if brief else ""
        forecast = weather.forecast(c.lat, c.lng, on)
        locations.append(
            PacketLocation(
                scene_id=c.scene_id,
                candidate_id=c.id,
                name=c.name,
                address=c.address,
                lat=c.lat,
                lng=c.lng,
                concept_image_url=concept_url,
                concept_prompt=moodboard.build_prompt(brief) if brief else "",
                sunrise=gw["sunrise"],
                sunset=gw["sunset"],
                golden_hour_morning_end=gw["golden_hour_morning_end"],
                golden_hour_evening_start=gw["golden_hour_evening_start"],
                golden_hour_am=gw["golden_hour_am"],
                golden_hour_pm=gw["golden_hour_pm"],
                sun_note=gw["sun_note"],
                weather=forecast,
                parking=notes.parking,
                nearest_hospital=notes.nearest_hospital,
                power_note=notes.power_note,
                permit_note=_merge_permit_note(c, notes),
                permit_required=c.permit_required,
                permit_status=c.permit_status,
                permit_contact=c.permit_contact,
                permit_restrictions=c.permit_restrictions,
                shotlist=notes.shotlist,
            )
        )

    return Packet(
        production_title=title,
        shoot_date=shoot_date,
        base_city=base_city,
        locations=locations,
        schedule=_build_schedule(locations, on),
        notes=(
            "Golden-hour times are computed from each location's coordinates and the shoot "
            "date. Weather uses the configured provider or demo estimates. Production notes "
            "are AI-generated starting points; confirm permits, rights, and access with the "
            "relevant film office."
        ),
    )
