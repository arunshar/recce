# Architecture

## Flow

```
scene text              -> Gemini scene understanding   -> structured briefs
brief                   -> Google Places text search    -> candidate pool
candidate photo / SV    -> Gemini vision scoring         -> match score + rationale + flags
                           (rank pool by fit, keep best)
shortlist               -> nearest-neighbor + 2-opt      -> scout-day route with ETAs
shortlist + briefs      -> astral + Gemini notes         -> shoot-day packet
```

## Components

- `backend/app/gemini.py`: scene extraction (structured output, `list[SceneBrief]`), Street View vision scoring (`VisionScore`), and shoot-day notes (`LocationNotes`).
- `backend/app/places.py`: Google Places (New) text search, Place Photos, Street View Static, geocoding, and a cinematic SVG placeholder for demo mode. Scoring prefers each venue's own photo over a Street View frame. Called server-side only.
- `backend/app/routing.py`: haversine distances, nearest-neighbor seed, 2-opt improvement, and arrival-time construction.
- `backend/app/astro.py`: sunrise, sunset, and golden-hour windows via `astral`, with timezone resolved from the base city.
- `backend/app/packet.py`: assembles the packet from deterministic sun math plus Gemini (or canned) production notes.
- `backend/app/routes.py`: the API surface. `main.py` serves the API and the built single-page app from one process.
- `frontend/`: Vite + React + TypeScript + Tailwind, with Leaflet + OpenStreetMap for the map.

## Design decisions

- **Keys stay server-side.** The browser never receives a Google key. Street View is proxied through `/api/streetview`, and the map uses keyless OpenStreetMap tiles via Leaflet. This is more secure and lets the map render in demo mode.
- **Demo mode.** With no Gemini key, the API serves bundled briefs and candidates plus a placeholder image, so the full flow works offline. Golden-hour math is real even in demo mode.
- **Our own routing.** A 2-opt optimizer keeps the routing dependency-free and in-house, with the Google Routes API available as a future enhancement.
- **One container.** The frontend is built into the backend's `static/` directory, so a single Cloud Run service serves everything at one URL.

## Deploy

- Recommended: `bash scripts/deploy_cloud_run.sh` runs `gcloud run deploy --source backend`, which builds the image remotely with Cloud Build (no local Docker needed) and returns a public URL.
- Local image build: `make docker-build` (requires a running Docker daemon).

## Roadmap

- Imagen mood-board frames per location (a styled concept image per scene).
- Photo-library candidates beyond Street View, and rights/permit data per jurisdiction.
- Google Routes API for real drive times and a managed location marketplace.
