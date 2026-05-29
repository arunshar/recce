"""Smoke tests for the Recce pipeline in demo mode (no API keys required)."""
import os

from starlette.testclient import TestClient

# Force demo mode for tests, even if local .env contains API keys.
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_MAPS_API_KEY"] = ""
from app.main import app
from app.routing import _nearest_neighbor, _tour_distance, _two_opt

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_returns_briefs():
    r = client.post("/api/analyze", json={"scene_text": "INT. ROOM - DAY", "base_city": "Los Angeles, CA"})
    assert r.status_code == 200
    briefs = r.json()["briefs"]
    assert len(briefs) >= 1
    assert all(b["scene_id"] for b in briefs)


def test_full_pipeline_demo():
    briefs = client.post("/api/analyze", json={"scene_text": "x"}).json()["briefs"]
    candidates = client.post("/api/candidates", json={"briefs": briefs}).json()["candidates"]
    assert len(candidates) >= 3

    shortlist = candidates[:3]
    route = client.post("/api/route", json={"candidates": shortlist}).json()
    assert len(route["stops"]) == len(shortlist)
    assert route["total_distance_km"] >= 0
    assert [s["order"] for s in route["stops"]] == list(range(1, len(shortlist) + 1))

    packet = client.post(
        "/api/packet",
        json={"candidates": shortlist, "briefs": briefs, "shoot_date": "2026-06-13"},
    ).json()
    assert len(packet["locations"]) == len(shortlist)
    # Golden-hour math runs even in demo mode.
    assert packet["locations"][0]["golden_hour_pm"]


def test_streetview_placeholder():
    r = client.get("/api/streetview", params={"lat": 34.0, "lng": -118.2, "name": "Test"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_two_opt_never_worse_than_nearest_neighbor():
    pts = [(34.05, -118.24), (33.77, -118.19), (33.74, -118.41), (34.04, -118.25), (34.01, -118.49)]
    nn = _nearest_neighbor(pts, 0)
    opt = _two_opt(pts, nn)
    assert _tour_distance(pts, opt) <= _tour_distance(pts, nn) + 1e-9
    assert opt[0] == 0  # base stays first
