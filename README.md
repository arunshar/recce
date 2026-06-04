# Recce

**AI location scouting, from script to shoot day.**

**Live demo:** https://recce-216756172879.us-central1.run.app (runs in demo mode, no setup needed)

Paste a screenplay scene or upload a text-like full script. Recce reads it like
a location manager would, finds and visually scores real-world filming locations
against the director's brief, maps them, creates concept mood-board frames, plans
an efficient scout-day route across the ones you shortlist, and generates a
shoot-day logistics packet (golden-hour timing, weather, parking, power, permits,
restrictions, and a starter shotlist).

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
[ Google Places + open data ]  candidate real-world locations + permit metadata
      |
      v
[ venue photo + Gemini vision ]  score each candidate vs. the brief (0-100 + why)
      |
      v
[ map + shortlist ]  you pick the contenders
      |
      v
[ OSRM or 2-opt + astral + weather ]  scout-day route, golden-hour aware
      |
      v
[ Gemini ]  shoot-day packet, schedule  +  [ Imagen ]  per-scene mood-board frames
```

- **Frontend:** Vite + React + TypeScript + Tailwind, map via Leaflet +
  OpenStreetMap (keyless, so the map renders even in demo mode).
- **Backend:** FastAPI. Gemini via the `google-genai` SDK. Google Places and
  Street View are called server-side only, so no map key ever ships to the
  browser.
- **Routing:** optional OSRM Trip routing (`RECCE_OSRM_URL`) with our own
  scout-day optimizer (nearest-neighbor seed + 2-opt) as the no-service fallback.
- **Open data:** normalized permit/location records can be loaded from
  `RECCE_LOCATION_DATA`; `scripts/data_ingest/ingest_open_locations.py` can fetch
  NYC/SF datasets or import a CSV.
- **Deploy:** one self-contained container (Docker / Cloud Run).

## Run with Docker (one command)

The published multi-arch image (amd64 + arm64) runs anywhere, no clone and no build:

```bash
docker run -p 8000:8080 arunsharma08/recce      # then open http://localhost:8000
```

Or build it from source. The whole app (frontend + API) builds and runs in a single
container. No Node or Python toolchain needed, just Docker.

```bash
docker compose up --build         # then open http://localhost:8000
```

It runs in **demo mode** by default (no keys, full flow on bundled sample data).
To go live, add your keys to a `.env` file (compose reads it automatically) or
pass them inline:

```bash
GEMINI_API_KEY=... GOOGLE_MAPS_API_KEY=... docker compose up --build
```

Equivalent without compose:

```bash
docker build -t recce .
docker run --rm -p 8000:8080 recce                 # demo mode
docker run --rm -p 8000:8080 --env-file .env recce # live (after: cp .env.example .env)
```

## Demo mode (no keys needed)

With no API keys set, Recce runs against a bundled sample screenplay and cached
responses, so the entire flow works offline. Golden-hour times are computed for
real even in demo mode. Add keys to `.env` to run the live pipeline on any scene.

## Local development (without Docker)

```bash
cp .env.example .env        # optional: add GEMINI_API_KEY + GOOGLE_MAPS_API_KEY
make install                # backend venv + frontend deps
make backend                # terminal 1: http://localhost:8000
make frontend               # terminal 2: http://localhost:5173
```

Open http://localhost:5173, click **Sample**, then **Find locations**.

## Build, test, deploy

```bash
make build          # frontend -> backend/app/static (for the local single-port run)
make test           # all backend pytest tests (demo mode, no keys)
make test-frontend  # frontend build + UI smoke + lint
make docker-build   # build the recce:latest image
make up             # docker compose up --build
bash scripts/deploy_cloud_run.sh
```

The test suite is split into eight practical categories: unit, integration,
end-to-end, smoke, contract, regression, performance, and security/config.
See [docs/testing.md](docs/testing.md) for commands and coverage. To smoke-test
a running service, use:

```bash
python3 scripts/smoke_api.py --base-url http://127.0.0.1:8000
```

The deploy script runs `gcloud run deploy --source .`, which builds the image
remotely with Cloud Build (no local Docker needed) and returns a public URL. Set
the keys in `.env` first to deploy the live pipeline; otherwise it runs in demo mode.

## Keys

| Key | Where | Needed for |
| --- | --- | --- |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | scene understanding, vision scoring, packet, mood boards |
| `GOOGLE_MAPS_API_KEY` | Google Maps Platform (Places API New + Street View Static + Geocoding) | live candidate search and Street View |
| `RECCE_LOCATION_DATA` | local JSON path | normalized open location / permit records |
| `RECCE_OSRM_URL` | OSRM service URL | real road-network route ordering |
| `RECCE_WEATHER_PROVIDER` | `demo`, `open-meteo`, or `openweather` | packet weather summaries |
| `OPENWEATHER_API_KEY` | OpenWeatherMap | only if `RECCE_WEATHER_PROVIDER=openweather` |

Without keys, demo mode covers the full flow with bundled candidates, demo
weather, deterministic script segmentation, and placeholder concept frames.

## Project layout

```
Dockerfile  docker-compose.yml          # one-command container
backend/app/  gemini.py  places.py  permits.py  routing.py  osrm.py  astro.py  weather.py  packet.py  routes.py
backend/tests/ test_pipeline.py
frontend/src/  App.tsx  api.ts  types.ts  components/{MapView,CandidateCard}.tsx
docs/          one-pager.md  demo-script.md  judging-map.md  architecture.md  go-live.md
k8s/base/      Kubernetes manifests for scalable deployment
scripts/       deploy_cloud_run.sh  smoke_api.py  k8s_smoke.sh  data_ingest/ingest_open_locations.py
```

## Kubernetes

Recce includes a Kustomize base under `k8s/base` with a non-root Deployment,
Service, health probes, HPA, PodDisruptionBudget, NetworkPolicy, and optional
Ingress. See [k8s/README.md](k8s/README.md).

```bash
kubectl apply -k k8s/base
kubectl rollout status deployment/recce -n recce
scripts/k8s_smoke.sh
```

## Docs

- [docs/submission.md](docs/submission.md): staged content for the hackathon submission.
- [docs/testing.md](docs/testing.md): test matrix, commands, and smoke workflows.
- [docs/go-live.md](docs/go-live.md): step-by-step to add keys, run live, and deploy.
- [docs/architecture.md](docs/architecture.md): data flow, components, design decisions.
- [docs/one-pager.md](docs/one-pager.md): the submission one-pager.
- [docs/demo-script.md](docs/demo-script.md): 2-minute intro and 1-minute demo scripts.
- [docs/judging-map.md](docs/judging-map.md): how Recce maps to the judging rubric.

## License

MIT. See [LICENSE](LICENSE).
