#!/usr/bin/env bash
# Deploy Recce to Google Cloud Run as a single container (API + built frontend).
# The multi-stage Dockerfile builds the frontend, so Cloud Build does everything;
# no local Docker or Node needed.
# Prereqs: gcloud SDK installed and authenticated, a billing-enabled project selected.
#   gcloud auth login && gcloud config set project YOUR_PROJECT
# Usage: bash scripts/deploy_cloud_run.sh   (override REGION / SERVICE via env vars)
set -euo pipefail

REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-recce}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Read a single value from .env WITHOUT shell-sourcing it (values may contain
# spaces or quotes, which would break `source`).
read_env() {
  [ -f "$ROOT/.env" ] || return 0
  local line
  line="$(grep -E "^$1=" "$ROOT/.env" 2>/dev/null | tail -1 || true)"
  line="${line#*=}"
  line="${line%\"}"; line="${line#\"}"
  line="${line%\'}"; line="${line#\'}"
  printf '%s' "$line"
}

ENV_PAIRS=()
GEMINI_API_KEY="$(read_env GEMINI_API_KEY)"
GOOGLE_MAPS_API_KEY="$(read_env GOOGLE_MAPS_API_KEY)"
[ -n "$GEMINI_API_KEY" ] && ENV_PAIRS+=("GEMINI_API_KEY=${GEMINI_API_KEY}")
[ -n "$GOOGLE_MAPS_API_KEY" ] && ENV_PAIRS+=("GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}")

SET_ENV=()
if [ ${#ENV_PAIRS[@]} -gt 0 ]; then
  SET_ENV=(--set-env-vars "$(IFS=,; echo "${ENV_PAIRS[*]}")")
fi

echo "==> Deploying '$SERVICE' to Cloud Run in $REGION (Cloud Build builds the image from the Dockerfile)"
gcloud run deploy "$SERVICE" \
  --source "$ROOT" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  "${SET_ENV[@]}"

echo "==> Done. The public service URL is printed above."
