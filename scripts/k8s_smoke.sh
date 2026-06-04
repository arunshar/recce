#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${K8S_NAMESPACE:-recce}"
LOCAL_PORT="${K8S_SMOKE_PORT:-18080}"
KUSTOMIZE_DIR="${KUSTOMIZE_DIR:-$ROOT_DIR/k8s/base}"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required for Kubernetes smoke testing" >&2
  exit 1
fi

kubectl apply -k "$KUSTOMIZE_DIR"
kubectl rollout status "deployment/recce" -n "$NAMESPACE" --timeout="${K8S_ROLLOUT_TIMEOUT:-180s}"

cleanup() {
  if [[ -n "${PF_PID:-}" ]]; then
    kill "$PF_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

kubectl port-forward -n "$NAMESPACE" "svc/recce" "$LOCAL_PORT:80" >/tmp/recce-k8s-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

python3 "$ROOT_DIR/scripts/smoke_api.py" --base-url "http://127.0.0.1:$LOCAL_PORT"
