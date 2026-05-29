# Go live: your step-by-step checklist

Recce already runs in demo mode with no setup. These steps take it live (real
Gemini + real Google Maps) and get you a public URL plus the assets you submit.

Project lives at `~/Desktop/recce`. Run all commands from there unless noted.

---

## First, the part people trip on: there are TWO different keys, from TWO places

| Key | Get it from | What it powers |
| --- | --- | --- |
| `GEMINI_API_KEY` | Google AI Studio | reading the script, scoring Street View, writing the packet |
| `GOOGLE_MAPS_API_KEY` | Google Cloud Console (Maps Platform) | finding real locations + fetching Street View images |

They can live in the same Google account and even the same Cloud project. They
are not the same key. Both happen to start with `AIza...`, which is why it is
easy to mix them up.

---

## Step 1: Get the Gemini key (about 2 minutes, free)

1. Go to https://aistudio.google.com/apikey and sign in with your Google account.
2. Click **Create API key**, then **Create API key in a new project** (or pick an existing one).
3. Copy the key. This is your `GEMINI_API_KEY`.

The free tier is plenty for the hackathon.

## Step 2: Get the Maps key (about 10 minutes, needs a card on file)

1. Go to https://console.cloud.google.com/google/maps-apis with the same Google account.
2. If asked, create or select a Cloud project (the same one as Step 1 is fine).
3. Turn on billing for the project (add a card). Google has a recurring free
   usage allowance that covers a demo, but a card is required to use Maps APIs.
4. Enable these three APIs (search each in the API Library and click Enable):
   - **Places API (New)**
   - **Street View Static API**
   - **Geocoding API**
5. Go to **APIs & Services > Credentials > Create credentials > API key**. Copy it.
   This is your `GOOGLE_MAPS_API_KEY`.
6. Optional but good: click the new key, and under **API restrictions** limit it
   to the three APIs above.

If you would rather not set up Maps billing before the deadline, skip Steps 2
and 5 to 6. Recce still runs end to end on the bundled sample data, and you can
deploy it that way (see the short path at the bottom).

## Step 3: Put the keys in `.env` (about 1 minute)

```bash
cd ~/Desktop/recce
cp .env.example .env
```

Open `.env` and fill in the two lines (no quotes, no spaces around `=`):

```
GEMINI_API_KEY=AIza...your_gemini_key...
GOOGLE_MAPS_API_KEY=AIza...your_maps_key...
```

`.env` is gitignored, so your keys are never committed.

## Step 4: Run it live on your laptop (about 2 minutes)

```bash
cd ~/Desktop/recce
make backend     # terminal 1  ->  http://localhost:8000
make frontend    # terminal 2  ->  http://localhost:5173
```

Open http://localhost:5173. The badge in the top-right should now read
**Live: Gemini + Maps** instead of **Demo mode**. Paste any scene (or your own
screenplay), click **Find locations**, and you will see real Street View images
and live Gemini scores.

## Step 5: Deploy for the public URL the submission needs (about 15 minutes the first time)

You need a Google Cloud project with billing on (the one from Step 2 works).

1. Install the gcloud CLI:
   ```bash
   brew install --cask google-cloud-sdk
   ```
   (or the installer at https://cloud.google.com/sdk/docs/install)
2. Sign in and pick your project:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
   `YOUR_PROJECT_ID` is shown in the Cloud Console top bar.
3. Turn on the services the deploy uses (first time only):
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```
4. Deploy:
   ```bash
   cd ~/Desktop/recce
   bash scripts/deploy_cloud_run.sh
   ```
   It builds the frontend, then runs `gcloud run deploy --source backend`. Cloud
   Build packages the container in the cloud, so you do not need Docker on your
   laptop. It reads your two keys from `.env` and sets them on the service. If it
   asks to enable an API or pick a region, accept (us-central1 is fine).
5. When it finishes it prints a **Service URL** like
   `https://recce-xxxxx-uc.a.run.app`. That is your hosted prototype link. Open it
   and confirm the badge says Live.

To avoid any ongoing cost, delete the service after judging:
`gcloud run services delete recce --region us-central1`.

## Step 6: Record the two videos (about 30 minutes)

Follow `docs/demo-script.md`. Use QuickTime (screen recording) or Loom.

- 2-minute intro: you on camera or a voiceover over a few slides, hitting the beats.
- 1-minute demo: screen-record the app (deployed URL or localhost) and narrate.

Upload both to YouTube (the event asks for a YouTube link). Unlisted is fine.

## Step 7: Submit

Provide on the submission form:

- One-pager: paste from `docs/one-pager.md` (or export it to PDF).
- Hosted prototype link: your Cloud Run URL.
- Code repository: https://github.com/arunshar/recce
- The two YouTube links.

---

## Short path if you are tight on time

You can skip the Maps key and even the keys entirely:

1. Skip Steps 2, 3 partially (leave keys blank), and deploy:
   ```bash
   cd ~/Desktop/recce && bash scripts/deploy_cloud_run.sh
   ```
2. You get a public URL that runs the full flow on the bundled sample (the badge
   says Demo mode). That is a legitimate working prototype for judges.
3. Add the keys later (set them on the Cloud Run service and redeploy) to flip it
   to live before the deadline.

Minimum to submit something strong: the repo link plus a deployed demo-mode URL
plus the 1-minute demo video. Everything else raises the score.
