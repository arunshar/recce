"""Optional OSRM routing client."""

from dataclasses import dataclass
from typing import Optional

import httpx

from .config import get_settings
from .schemas import Candidate

settings = get_settings()


@dataclass
class OsrmTrip:
    candidate_order: list[int]
    leg_minutes: list[float]
    total_distance_km: float


def _coords(base: tuple[float, float], candidates: list[Candidate]) -> str:
    points = [base] + [(c.lat, c.lng) for c in candidates]
    return ";".join(f"{lng},{lat}" for lat, lng in points)


def table_minutes(base: tuple[float, float], candidates: list[Candidate]) -> Optional[list[list[float]]]:
    """Fetch an OSRM duration matrix in minutes."""
    if not settings.has_osrm:
        return None
    try:
        r = httpx.get(
            f"{settings.osrm_base_url}/table/v1/driving/{_coords(base, candidates)}",
            params={"annotations": "duration"},
            timeout=12,
        )
        r.raise_for_status()
        durations = r.json().get("durations")
        if not durations:
            return None
        return [[round((cell or 0) / 60, 1) for cell in row] for row in durations]
    except Exception as exc:
        print(f"[recce] OSRM table failed: {exc}")
    return None


def optimize_trip(base: tuple[float, float], candidates: list[Candidate]) -> Optional[OsrmTrip]:
    """Use OSRM's Trip service to order candidates, with base fixed first."""
    if not settings.has_osrm or not candidates:
        return None
    try:
        r = httpx.get(
            f"{settings.osrm_base_url}/trip/v1/driving/{_coords(base, candidates)}",
            params={
                "source": "first",
                "roundtrip": "false",
                "overview": "false",
                "steps": "false",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        waypoints = data.get("waypoints") or []
        trips = data.get("trips") or []
        if len(waypoints) != len(candidates) + 1 or not trips:
            return None

        ordered_input_indexes = sorted(range(len(waypoints)), key=lambda i: waypoints[i].get("waypoint_index", i))
        if ordered_input_indexes and ordered_input_indexes[0] != 0:
            # `source=first` should keep base first; if OSRM disagrees, avoid a bad handoff.
            return None
        candidate_order = [i - 1 for i in ordered_input_indexes if i > 0]
        legs = trips[0].get("legs") or []
        leg_minutes = [round((leg.get("duration") or 0) / 60, 1) for leg in legs[: len(candidate_order)]]
        if len(leg_minutes) < len(candidate_order):
            return None
        total_distance_km = round((trips[0].get("distance") or 0) / 1000, 1)
        return OsrmTrip(candidate_order=candidate_order, leg_minutes=leg_minutes, total_distance_km=total_distance_km)
    except Exception as exc:
        print(f"[recce] OSRM trip failed: {exc}")
    return None
