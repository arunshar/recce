# Submission packet (main hackathon)

Staged content for the main GDG Stanford Hackathon project submission. This is
separate from the prerequisite setup form. Copy each field when the submission
opens. Required deliverables: hosted prototype, code repo, one-pager, a 2-minute
intro video, and a 1-minute demo video.

## Links

- Hosted prototype (Cloud Run): https://recce-216756172879.us-central1.run.app
- Code repository: https://github.com/arunshar/recce
- Intro video (2 min): ADD YOUTUBE LINK AFTER RECORDING
- Demo video (1 min): ADD YOUTUBE LINK AFTER RECORDING

## Fields

Project name
```
Recce
```

Tagline
```
AI location scouting, from script to shoot day
```

One-line description
```
Paste a screenplay scene and Recce uses Gemini to find, score, map, route, and package real filming locations in minutes.
```

What it does
```
Recce reads a screenplay scene with Gemini into a structured location brief, finds real candidates on Google Places, and scores each by judging the venue's own photography against the brief on look and mood. You shortlist on a map, it optimizes a scout-day route, and it generates a shoot-day packet (real golden-hour times, parking, power, permits, a starter shotlist) plus an Imagen mood-board frame per scene.
```

Problem
```
Location scouting is a manual workflow that takes location teams days or weeks. Recce compresses it to minutes.
```

Tech stack
```
Gemini, Google AI Studio, Imagen, Google Maps (Places, Street View, Geocoding), FastAPI, React, Leaflet, Docker, Cloud Run
```

Team
```
Arun Sharma (solo). PhD in spatial AI and GeoAI, University of Minnesota.
```

Category / track
```
AI / Gemini
```

## Longer description (for a comments or summary field)

```
Recce is an AI location-scouting tool for film and TV. Paste a screenplay scene and it turns each scene into shoot-ready locations in minutes. Gemini reads the scene into a structured location brief, then scores real Google Places candidates by judging each venue's own photography against the brief on look and mood (not keyword matching), so genuine matches surface over lookalikes. You shortlist on a map, Recce optimizes an efficient scout-day route across your picks, and generates a shoot-day packet per location with real golden-hour windows, parking, power, permits, and a starter shotlist. It also generates a cinematic Imagen mood-board frame per scene.

Built on Gemini and Google AI Studio, with Google Maps (Places and Street View) and Imagen, served as a single container (FastAPI plus React) deployed to Cloud Run. It runs fully in demo mode with no keys, so it can be tried instantly without setup.

Code: https://github.com/arunshar/recce
```

## Still to do (only you can)

- Record the 2-minute intro and 1-minute demo (script: docs/demo-script.md). Demo the live URL, pre-load Find locations first (it takes ~30 to 40 seconds), show the lighthouse scene, and generate one mood board on camera.
- Upload both to YouTube (unlisted is fine) and paste the links above.
- Submit when the main project form opens.

## Fine print to keep in mind

- "Win up to $5M" is pitch access to VCs, not guaranteed funding.
- Watch for any paid-social-ads expectation in Phase-2 judging; running ads is not required to submit.
- The official build window is the May 31 sprint (11:30 to 2:30 PT). This repo is pre-built, which is a strength; if the rules require building during the window, treat it as a staged foundation.
