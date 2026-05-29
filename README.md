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
[ venue photo + Gemini vision ]  score each candidate vs. the brief (0-100 + why)
      |
      v
[ map + shortlist ]  you pick the contenders
      |
      v
[ 2-opt route optimizer + astral ]  scout-day route, golden-hour aware
      |
      v
[ Gemini ]  shoot-day packet  +  [ Imagen ]  per-scene mood-board frames
```

- **Frontend:** Vite + React + TypeScript + Tailwind, map via Leaflet +
  OpenStreetMap (keyless, so the map renders even in demo mode).
- **Backend:** FastAPI. Gemini via the `google-genai` SDK. Google Places and
  Street View are called server-side only, so no map key ever ships to the
  browser.
- **Routing:** our own scout-day optimizer (nearest-neighbor seed + 2-opt) over
  shortlisted locations with travel-time estimates.
- **Deploy:** one self-contained container (Docker / Cloud Run).

## Run with Docker (one command)

The whole app (frontend + API) builds and runs in a single container. No Node or
Python toolchain needed, just Docker.

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
make test           # backend pytest smoke tests (demo mode, no keys)
make docker-build   # build the recce:latest image
make up             # docker compose up --build
bash scripts/deploy_cloud_run.sh
```

The deploy script runs `gcloud run deploy --source .`, which builds the image
remotely with Cloud Build (no local Docker needed) and returns a public URL. Set
the keys in `.env` first to deploy the live pipeline; otherwise it runs in demo mode.

## Keys

| Key | Where | Needed for |
| --- | --- | --- |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | scene understanding, vision scoring, packet, mood boards |
| `GOOGLE_MAPS_API_KEY` | Google Maps Platform (Places API New + Street View Static + Geocoding) | live candidate search and Street View |

Without keys, demo mode covers the full flow.

## Project layout

```
Dockerfile  docker-compose.yml          # one-command container
backend/app/  gemini.py  places.py  routing.py  astro.py  packet.py  routes.py  main.py
backend/tests/ test_pipeline.py
frontend/src/  App.tsx  api.ts  types.ts  components/{MapView,CandidateCard}.tsx
docs/          one-pager.md  demo-script.md  judging-map.md  architecture.md  go-live.md
scripts/       deploy_cloud_run.sh
```

## Docs

- [docs/go-live.md](docs/go-live.md): step-by-step to add keys, run live, and deploy.
- [docs/architecture.md](docs/architecture.md): data flow, components, design decisions.
- [docs/one-pager.md](docs/one-pager.md): the submission one-pager.
- [docs/demo-script.md](docs/demo-script.md): 2-minute intro and 1-minute demo scripts.
- [docs/judging-map.md](docs/judging-map.md): how Recce maps to the judging rubric.

## License

MIT. See [LICENSE](LICENSE).
