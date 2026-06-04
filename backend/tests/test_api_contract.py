from datetime import date

import pytest

from app import osrm, weather
from app.schemas import Candidate, Packet, RouteResult, SceneBrief

pytestmark = [pytest.mark.integration, pytest.mark.contract]


def test_health_contract_does_not_leak_secret_values(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {
        "status",
        "demo_mode",
        "has_gemini",
        "has_maps",
        "has_osrm",
        "gemini_model",
        "weather_provider",
    }
    assert body["status"] == "ok"
    assert "api_key" not in str(body).lower()


def test_openapi_exposes_workflow_endpoints(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    for path in [
        "/api/health",
        "/api/analyze",
        "/api/script/segments",
        "/api/candidates",
        "/api/route",
        "/api/packet",
        "/api/moodboard",
    ]:
        assert path in paths


def test_analyze_candidates_route_packet_validate_against_models(client):
    analyze = client.post(
        "/api/analyze",
        json={
            "scene_text": "EXT. COASTAL PIER - DUSK\n\nA warm tense goodbye by the rides.",
            "base_city": "Los Angeles, CA",
        },
    )
    assert analyze.status_code == 200
    briefs = [SceneBrief(**item) for item in analyze.json()["briefs"]]
    assert briefs

    candidates = client.post("/api/candidates", json={"briefs": [b.model_dump() for b in briefs]}).json()["candidates"]
    assert candidates

    route = client.post("/api/route", json={"candidates": candidates[:2]}).json()
    RouteResult(**route)
    assert route["route_method"] in {"haversine_2opt", "osrm_trip"}

    packet = client.post(
        "/api/packet",
        json={"candidates": candidates[:2], "briefs": [b.model_dump() for b in briefs], "shoot_date": "2026-06-13"},
    ).json()
    parsed = Packet(**packet)
    assert len(parsed.locations) == min(2, len(candidates))
    assert parsed.schedule[0].stops


def test_invalid_payloads_return_422(client):
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/candidates", json={"briefs": "not-a-list"}).status_code == 422
    assert client.post("/api/route", json={"candidates": [{"name": "missing coords"}]}).status_code == 422


def test_media_endpoints_return_images(client):
    street = client.get("/api/streetview", params={"lat": 34.0, "lng": -118.2, "name": "Test"})
    assert street.status_code == 200
    assert street.headers["content-type"].startswith("image/")

    photo = client.get("/api/placephoto", params={"ref": "", "name": "Test"})
    assert photo.status_code == 200
    assert photo.headers["content-type"].startswith("image/")

    brief = SceneBrief(scene_id="S1", slugline="EXT. TEST - DAY", location_type="test location")
    mood = client.post("/api/moodboard", json=brief.model_dump())
    assert mood.status_code == 200
    assert mood.headers["content-type"].startswith("image/")


def test_osrm_table_and_trip_clients(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, params, timeout):
        assert "driving" in url
        if "/table/" in url:
            return Response({"durations": [[0, 120], [130, 0]]})
        return Response(
            {
                "waypoints": [{"waypoint_index": 0}, {"waypoint_index": 2}, {"waypoint_index": 1}],
                "trips": [{"distance": 3456, "legs": [{"duration": 90}, {"duration": 180}]}],
            }
        )

    monkeypatch.setattr(osrm.settings, "osrm_base_url", "http://osrm.test")
    monkeypatch.setattr(osrm.httpx, "get", fake_get)
    candidates = [
        {"id": "a", "name": "A", "lat": 34.0, "lng": -118.2},
        {"id": "b", "name": "B", "lat": 34.1, "lng": -118.3},
    ]
    parsed = [Candidate(**item) for item in candidates]
    assert osrm.table_minutes((34.05, -118.24), parsed) == [[0.0, 2.0], [2.2, 0.0]]
    trip = osrm.optimize_trip((34.05, -118.24), parsed)
    assert trip is not None
    assert trip.candidate_order == [1, 0]
    assert trip.leg_minutes == [1.5, 3.0]


def test_weather_open_meteo_client(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "daily": {
                    "temperature_2m_max": [72],
                    "temperature_2m_min": [61],
                    "precipitation_probability_max": [20],
                    "wind_speed_10m_max": [9],
                }
            }

    monkeypatch.setattr(weather.settings, "weather_provider", "open-meteo")
    monkeypatch.setattr(weather.httpx, "get", lambda *_, **__: Response())
    forecast = weather.forecast(34.0, -118.2, date(2026, 6, 13))
    assert forecast.source == "open-meteo"
    assert forecast.temperature_f == 66.5
    assert forecast.precipitation_probability == 20
