#!/usr/bin/env python3
"""Ingest open film-location / permit datasets into Recce's normalized JSON schema.

Examples:
  python scripts/data_ingest/ingest_open_locations.py nyc-permits --limit 5000 --out backend/app/data/locations.json
  python scripts/data_ingest/ingest_open_locations.py sf-filming --out backend/app/data/locations.json
  python scripts/data_ingest/ingest_open_locations.py csv path/to/locations.csv --out backend/app/data/locations.json
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

NYC_FILM_PERMITS = "https://data.cityofnewyork.us/resource/tg4x-b46p.json"
SF_FILMING_LOCATIONS = "https://data.sfgov.org/resource/yitu-d5am.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["nyc-permits", "sf-filming", "csv"])
    parser.add_argument("path", nargs="?", help="CSV path when source=csv")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--out", default="backend/app/data/locations.json")
    args = parser.parse_args()

    if args.source == "nyc-permits":
        records = ingest_nyc(args.limit)
    elif args.source == "sf-filming":
        records = ingest_sf(args.limit)
    else:
        if not args.path:
            raise SystemExit("source=csv requires a CSV path")
        records = ingest_csv(Path(args.path))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(records)} records to {out}")


def fetch_json(url: str, params: dict[str, str | int]) -> list[dict]:
    full_url = f"{url}?{urlencode(params)}"
    with urlopen(full_url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def ingest_nyc(limit: int) -> list[dict]:
    rows = fetch_json(NYC_FILM_PERMITS, {"$limit": limit})
    records: dict[str, dict] = {}
    for row in rows:
        borough = row.get("borough", "")
        category = row.get("eventtype") or row.get("event_type") or "film permit"
        parking = row.get("parkingheld") or row.get("parking_held") or ""
        streets = row.get("streetclosure") or row.get("street_closure") or ""
        name = row.get("eventid") or row.get("event_id") or f"{category} {borough}".strip()
        address = ", ".join(part for part in [parking, borough, "NY"] if part)
        key = stable_id("nyc_open_data_film_permits", name, address)
        restrictions = [item for item in [parking, streets] if item]
        records[key] = normalize(
            key,
            name=f"NYC Film Permit {name}",
            address=address,
            categories=[category, borough, "film permit"],
            permit_required=True,
            permit_status="historical NYC film permit record; verify current status with MOME",
            contact="NYC Mayor's Office of Media and Entertainment",
            restrictions=restrictions,
            source="nyc_open_data_film_permits",
        )
    return list(records.values())


def ingest_sf(limit: int) -> list[dict]:
    rows = fetch_json(SF_FILMING_LOCATIONS, {"$limit": limit})
    records: dict[str, dict] = {}
    for row in rows:
        location = row.get("locations") or row.get("location") or ""
        if not location:
            continue
        title = row.get("title", "Untitled production")
        facts = row.get("fun_facts", "")
        key = stable_id("sf_filming_locations", title, location)
        records[key] = normalize(
            key,
            name=location,
            address=f"{location}, San Francisco, CA",
            categories=["known filming location", title],
            permit_required=True,
            permit_status="known San Francisco filming location; verify current permit needs with Film SF",
            contact="Film SF",
            restrictions=[facts] if facts else [],
            source="sf_filming_locations",
        )
    return list(records.values())


def ingest_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    records = []
    for row in rows:
        name = row.get("name") or row.get("Name") or row.get("location") or row.get("Location")
        if not name:
            continue
        address = row.get("address") or row.get("Address") or ""
        source = row.get("source") or row.get("Source") or path.stem
        key = stable_id(source, name, address)
        records.append(
            normalize(
                key,
                name=name,
                address=address,
                lat=parse_float(row.get("lat") or row.get("latitude")),
                lng=parse_float(row.get("lng") or row.get("lon") or row.get("longitude")),
                categories=split_list(row.get("categories") or row.get("category")),
                permit_required=parse_bool(row.get("permit_required")),
                permit_status=row.get("permit_status", ""),
                contact=row.get("contact", ""),
                restrictions=split_list(row.get("restrictions")),
                source=source,
            )
        )
    return records


def normalize(
    id_: str,
    name: str,
    address: str = "",
    lat: float | None = None,
    lng: float | None = None,
    categories: list[str] | None = None,
    permit_required: bool = False,
    permit_status: str = "",
    contact: str = "",
    restrictions: list[str] | None = None,
    source: str = "open_data",
) -> dict:
    return {
        "id": id_,
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "categories": [item for item in (categories or []) if item],
        "permit_required": permit_required,
        "permit_status": permit_status,
        "contact": contact,
        "restrictions": [item for item in (restrictions or []) if item],
        "source": source,
    }


def stable_id(source: str, name: str, address: str) -> str:
    return hashlib.sha1(f"{source}:{name}:{address}".encode()).hexdigest()[:16]


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace("|", ";").split(";") if part.strip()]


def parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


if __name__ == "__main__":
    main()
