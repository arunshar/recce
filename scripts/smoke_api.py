#!/usr/bin/env python3
"""Run Recce API smoke checks against a running service.

Usage:
  python scripts/smoke_api.py --base-url http://127.0.0.1:8000
  python scripts/smoke_api.py --base-url https://recce.example.com
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        health = get_json(base_url, "/api/health", args.timeout)
        assert health["status"] == "ok", health

        scene = get_json(base_url, "/api/demo/scene", args.timeout)["scene_text"]
        segments = post_json(base_url, "/api/script/segments", {"script_text": scene}, args.timeout)
        assert "scenes" in segments

        analyzed = post_json(
            base_url,
            "/api/analyze",
            {"scene_text": scene or "INT. ROOM - DAY", "base_city": "Los Angeles, CA"},
            args.timeout,
        )
        briefs = analyzed["briefs"]
        assert briefs, analyzed

        candidates = post_json(
            base_url,
            "/api/candidates",
            {"briefs": briefs, "base_city": "Los Angeles, CA", "max_per_brief": 3},
            args.timeout,
        )["candidates"]
        assert candidates

        shortlist = candidates[: min(3, len(candidates))]
        route = post_json(base_url, "/api/route", {"candidates": shortlist, "base_city": "Los Angeles, CA"}, args.timeout)
        assert len(route["stops"]) == len(shortlist), route

        packet = post_json(
            base_url,
            "/api/packet",
            {"candidates": shortlist, "briefs": briefs, "base_city": "Los Angeles, CA"},
            args.timeout,
        )
        assert len(packet["locations"]) == len(shortlist), packet
        assert packet["schedule"], packet
        assert packet["locations"][0]["weather"]["summary"], packet

        mood = post_bytes(base_url, "/api/moodboard", briefs[0], args.timeout)
        assert mood, "empty moodboard response"

    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(f"Smoke failed for {base_url}: {exc}", file=sys.stderr)
        return 1

    print(f"Smoke passed for {base_url}")
    return 0


def get_json(base_url: str, path: str, timeout: float) -> dict:
    with urllib.request.urlopen(base_url + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url: str, path: str, payload: dict, timeout: float) -> dict:
    data = post_bytes(base_url, path, payload, timeout)
    return json.loads(data.decode("utf-8"))


def post_bytes(base_url: str, path: str, payload: dict, timeout: float) -> bytes:
    req = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


if __name__ == "__main__":
    raise SystemExit(main())
