# Architecture

## Flow

```
scene text / full script -> Gemini or heuristic segmentation -> structured briefs
brief                    -> Google Places + open location data -> candidate pool + permit metadata
candidate photo / SV     -> Gemini vision scoring              -> match score + rationale + flags
                            (rank pool by fit, keep best)
shortlist                -> OSRM Trip or nearest-neighbor+2-opt -> scout-day route with ETAs
shortlist + briefs       -> astral + weather + Gemini notes     -> packet + schedule + mood frames
```

## Components

- `backend/app/gemini.py`: scene extraction (structured output, `list[SceneBrief]`), Street View vision scoring (`VisionScore`), shoot-day notes (`LocationNotes`), and image-provider calls.
- `backend/app/script_analysis.py`: deterministic screenplay slugline segmentation for batch uploads and demo fallback.
- `backend/app/moodboard.py`: concept-frame prompt construction, packet-safe image URLs, and demo placeholders.
- `backend/app/places.py`: Google Places (New) text search, Place Photos, Street View Static, geocoding, and a cinematic SVG placeholder for demo mode. Scoring prefers each venue's own photo over a Street View frame. Called server-side only.
- `backend/app/permits.py`: normalized open-data location records, permit flags, restrictions, contacts, and candidate enrichment. Local data can be loaded through `RECCE_LOCATION_DATA`.
- `backend/app/osrm.py`: optional OSRM Table/Trip client. `routing.py` uses it when `RECCE_OSRM_URL` is set, otherwise the in-house 2-opt path remains the fallback.
- `backend/app/routing.py`: route result construction, OSRM handoff, haversine distances, nearest-neighbor seed, 2-opt improvement, and arrival-time construction.
- `backend/app/astro.py`: sunrise, sunset, and golden-hour windows via `astral`, with timezone resolved from the base city.
- `backend/app/weather.py`: optional weather provider layer. Demo estimates are returned by default; `RECCE_WEATHER_PROVIDER=open-meteo` enables no-key live forecasts, and `openweather` uses `OPENWEATHER_API_KEY`.
- `backend/app/packet.py`: assembles the packet from sun math, weather, permit data, concept images, schedule slots, and Gemini (or canned) production notes.
- `backend/app/routes.py`: the API surface. `main.py` serves the API and the built single-page app from one process.
- `frontend/`: Vite + React + TypeScript + Tailwind, with Leaflet + OpenStreetMap for the map.
- `scripts/data_ingest/ingest_open_locations.py`: downloads NYC/SF open film datasets or imports a CSV and writes normalized location JSON.
- `scripts/smoke_api.py`: end-to-end smoke runner for a local, Kubernetes, or deployed service URL.
- `k8s/base/`: Kustomize deployment base with health probes, non-root container security, HPA, PDB, NetworkPolicy, Service, and optional Ingress.

## Design decisions

- **Keys stay server-side.** The browser never receives a Google key. Street View is proxied through `/api/streetview`, and the map uses keyless OpenStreetMap tiles via Leaflet. This is more secure and lets the map render in demo mode.
- **Demo mode.** With no Gemini key, the API serves bundled data or deterministic script segmentation, candidate enrichments, demo weather, and placeholder concept frames. Golden-hour math is real even in demo mode.
- **Optional live services.** `RECCE_OSRM_URL`, `RECCE_WEATHER_PROVIDER`, and `RECCE_LOCATION_DATA` upgrade routing, weather, and permit/location metadata independently; each has a local fallback.
- **Routing fallback.** OSRM gives real road-network route ordering when deployed, while the 2-opt optimizer keeps the product dependency-free in offline demos.
- **One container.** The frontend is built into the backend's `static/` directory, so a single Cloud Run service serves everything at one URL.

## Live-mode switches

| Setting | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Scene understanding, visual scoring, packet notes, and generated concept frames. |
| `GOOGLE_MAPS_API_KEY` | Live Places, Place Photos, Street View, and geocoding. |
| `RECCE_LOCATION_DATA` | Path to normalized open location / permit JSON. |
| `RECCE_OSRM_URL` | Base URL for an OSRM service, e.g. `http://localhost:5000`. |
| `RECCE_WEATHER_PROVIDER` | `demo` (default), `open-meteo`, or `openweather`. |
| `OPENWEATHER_API_KEY` | Required only when `RECCE_WEATHER_PROVIDER=openweather`. |

## Run and deploy

- One container, anywhere: `docker compose up --build` (or `make up`), then open http://localhost:8000. A multi-stage Dockerfile builds the frontend and backend in-image; demo mode needs no keys.
- Cloud Run: `bash scripts/deploy_cloud_run.sh` runs `gcloud run deploy --source .`, which builds the image remotely with Cloud Build (no local Docker needed) and returns a public URL.
- Kubernetes: `kubectl apply -k k8s/base` deploys the scalable base. The image runs as UID `10001`, probes `/api/health`, and can be smoke-tested with `scripts/k8s_smoke.sh`.

## Testing

The backend test suite is organized into eight markers: `unit`, `integration`,
`e2e`, `smoke`, `contract`, `regression`, `performance`, and `security`. The
Kubernetes manifests have separate `k8s` contract/security checks. Frontend smoke
coverage runs through `npm run build`, `npm run smoke`, and `npm run lint`.

## Roadmap

- Imagen mood-board frames per location (a styled concept image per scene).
- Photo-library candidates beyond Street View, and rights/permit data per jurisdiction.
- Google Routes API for real drive times and a managed location marketplace.
