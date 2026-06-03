"""Sun and golden-hour math via astral. Needs no API key, so it works in demo mode too."""

from datetime import date as Date
from zoneinfo import ZoneInfo

from astral import Observer, SunDirection
from astral.sun import golden_hour, sun

# Approximate timezone by base city; defaults to America/Los_Angeles (this is a film tool).
_CITY_TZ = {
    "los angeles": "America/Los_Angeles",
    "malibu": "America/Los_Angeles",
    "san pedro": "America/Los_Angeles",
    "long beach": "America/Los_Angeles",
    "santa monica": "America/Los_Angeles",
    "rancho palos verdes": "America/Los_Angeles",
    "new york": "America/New_York",
    "atlanta": "America/New_York",
    "new orleans": "America/Chicago",
    "vancouver": "America/Vancouver",
    "london": "Europe/London",
}


def tz_for(city: str) -> str:
    key = (city or "").lower()
    for name, tz in _CITY_TZ.items():
        if name in key:
            return tz
    return "America/Los_Angeles"


def _fmt(dt) -> str:
    return dt.strftime("%-I:%M %p")


def golden_windows(lat: float, lng: float, on: Date, tz: str) -> dict:
    """Real morning/evening golden-hour windows plus a sunrise/sunset note."""
    out = {
        "sunrise": "",
        "sunset": "",
        "golden_hour_morning_end": "",
        "golden_hour_evening_start": "",
        "golden_hour_am": "",
        "golden_hour_pm": "",
        "sun_note": "",
    }
    try:
        obs = Observer(latitude=lat, longitude=lng)
        zone = ZoneInfo(tz)
        s = sun(obs, date=on, tzinfo=zone)
        gh_am = golden_hour(obs, on, SunDirection.RISING, tzinfo=zone)
        gh_pm = golden_hour(obs, on, SunDirection.SETTING, tzinfo=zone)
        out["sunrise"] = _fmt(s["sunrise"])
        out["sunset"] = _fmt(s["sunset"])
        out["golden_hour_morning_end"] = _fmt(gh_am[1])
        out["golden_hour_evening_start"] = _fmt(gh_pm[0])
        out["golden_hour_am"] = f"{_fmt(gh_am[0])}-{_fmt(gh_am[1])}"
        out["golden_hour_pm"] = f"{_fmt(gh_pm[0])}-{_fmt(gh_pm[1])}"
        out["sun_note"] = (
            f"Sunrise {_fmt(s['sunrise'])}, sunset {_fmt(s['sunset'])} "
            f"({tz.split('/')[-1].replace('_', ' ')} time)."
        )
    except Exception as exc:
        print(f"[recce] golden-hour calc failed: {exc}")
    return out
