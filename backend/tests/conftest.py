"""Shared test fixtures.

All tests run in deterministic demo mode unless a test explicitly monkeypatches
module settings. This prevents local API keys from changing CI results.
"""

import os

import pytest
from starlette.testclient import TestClient

os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_MAPS_API_KEY"] = ""
os.environ["RECCE_WEATHER_PROVIDER"] = "demo"
os.environ["RECCE_OSRM_URL"] = ""

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
