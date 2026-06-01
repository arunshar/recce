# Submission packet (main hackathon project form)

Paste-ready content for the "May 31st Stanford Hackathon [online and second
chance track] Project Submission Form." All fields below.

> Email caveat: the form is signed in as arunshar@umn.edu, but "Team Leader Email
> (same as Luma)" must match the address used to register the Luma event. The
> prerequisite form used arun08sharma@gmail.com. Use whichever you registered Luma with.

## Field values

Team Name
```
Recce
```

Team Leader Name
```
Arun Sharma
```

Team Leader Email (same as Luma)
```
use the email you registered the Luma event with (gmail vs umn, see caveat above)
```

Team Members (up to 3, excluding leader)
```
Solo entry (no additional members)
```

Hosted Prototype URL (Google AI Studio and Google Cloud Run)
```
https://recce-216756172879.us-central1.run.app
```

Code Repository Link
```
https://github.com/arunshar/recce
```
Note: the field hints "Google AI Studio Sharing Link." Recce was built as a real
repo (FastAPI + React), not inside the AI Studio app builder, so there is no AI
Studio share link. The GitHub repo is the actual code repository; use that.

2-Minute Video URL (team intro + elevator pitch): ADD YOUTUBE LINK AFTER RECORDING
1-Minute Video URL (prototype demo): ADD YOUTUBE LINK AFTER RECORDING

## One-Pager (Project Description, plain text, paste into the form)

```
RECCE: AI location scouting, from script to shoot day.

The problem. Finding where to film is still done by hand. A location manager reads the script, pictures each scene, then spends days or weeks searching listings and personal knowledge, driving around to shortlist options, and assembling the logistics for each one. The judgment is skilled, but the search is brute force.

What it does. Recce turns a screenplay scene into shoot-ready locations in minutes. Gemini reads the scene into a structured location brief (type, time of day, period, mood, must-have visual elements, practical needs). It searches real candidates on Google Places and scores each by having Gemini look at the venue's own photography and judge it against the brief on look and mood, not keyword matching, so genuine matches surface over lookalikes (a search for a lighthouse returns actual lighthouses, not companies named Lighthouse). You shortlist on a map, Recce optimizes an efficient scout-day route across your picks, and it generates a shoot-day packet per location with real golden-hour windows, parking, power, permit pointers, and a starter shotlist. It also generates a cinematic Imagen mood-board frame per scene.

Why it matters. Location scouting is a real, costly, manual workflow across film, television, commercials, and branded content, all of which run location departments with real budgets. The output is concrete: a scored shortlist with rationales and a shoot-day packet a crew could actually use.

How it is built. Gemini and Google AI Studio for scene understanding, vision scoring, and shoot-day notes; Google Maps (Places, Street View, Geocoding) for real locations; Imagen for mood boards; a custom nearest-neighbor plus 2-opt route optimizer; FastAPI and React served as one container on Google Cloud Run. It runs fully in demo mode with no keys, so it can be tried instantly.

Team. Arun Sharma, PhD in Computer Science (University of Minnesota), specializing in spatial AI and GeoAI, with prior production geospatial ML at ESRI. Recce points exactly that stack at film: spatial search, multimodal scoring, and route optimization.
```

## Videos (the only things needing recording)

Scripts are in docs/demo-script.md. See the chat walkthrough for step-by-step
recording and YouTube upload instructions.

- 2-minute: team intro and elevator pitch (you on camera or voiceover over slides).
- 1-minute: narrated screen recording of the prototype. Pre-click "Find locations"
  before recording (it takes ~45s live), and demo the lighthouse scene.
