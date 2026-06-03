"""Scout-day route optimizer: nearest-neighbor seed plus 2-opt improvement over the
shortlist, starting and counting from the production base. This is Recce's own routing
logic (no external routing API required)."""

import math
from datetime import datetime, timedelta

from . import osrm
from .schemas import Candidate, RouteResult, RouteStop

AVG_KMH = 38.0   # rough city driving speed for ETA estimates
DWELL_MIN = 30   # minutes spent scouting each location
START_HOUR = 9   # scout day begins at 9:00 local


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    radius = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def _tour_distance(points: list[tuple[float, float]], order: list[int]) -> float:
    return sum(haversine_km(points[order[i]], points[order[i + 1]]) for i in range(len(order) - 1))


def _nearest_neighbor(points: list[tuple[float, float]], start: int = 0) -> list[int]:
    unvisited = set(range(len(points))) - {start}
    order = [start]
    while unvisited:
        last = order[-1]
        nxt = min(unvisited, key=lambda j: haversine_km(points[last], points[j]))
        order.append(nxt)
        unvisited.remove(nxt)
    return order


def _two_opt(points: list[tuple[float, float]], order: list[int]) -> list[int]:
    best = order
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 1):           # keep index 0 (base) fixed at the start
            for k in range(i + 1, len(best)):
                candidate = best[:i] + best[i : k + 1][::-1] + best[k + 1 :]
                if _tour_distance(points, candidate) < _tour_distance(points, best) - 1e-9:
                    best = candidate
                    improved = True
    return best


def _build_result(
    base: tuple[float, float],
    base_name: str,
    candidates: list[Candidate],
    candidate_order: list[int],
    method: str,
    leg_minutes: list[float] | None = None,
    total_distance_km: float | None = None,
) -> RouteResult:
    clock = datetime(2026, 1, 1, START_HOUR, 0)     # date is irrelevant; we only render times
    stops: list[RouteStop] = []
    total_km = 0.0
    prev = base

    for step, cand_idx in enumerate(candidate_order, start=1):
        cand = candidates[cand_idx]
        point = (cand.lat, cand.lng)
        leg_km = haversine_km(prev, point)
        drive_min = leg_minutes[step - 1] if leg_minutes and step - 1 < len(leg_minutes) else leg_km / AVG_KMH * 60
        total_km += leg_km
        clock += timedelta(minutes=drive_min)
        window_bits = []
        if cand.permit_required:
            window_bits.append("permit review")
        if cand.permit_restrictions:
            window_bits.append(cand.permit_restrictions[0])
        stops.append(
            RouteStop(
                order=step,
                candidate_id=cand.id,
                name=cand.name,
                lat=cand.lat,
                lng=cand.lng,
                drive_minutes_from_prev=round(drive_min, 1),
                arrive_local=clock.strftime("%-I:%M %p"),
                window_note=", ".join(window_bits),
            )
        )
        clock += timedelta(minutes=DWELL_MIN)
        prev = point

    total_min = sum(s.drive_minutes_from_prev for s in stops) + DWELL_MIN * len(stops)
    return RouteResult(
        base_name=base_name,
        base_lat=base[0],
        base_lng=base[1],
        stops=stops,
        total_distance_km=round(total_distance_km if total_distance_km is not None else total_km, 1),
        total_drive_minutes=round(total_min, 1),
        route_method=method,
    )


def optimize(base: tuple[float, float], base_name: str, candidates: list[Candidate]) -> RouteResult:
    if not candidates:
        return RouteResult(base_name=base_name, base_lat=base[0], base_lng=base[1])

    osrm_trip = osrm.optimize_trip(base, candidates)
    if osrm_trip is not None:
        return _build_result(
            base,
            base_name,
            candidates,
            osrm_trip.candidate_order,
            "osrm_trip",
            osrm_trip.leg_minutes,
            osrm_trip.total_distance_km,
        )

    points = [base] + [(c.lat, c.lng) for c in candidates]
    order = _two_opt(points, _nearest_neighbor(points, start=0))
    return _build_result(base, base_name, candidates, [idx - 1 for idx in order[1:]], "haversine_2opt")
