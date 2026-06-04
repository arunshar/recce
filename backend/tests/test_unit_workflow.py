from datetime import date

import pytest

from app import astro, moodboard, permits, places, routing, script_analysis, weather
from app.schemas import Candidate, LocationRecord, SceneBrief

pytestmark = pytest.mark.unit


def brief(scene_id: str = "S1", location_type: str = "coastal pier") -> SceneBrief:
    return SceneBrief(
        scene_id=scene_id,
        slugline="EXT. COASTAL PIER - DUSK",
        int_ext="EXT",
        location_type=location_type,
        time_of_day="DUSK",
        mood=["romantic", "windswept"],
        key_visual_elements=["pier", "boardwalk"],
        practical_needs=["crowd control"],
        search_queries=[f"{location_type} Los Angeles"],
    )


def candidate(id_: str = "c1", name: str = "Echo Park") -> Candidate:
    return Candidate(
        id=id_,
        scene_id="S1",
        name=name,
        address="Los Angeles, CA",
        lat=34.05,
        lng=-118.24,
        types=["park"],
        match_score=70,
    )


def test_script_analysis_extracts_scene_fields_and_briefs():
    script = """INT/EXT. ROOFTOP BAR - GOLDEN HOUR

A warm, tense goodbye under string lights.

MAYA
Stay.

EXT. INDUSTRIAL ALLEY - NIGHT

Sirens cut through mist and concrete.
"""
    scenes = script_analysis.segment_script(script)
    assert [s.scene_id for s in scenes] == ["S1", "S2"]
    assert scenes[0].int_ext == "INT/EXT"
    assert scenes[0].location_type == "Rooftop Bar"
    assert scenes[0].time_of_day == "GOLDEN HOUR"
    assert "Maya" in scenes[0].characters

    briefs = script_analysis.briefs_from_segments(scenes, "Los Angeles, CA")
    assert briefs[0].search_queries[0] == "Rooftop Bar near Los Angeles, CA"
    assert "holding area" in briefs[0].practical_needs
    assert "urgent" in briefs[1].mood


def test_script_analysis_returns_empty_for_no_sluglines():
    assert script_analysis.segment_script("A paragraph with no screenplay headings.") == []


def test_astro_timezone_and_golden_windows():
    assert astro.tz_for("New York, NY") == "America/New_York"
    assert astro.tz_for("Unknown City") == "America/Los_Angeles"
    windows = astro.golden_windows(34.0522, -118.2437, date(2026, 6, 13), astro.tz_for("Los Angeles, CA"))
    assert windows["sunrise"]
    assert windows["sunset"]
    assert "-" in windows["golden_hour_pm"]
    assert "Los Angeles" in windows["sun_note"]


def test_moodboard_prompt_and_packet_urls(monkeypatch):
    b = brief(location_type="retro seaside diner")
    prompt = moodboard.build_prompt(b)
    assert "retro seaside diner" in prompt
    assert "No text" in prompt
    assert "pier, boardwalk" in prompt

    monkeypatch.setattr(moodboard, "_generate_by_prompt", lambda _: b"\x89PNGdemo")
    assert moodboard.generate_image_bytes(b) == b"\x89PNGdemo"
    assert moodboard.packet_image_url(b).startswith("data:image/png;base64,")

    monkeypatch.setattr(moodboard, "_generate_by_prompt", lambda _: None)
    assert moodboard.packet_image_url(b).startswith("/api/moodboard/placeholder")


def test_permit_enrichment_and_merge_unique_ids():
    b1 = brief("S1")
    b2 = brief("S2")
    merged_1 = permits.merge_open_locations(b1, (34.0, -118.2), [], 4)
    merged_2 = permits.merge_open_locations(b2, (34.0, -118.2), [], 4)
    assert any(c.name == "Santa Monica Pier" and c.permit_required for c in merged_1)
    assert {c.id for c in merged_1}.isdisjoint({c.id for c in merged_2})

    c = candidate(name="Griffith Observatory")
    enriched = permits.enrich_candidate(c)
    assert enriched.permit_required
    assert enriched.permit_contact == "FilmLA"
    assert "Restrictions:" in permits.permit_note(enriched)


def test_permit_record_scoring_ignores_unusable_records():
    no_coords = LocationRecord(
        id="x",
        name="Pier Without Coordinates",
        categories=["pier"],
        permit_required=True,
        source="test",
    )
    score = permits._score_record(brief(), no_coords)
    assert score > 0


def test_places_demo_helpers_are_safe_and_keyless():
    assert places.geocode("Vancouver") == (49.2827, -123.1207)
    c = candidate()
    assert places.best_image_url(c).startswith("/api/streetview?")
    svg = places.placeholder_svg("<script>alert(1)</script>", "demo")
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_routing_haversine_two_opt_and_empty_route(monkeypatch):
    assert routing.haversine_km((34.0522, -118.2437), (34.0522, -118.2437)) == 0
    candidates = [
        Candidate(id="a", name="A", lat=34.0, lng=-118.2, permit_required=True, permit_restrictions=["night access"]),
        Candidate(id="b", name="B", lat=34.1, lng=-118.3),
    ]
    monkeypatch.setattr(routing.osrm, "optimize_trip", lambda *_: None)
    result = routing.optimize((34.05, -118.24), "LA", candidates)
    assert result.route_method == "haversine_2opt"
    assert len(result.stops) == 2
    assert "permit review" in result.stops[0].window_note
    assert routing.optimize((34.05, -118.24), "LA", []).stops == []


def test_routing_uses_osrm_trip_when_available(monkeypatch):
    candidates = [
        Candidate(id="a", name="A", lat=34.0, lng=-118.2),
        Candidate(id="b", name="B", lat=34.1, lng=-118.3),
    ]
    trip = routing.osrm.OsrmTrip(candidate_order=[1, 0], leg_minutes=[7.5, 4.5], total_distance_km=12.3)
    monkeypatch.setattr(routing.osrm, "optimize_trip", lambda *_: trip)
    result = routing.optimize((34.05, -118.24), "LA", candidates)
    assert result.route_method == "osrm_trip"
    assert [s.candidate_id for s in result.stops] == ["b", "a"]
    assert result.total_distance_km == 12.3


def test_weather_demo_and_summary_are_stable():
    first = weather.forecast(34.0, -118.2, date(2026, 6, 13))
    second = weather.forecast(34.0, -118.2, date(2026, 6, 13))
    assert first == second
    assert first.source == "demo"
    assert "precip" in first.summary
    assert weather._summary(None, None, None, None).startswith("Forecast unavailable")
