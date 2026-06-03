# Recce One-Pager

**AI location scouting, from script to shoot day.**

## The problem
Finding where to film is still done by hand. A location manager reads the script, pictures each scene, then spends days or weeks searching listings and personal knowledge, driving around to shortlist options, and assembling the logistics for each one. The judgment is skilled, but the search is brute force.

## The solution
Recce turns screenplay material into shoot-ready locations in minutes:

1. It reads a single scene or segments a full script into scene briefs: type, time of day, period, mood, must-have visual elements, characters, and practical needs.
2. It searches a wide pool of real candidates from Google Places plus normalized open location and permit datasets. Gemini looks at each location's own photography to score fit against the director's brief, with a rationale and practical flags. Ranking the full pool by fit lets the genuine matches rise and brand-name lookalikes fall away.
3. It creates concept mood-board frames per scene so the director's visual target is visible beside real candidate imagery.
4. You shortlist on a map, and Recce optimizes an efficient scout-day route across your picks, using OSRM road-network routing when configured and a 2-opt fallback in demo mode.
5. It generates a shoot-day packet per location: real golden-hour windows, weather, parking, power, permit and restriction pointers, a schedule view, and a starter shotlist.

## The core idea
Recce does not stop at keyword matching. It judges each real location's imagery against the director's brief the way a scout does, then layers in permit data, routing, weather, and sun windows so a score becomes an operational recommendation, not just a search result.

## Why now
Multimodal models can finally read a script for intent and judge a place from an image the way a scout does. Content volume keeps rising across studios, streamers, and agencies while location teams stay small.

## Market
Film, television, commercials, and branded content all run location departments with real budgets. Adjacent buyers include event and experiential producers, real-estate and tourism marketers, and virtual-production teams that still scout real references. The entry wedge is indie productions and ad agencies without a deep location library. Expansion runs into studios and a marketplace of vetted, rights-cleared locations.

## Business model
Seat-based SaaS for production companies and agencies, with usage credits for AI scoring and packet generation. Natural upsell into a managed location marketplace and a permit and logistics concierge.

## Why this team
Built by Arun Sharma, PhD in Computer Science (University of Minnesota), specializing in spatial AI and GeoAI. Prior work includes production geospatial ML pipelines at ESRI (maritime route optimization and anomaly detection on AWS) and 15 peer-reviewed publications spanning trajectory analysis, route optimization, and physics-informed learning. Recce points exactly that stack at film: spatial search, multimodal scoring, and route optimization.

## Traction and go-to-market
A working, deployable prototype with a live demo that needs no setup. The expanded pipeline supports multi-scene script upload, mood-board frames, permit-aware filters, optional OSRM routing, and weather-enriched logistics. Go-to-market is short, visually striking demo videos aimed at location managers, line producers, indie filmmakers, and ad-agency producers, plus film-office and film-school partnerships.

## The ask
Intros to production companies and agencies for design-partner pilots, and seed funding to expand the location library, add rights and permit data, and ship the marketplace.
