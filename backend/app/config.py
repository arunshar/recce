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
        self.default_base_city = os.getenv("RECCE_BASE_CITY", "Los Angeles, CA").strip()

        origins = os.getenv("RECCE_CORS_ORIGINS", "*").strip()
        self.cors_origins = ["*"] if origins in ("", "*") else [o.strip() for o in origins.split(",")]

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_maps(self) -> bool:
        return bool(self.maps_api_key)

    @property
    def demo_mode(self) -> bool:
        # The core pipeline depends on Gemini; without it we serve cached demo data.
        return not self.has_gemini


@lru_cache
def get_settings() -> Settings:
    return Settings()
