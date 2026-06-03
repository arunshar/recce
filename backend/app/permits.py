"""Open location and permit-data enrichment."""

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from .config import get_settings
from .schemas import Candidate, LocationRecord, SceneBrief

settings = get_settings()
DATA_DIR = Path(__file__).parent / "data"


def _record_id(source: str, name: str, address: str = "") -> str:
    return hashlib.sha1(f"{source}:{name}:{address}".encode()).hexdigest()[:12]


def _seed_records() -> list[LocationRecord]:
    """Small demo corpus that exercises permit filtering before external ingestion."""
    return [
        LocationRecord(
            id="demo-santa-monica-pier",
            name="Santa Monica Pier",
            address="200 Santa Monica Pier, Santa Monica, CA",
            lat=34.0101,
            lng=-118.4962,
            categories=["pier", "coastal", "public landmark", "boardwalk"],
            permit_required=True,
            permit_status="city film permit required for commercial filming",
            contact="Santa Monica Film Office",
            restrictions=["crowd control", "parking holds", "public access"],
            source="demo_open_locations",
        ),
        LocationRecord(
            id="demo-griffith-observatory",
            name="Griffith Observatory",
            address="2800 E Observatory Rd, Los Angeles, CA",
            lat=34.1184,
            lng=-118.3004,
            categories=["observatory", "historic", "city overlook", "public landmark"],
            permit_required=True,
            permit_status="park and city permit review required",
            contact="FilmLA",
            restrictions=["night access", "public hours", "parking limits"],
            source="demo_open_locations",
        ),
        LocationRecord(
            id="demo-angelino-heights",
            name="Angelino Heights Victorian District",
            address="Angelino Heights, Los Angeles, CA",
            lat=34.0704,
            lng=-118.2547,
            categories=["residential street", "historic homes", "period exterior"],
            permit_required=True,
            permit_status="neighborhood notification and parking plan required",
            contact="FilmLA",
            restrictions=["resident notification", "truck parking", "street closure review"],
            source="demo_open_locations",
        ),
    ]


@lru_cache
def load_records() -> list[LocationRecord]:
    """Load normalized records from RECCE_LOCATION_DATA or backend/app/data/locations.json."""
    candidates: list[Path] = []
    if settings.location_data_path:
        candidates.append(Path(settings.location_data_path))
    candidates.append(DATA_DIR / "locations.json")

    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records = [LocationRecord(**item) for item in data]
            return records + _seed_records()
        except Exception as exc:
            print(f"[recce] location data load failed for {path}: {exc}")
    return _seed_records()


def merge_open_locations(
    brief: SceneBrief,
    center: tuple[float, float],
    existing: list[Candidate],
    max_results: int,
) -> list[Candidate]:
    """Merge matching normalized records into the candidate pool and enrich existing rows."""
    enriched = [enrich_candidate(c) for c in existing]
    seen = {_fingerprint(c.name, c.address) for c in enriched}

    scored = sorted(
        ((record, _score_record(brief, record)) for record in load_records()),
        key=lambda item: item[1],
        reverse=True,
    )
    added = 0
    for record, score in scored:
        if score <= 0:
            continue
        if record.lat is None or record.lng is None:
            continue
        fp = _fingerprint(record.name, record.address)
        if fp in seen:
            continue
        enriched.append(_candidate_from_record(brief, record, center, score))
        seen.add(fp)
        added += 1
        if added >= min(4, max_results):
            break
    enriched.sort(key=lambda c: (c.match_score, int(c.permit_required)), reverse=True)
    return enriched[:max_results]


def enrich_candidate(candidate: Candidate) -> Candidate:
    """Attach permit metadata from matching records or lightweight heuristics."""
    best: tuple[LocationRecord, int] | None = None
    for record in load_records():
        score = _name_address_overlap(candidate.name, candidate.address, record)
        if score > 0 and (best is None or score > best[1]):
            best = (record, score)
    if best is not None:
        record = best[0]
        candidate.permit_required = record.permit_required
        candidate.permit_status = record.permit_status
        candidate.permit_contact = record.contact
        candidate.permit_restrictions = record.restrictions
        candidate.source = candidate.source or record.source
        if record.source not in candidate.rights_notes:
            candidate.rights_notes.append(f"Metadata source: {record.source}")
        return candidate

    types_text = " ".join(candidate.types).lower()
    if any(token in types_text for token in ("park", "tourist_attraction", "museum", "stadium")):
        candidate.permit_required = True
        candidate.permit_status = "permit likely required; confirm with local film office"
        candidate.permit_restrictions = ["public access", "posted rules"]
    return candidate


def permit_note(candidate: Candidate) -> str:
    bits: list[str] = []
    if candidate.permit_required:
        bits.append(candidate.permit_status or "Film permit likely required.")
    elif candidate.permit_status:
        bits.append(candidate.permit_status)
    if candidate.permit_contact:
        bits.append(f"Contact: {candidate.permit_contact}.")
    if candidate.permit_restrictions:
        bits.append(f"Restrictions: {', '.join(candidate.permit_restrictions[:4])}.")
    return " ".join(bits)


def _candidate_from_record(
    brief: SceneBrief,
    record: LocationRecord,
    center: tuple[float, float],
    score: int,
) -> Candidate:
    return Candidate(
        id=_record_id(f"{brief.scene_id}:{record.source}", record.name, record.address),
        scene_id=brief.scene_id,
        name=record.name,
        address=record.address,
        lat=record.lat if record.lat is not None else center[0],
        lng=record.lng if record.lng is not None else center[1],
        match_score=min(88, 58 + score * 6),
        rationale=f"Open location data match for {brief.location_type or brief.slugline}.",
        flags=record.restrictions[:3],
        types=record.categories,
        source=record.source,
        permit_required=record.permit_required,
        permit_status=record.permit_status,
        permit_contact=record.contact,
        permit_restrictions=record.restrictions,
        rights_notes=[f"Metadata source: {record.source}"],
    )


def _score_record(brief: SceneBrief, record: LocationRecord) -> int:
    terms = _brief_terms(brief)
    haystack = " ".join([record.name, record.address, *record.categories, *record.restrictions]).lower()
    return sum(1 for term in terms if term in haystack)


def _brief_terms(brief: SceneBrief) -> set[str]:
    text = " ".join(
        [
            brief.location_type,
            brief.slugline,
            *brief.key_visual_elements,
            *brief.mood,
            *brief.search_queries,
        ]
    ).lower()
    terms = set(re.findall(r"[a-z][a-z0-9'-]{2,}", text))
    return {term for term in terms if term not in {"near", "film", "location", "city", "day", "night"}}


def _name_address_overlap(name: str, address: str, record: LocationRecord) -> int:
    left = set(re.findall(r"[a-z0-9]{3,}", f"{name} {address}".lower()))
    right = set(re.findall(r"[a-z0-9]{3,}", f"{record.name} {record.address}".lower()))
    return len(left & right)


def _fingerprint(name: str, address: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", f"{name} {address}".lower()).strip()
    return cleaned
