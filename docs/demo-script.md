# Recce Demo Script

Two videos are required: a 2-minute team intro and a 1-minute prototype demo.

## 2-minute intro (talking head with a few B-roll cuts)

- 0:00 Hook. "Finding where to film is still done by hand. A location manager reads the script, then spends days hunting for places that match and working out the logistics."
- 0:20 Problem. The search is brute force even though the judgment is skilled. Small teams, rising production volume.
- 0:40 Solution. "Recce reads the script with Gemini and turns each scene into shoot-ready locations in minutes." One line per step: brief, find and score, route, packet.
- 1:10 Why us. PhD in spatial AI, production geospatial ML at ESRI, route-optimization research. This is exactly that stack pointed at film.
- 1:30 Market and ask. Studios, streamers, agencies; design-partner pilots; what the seed unlocks.
- 1:50 Close. "From script to shoot day, in minutes."

## 1-minute prototype demo (narrated screen recording)

- 0:00 Start in demo mode. Click "Sample" to load a three-scene noir excerpt. "No setup, this runs live."
- 0:08 Click "Find locations." As briefs appear: "Gemini pulls each scene into a structured brief: a dawn seaside diner, a clifftop lighthouse at dusk, a rain-soaked alley at night."
- 0:20 The map fills with scored pins. "It finds real places and scores each against the brief from Street View. Green is shoot-ready." Hover a 92 and a 54 to show the rationale and flags.
- 0:35 The top pick per scene is pre-shortlisted. Click "Plan scout day." "It optimizes the drive across your picks, with arrival times."
- 0:45 Click "Shoot-day packet" and open a location. "Real golden-hour windows for the shoot date, parking, power, permits, and a starter shotlist."
- 0:55 End on the packet. "From script to shoot day, in minutes. That is Recce."

## Tips

- Record at 1280x800 or larger; the two-pane layout films well.
- For the live version, set `GEMINI_API_KEY` and `GOOGLE_MAPS_API_KEY` so Street View shows real imagery and the scores are generated on camera.
- Move the cursor deliberately; pause on the rationale text and the golden-hour line.
