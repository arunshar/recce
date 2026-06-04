import time
from pathlib import Path

import pytest

from app import gemini, packet as packet_mod, places, routing
from app.schemas import Candidate, SceneBrief

DEMO_DIR = Path(__file__).resolve().parents[1] / "app" / "demo_data"


@pytest.mark.e2e
@pytest.mark.smoke
def test_full_user_workflow_from_script_to_packet(client):
    script = """INT. COFFEE SHOP - DAY

MAYA sits alone under flickering neon.

EXT. COASTAL PIER - DUSK

MAYA
This is where we leave it.
"""
    segments = client.post("/api/script/segments", json={"script_text": script})
    assert segments.status_code == 200
    assert len(segments.json()["scenes"]) == 2

    analyze = client.post("/api/analyze", json={"scene_text": script, "base_city": "Los Angeles, CA"})
    assert analyze.status_code == 200
    briefs = analyze.json()["briefs"]
    assert len(briefs) == 2

    candidates = client.post(
        "/api/candidates",
        json={"briefs": briefs, "base_city": "Los Angeles, CA", "max_per_brief": 3},
    )
    assert candidates.status_code == 200
    cands = candidates.json()["candidates"]
    assert cands
    assert all(c["street_view_url"] for c in cands)

    shortlist = cands[: min(3, len(cands))]
    route = client.post("/api/route", json={"candidates": shortlist, "base_city": "Los Angeles, CA"})
    assert route.status_code == 200
    assert len(route.json()["stops"]) == len(shortlist)

    packet = client.post(
        "/api/packet",
        json={
            "candidates": shortlist,
            "briefs": briefs,
            "base_city": "Los Angeles, CA",
            "shoot_date": "2026-06-13",
            "production_title": "Workflow Test",
        },
    )
    assert packet.status_code == 200
    body = packet.json()
    assert body["production_title"] == "Workflow Test"
    assert len(body["locations"]) == len(shortlist)
    assert body["schedule"][0]["stops"]
    assert all(loc["weather"]["summary"] for loc in body["locations"])
    assert all(loc["concept_image_url"] for loc in body["locations"])


@pytest.mark.regression
def test_demo_scene_fallback_golden_candidates_are_stable():
    scene_text = (DEMO_DIR / "sample_screenplay.txt").read_text(encoding="utf-8")
    briefs = gemini.extract_scene_briefs(scene_text, "Los Angeles, CA")
    assert [brief.scene_id for brief in briefs] == ["S1", "S2", "S3"]
    assert briefs[0].slugline == "INT. SALTWATER DINER - DAWN"

    center = places.geocode("Los Angeles, CA")
    first_scene_candidates = places.search_candidates(briefs[0], center, 4)
    names = [cand.name for cand in first_scene_candidates]
    assert "Ocean View Diner" in names
    assert "Santa Monica Pier" in names


@pytest.mark.regression
def test_packet_schedule_rolls_over_after_four_locations():
    b = SceneBrief(scene_id="S1", slugline="EXT. TEST - DAY", location_type="pier")
    candidates = [
        Candidate(id=f"c{i}", scene_id="S1", name=f"Location {i}", lat=34.0 + i * 0.01, lng=-118.2)
        for i in range(5)
    ]
    packet = packet_mod.build_packet(candidates, [b], "Los Angeles, CA", "2026-06-13", "Schedule Test")
    assert len(packet.schedule) == 2
    assert len(packet.schedule[0].stops) == 4
    assert len(packet.schedule[1].stops) == 1
    assert packet.schedule[1].date == "2026-06-14"


@pytest.mark.performance
def test_demo_pipeline_performance_budget(client):
    started = time.perf_counter()
    briefs = client.post("/api/analyze", json={"scene_text": "x"}).json()["briefs"]
    cands = client.post("/api/candidates", json={"briefs": briefs, "max_per_brief": 4}).json()["candidates"]
    shortlist = cands[:3]
    client.post("/api/route", json={"candidates": shortlist}).raise_for_status()
    client.post("/api/packet", json={"candidates": shortlist, "briefs": briefs}).raise_for_status()
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0


@pytest.mark.performance
def test_route_optimizer_handles_medium_shortlist_quickly(monkeypatch):
    monkeypatch.setattr(routing.osrm, "optimize_trip", lambda *_: None)
    candidates = [
        Candidate(id=f"c{i}", name=f"C{i}", lat=34.0 + (i % 5) * 0.01, lng=-118.3 + (i // 5) * 0.01)
        for i in range(25)
    ]
    started = time.perf_counter()
    result = routing.optimize((34.05, -118.24), "LA", candidates)
    elapsed = time.perf_counter() - started
    assert len(result.stops) == 25
    assert elapsed < 1.0


@pytest.mark.security
def test_security_headers_and_secret_hygiene(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert "GEMINI_API_KEY" not in health.text
    assert "GOOGLE_MAPS_API_KEY" not in health.text

    payload = "<script>alert('x')</script>"
    image = client.get("/api/streetview", params={"lat": 34.0, "lng": -118.2, "name": payload})
    assert image.status_code == 200
    assert payload not in image.text
    assert "&lt;script&gt;" in image.text
