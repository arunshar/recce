"""Runtime configuration and key detection.

Recce reads keys from the environment (loaded from a .env file if present).
When the Gemini key is missing, the app runs in demo mode and serves bundled
sample data so the full flow works with no keys at all.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root or the backend directory, whichever exists.
_HERE = Path(__file__).resolve()
for _candidate in (_HERE.parents[2] / ".env", _HERE.parents[1] / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate, override=False)


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.gemini_pro_model = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro").strip()
        self.image_model = os.getenv("RECCE_IMAGE_MODEL", "imagen-4.0-fast-generate-001").strip()
        self.image_fallback_model = os.getenv("RECCE_IMAGE_FALLBACK_MODEL", "gemini-2.5-flash-image").strip()
        self.default_base_city = os.getenv("RECCE_BASE_CITY", "Los Angeles, CA").strip()
        self.osrm_base_url = os.getenv("RECCE_OSRM_URL", "").strip().rstrip("/")
        self.weather_provider = os.getenv("RECCE_WEATHER_PROVIDER", "demo").strip().lower()
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        self.location_data_path = os.getenv("RECCE_LOCATION_DATA", "").strip()

        origins = os.getenv("RECCE_CORS_ORIGINS", "*").strip()
        self.cors_origins = ["*"] if origins in ("", "*") else [o.strip() for o in origins.split(",")]

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_maps(self) -> bool:
        return bool(self.maps_api_key)

    @property
    def has_osrm(self) -> bool:
        return bool(self.osrm_base_url)

    @property
    def demo_mode(self) -> bool:
        # The core pipeline depends on Gemini; without it we serve cached demo data.
        return not self.has_gemini


@lru_cache
def get_settings() -> Settings:
    return Settings()
