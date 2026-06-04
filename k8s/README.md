# Kubernetes Deployment

This directory contains a Kustomize base for running Recce on Kubernetes.

## Build and Push

```bash
docker build -t arunsharma08/recce:latest .
docker push arunsharma08/recce:latest
```

For another registry, override the image:

```bash
kubectl kustomize k8s/base | sed 's#arunsharma08/recce:latest#YOUR_IMAGE#g' | kubectl apply -f -
```

## Secrets

The Deployment references `recce-secrets` as optional so demo mode works without keys.
For live mode:

```bash
kubectl create namespace recce
kubectl create secret generic recce-secrets \
  -n recce \
  --from-literal=GEMINI_API_KEY='...' \
  --from-literal=GOOGLE_MAPS_API_KEY='...' \
  --from-literal=OPENWEATHER_API_KEY='...'
```

## Deploy

```bash
kubectl apply -k k8s/base
kubectl rollout status deployment/recce -n recce
```

## Smoke Test

```bash
scripts/k8s_smoke.sh
```

The smoke script port-forwards the Service and runs `scripts/smoke_api.py` through
the full API workflow: health, script segmentation, analysis, candidates, route,
packet, and moodboard response.

## Production Notes

- Replace `recce.example.com` in `k8s/base/ingress.yaml`.
- Use a stable image tag instead of `latest` for production rollouts.
- Set `RECCE_WEATHER_PROVIDER=open-meteo` or `openweather` in the ConfigMap when
  live forecasts are needed.
- Set `RECCE_OSRM_URL` to a cluster-local OSRM Service URL if OSRM is deployed.
- Keep API keys in Kubernetes Secrets or an external secret operator, not in Git.
