# Recce Demo Script

Two videos are required: a 2-minute team intro and a 1-minute prototype demo.

## 2-minute intro (talking head with a few B-roll cuts)

- 0:00 Hook. "Finding where to film is still done by hand. A location manager reads the script, then spends days hunting for places that match and working out the logistics."
- 0:20 Problem. The search is brute force even though the judgment is skilled. Small teams, rising production volume.
- 0:40 Solution. "Recce reads the script with Gemini and turns each scene into shoot-ready locations in minutes." One line per step: brief, find and score, route, packet. The core idea: it does not keyword-match, it judges each real location's photography against the director's brief, on look and tone, the way a scout does.
- 1:10 Why us. PhD in spatial AI, production geospatial ML at ESRI, route-optimization research. This is exactly that stack pointed at film.
- 1:30 Market and ask. Studios, streamers, agencies; design-partner pilots; what the seed unlocks.
- 1:50 Close. "From script to shoot day, in minutes."

## 1-minute prototype demo (narrated screen recording)

- 0:00 Start with results already loaded (see the timing tip below). "Recce read this scene and scouted real locations for it."
- 0:08 Point at the briefs. "Gemini pulled each scene into a structured brief: a dawn seaside diner, a clifftop lighthouse at dusk, a rain-soaked alley at night."
- 0:20 The map and cards. "For every candidate, Gemini looks at the location's real photography and scores how well it fits the brief, on look and mood, not just keywords. Search a lighthouse and it surfaces actual lighthouses, Point Arena, Point Reyes, not companies named Lighthouse." Hover a high score and a low one to show the rationale and flags; note the low scores are honest signal, a real place that does not fit the tone.
- 0:35 The top pick per scene is pre-shortlisted. Click "Plan scout day." "It optimizes the drive across your picks, with arrival times."
- 0:45 Click "Shoot-day packet" and open a location. "Real golden-hour windows for the shoot date, parking, power, permits, and a starter shotlist."
- 0:55 End on the packet. "From script to shoot day, in minutes. That is Recce."

## Tips

- Record at 1280x800 or larger; the two-pane layout films well.
- Scoring is the highlight: it reflects each venue's real photo judged against the brief on look and mood, so a strong location can still score mid if the tone is off. That is the feature, lean into it.
- The lighthouse scene demos best on camera (clear, high-scoring matches). The alley scene is the honest hard case (night noir alleys rarely have flattering daytime venue photos).
- Live scoring of a full candidate pool takes roughly 30 to 40 seconds. Run "Find locations" before you start recording, or trim the wait, so the demo opens on results.
- For the live version, set `GEMINI_API_KEY` and `GOOGLE_MAPS_API_KEY` so the thumbnails are real venue photos and the scores are generated on camera.
