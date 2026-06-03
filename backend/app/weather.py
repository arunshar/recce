"""Weather summaries for shoot-day packets."""

from datetime import date as Date

import httpx

from .config import get_settings
from .schemas import WeatherSummary

settings = get_settings()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"


def forecast(lat: float, lng: float, on: Date) -> WeatherSummary:
    """Return a weather summary for a location/date, with demo fallback."""
    provider = settings.weather_provider
    if provider == "open-meteo":
        live = _open_meteo(lat, lng, on)
        if live:
            return live
    if provider == "openweather" and settings.openweather_api_key:
        live = _openweather(lat, lng, on)
        if live:
            return live
    return _demo_weather(lat, lng, on)


def _open_meteo(lat: float, lng: float, on: Date) -> WeatherSummary | None:
    try:
        r = httpx.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lng,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "timezone": "auto",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "start_date": on.isoformat(),
                "end_date": on.isoformat(),
            },
            timeout=10,
        )
        r.raise_for_status()
        daily = r.json().get("daily") or {}
        hi = _first(daily.get("temperature_2m_max"))
        lo = _first(daily.get("temperature_2m_min"))
        precip = _first(daily.get("precipitation_probability_max"))
        wind = _first(daily.get("wind_speed_10m_max"))
        summary = _summary(hi, lo, precip, wind)
        return WeatherSummary(
            summary=summary,
            temperature_f=round((hi + lo) / 2, 1) if hi is not None and lo is not None else hi,
            precipitation_probability=precip,
            wind_mph=wind,
            source="open-meteo",
        )
    except Exception as exc:
        print(f"[recce] Open-Meteo forecast failed: {exc}")
    return None


def _openweather(lat: float, lng: float, on: Date) -> WeatherSummary | None:
    try:
        r = httpx.get(
            OPENWEATHER_URL,
            params={
                "lat": lat,
                "lon": lng,
                "appid": settings.openweather_api_key,
                "units": "imperial",
            },
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("list") or []
        same_day = [item for item in items if str(item.get("dt_txt", "")).startswith(on.isoformat())]
        if not same_day:
            return None
        temps = [(item.get("main") or {}).get("temp") for item in same_day]
        winds = [(item.get("wind") or {}).get("speed") for item in same_day]
        pops = [item.get("pop") for item in same_day]
        temp = _avg([v for v in temps if isinstance(v, (int, float))])
        wind = max([v for v in winds if isinstance(v, (int, float))], default=None)
        precip = max([v * 100 for v in pops if isinstance(v, (int, float))], default=None)
        return WeatherSummary(
            summary=_summary(temp, None, precip, wind),
            temperature_f=round(temp, 1) if temp is not None else None,
            precipitation_probability=round(precip, 1) if precip is not None else None,
            wind_mph=round(wind, 1) if wind is not None else None,
            source="openweather",
        )
    except Exception as exc:
        print(f"[recce] OpenWeather forecast failed: {exc}")
    return None


def _demo_weather(lat: float, lng: float, on: Date) -> WeatherSummary:
    seed = int(abs(lat * 10) + abs(lng * 10) + on.toordinal()) % 9
    temp = 66 + seed
    precip = [0, 5, 10, 15, 20, 30, 0, 8, 12][seed]
    wind = 5 + seed * 0.8
    return WeatherSummary(
        summary=_summary(temp, None, precip, wind),
        temperature_f=round(temp, 1),
        precipitation_probability=precip,
        wind_mph=round(wind, 1),
        source="demo",
    )


def _summary(hi: float | None, lo: float | None, precip: float | None, wind: float | None) -> str:
    bits: list[str] = []
    if hi is not None and lo is not None:
        bits.append(f"{round(lo)}-{round(hi)} F")
    elif hi is not None:
        bits.append(f"{round(hi)} F")
    if precip is not None:
        bits.append(f"{round(precip)}% precip")
    if wind is not None:
        bits.append(f"{round(wind)} mph wind")
    return ", ".join(bits) if bits else "Forecast unavailable; confirm during tech scout."


def _first(values):
    if isinstance(values, list) and values:
        value = values[0]
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
