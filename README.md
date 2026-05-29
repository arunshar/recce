# Recce

**AI location scouting, from script to shoot day.**

Paste a screenplay scene. Recce uses Gemini to read it like a location manager
would, finds and visually scores real-world filming locations against the
director's brief, maps them, plans an efficient scout-day route across the ones
you shortlist, and generates a shoot-day logistics packet (golden-hour timing,
parking, power, permits, a starter shotlist).

A workflow that takes a location department days or weeks, compressed into
minutes.

> Built for the GDG Stanford Hackathon (Gemini / Google AI Studio). "Recce" is
> the film industry's term for a location-scouting trip.

---

## How it works

```
screenplay scene
      |
      v
[ Gemini ]  scene understanding -> structured location briefs
      |
      v
[ Google Places ]  candidate real-world locations per brief
      |
      v
[ Street View + Gemini vision ]  score each candidate vs. the brief (0-100 + why)
      |
      v
[ map + shortlist ]  you pick the contenders
      |
      v
[ 2-opt route optimizer + astral ]  scout-day route, golden-hour aware
      |
      v
[ Gemini ]  shoot-day logistics packet (exportable one-pager)
```

- **Frontend:** Vite + React + TypeScript + Tailwind, map via Leaflet +
  OpenStreetMap (keyless, so the map renders even in demo mode).
- **Backend:** FastAPI. Gemini via the `google-genai` SDK. Google Places and
  Street View are called server-side only, so no map key ever ships to the
  browser.
- **Routing:** our own scout-day optimizer (nearest-neighbor seed + 2-opt) over
  shortlisted locations with travel-time estimates.
- **Deploy:** one container to Google Cloud Run.

## Demo mode (no keys needed)

With no API keys set, Recce runs in **demo mode** against a bundled sample
screenplay and cached responses, so the entire flow works offline. Add keys to
`.env` to run the live pipeline on any scene.

## Quickstart

```bash
cp .env.example .env        # optional: add GEMINI_API_KEY + GOOGLE_MAPS_API_KEY
make install                # backend venv + frontend deps
make backend                # terminal 1: http://localhost:8000
make frontend               # terminal 2: http://localhost:5173
```

Build the single-container production bundle:

```bash
make build                  # frontend -> backend/app/static
make docker-build           # builds recce:latest
```

## Keys

| Key | Where | Needed for |
| --- | --- | --- |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | scene understanding, vision scoring, packet |
| `GOOGLE_MAPS_API_KEY` | Google Maps Platform (Places API New + Street View Static) | live candidate search + Street View |

Without keys, demo mode covers the full flow.

## Status

Built over a weekend for a hackathon. See `docs/` for the architecture notes,
one-pager, demo script, and how Recce maps to the judging rubric.

## License

MIT. See [LICENSE](LICENSE).
