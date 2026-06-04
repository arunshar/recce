# Testing Strategy

Recce now uses eight practical test categories. All backend tests run in demo
mode by default, so local API keys do not change CI behavior.

## Commands

```bash
make test              # all backend pytest tests
make test-unit         # pure function/module behavior
make test-integration  # API + provider-client integration with mocked services
make test-e2e          # full workflow: script -> packet
make test-smoke        # fast health/workflow sanity
make test-contract     # API/schema and Kubernetes contract checks
make test-regression   # demo-data and schedule fallback stability
make test-performance  # deterministic local performance budgets
make test-security     # secret hygiene and deploy security checks
make test-k8s          # Kubernetes manifest best-practice checks
make test-frontend     # TypeScript build, UI smoke check, lint
```

To smoke-test a running service:

```bash
python3 scripts/smoke_api.py --base-url http://127.0.0.1:8000
python3 scripts/smoke_api.py --base-url https://recce-216756172879.us-central1.run.app
```

To smoke-test Kubernetes after deploying:

```bash
scripts/k8s_smoke.sh
```

## Coverage Map

| Type | What It Covers | Files |
| --- | --- | --- |
| Unit | Script segmentation, sun math, mood prompts, permits, routing, weather, demo image helpers. | `backend/tests/test_unit_workflow.py` |
| Integration | API endpoints, schema parsing, mocked OSRM/Open-Meteo clients. | `backend/tests/test_api_contract.py` |
| End-to-end | Full API workflow from script upload through packet generation. | `backend/tests/test_e2e_smoke_regression.py` |
| Smoke | Health and minimal workflow sanity. | `backend/tests/test_pipeline.py`, `scripts/smoke_api.py` |
| Contract | OpenAPI routes, Pydantic response models, Kubernetes object contract. | `backend/tests/test_api_contract.py`, `backend/tests/test_kubernetes_manifests.py` |
| Regression | Demo brief/candidate stability and schedule rollover behavior. | `backend/tests/test_e2e_smoke_regression.py` |
| Performance | Demo pipeline and route optimizer runtime budgets. | `backend/tests/test_e2e_smoke_regression.py` |
| Security | Key non-disclosure, placeholder escaping, non-root Kubernetes settings. | `backend/tests/test_e2e_smoke_regression.py`, `backend/tests/test_kubernetes_manifests.py` |

## Notes

- Performance tests use deterministic local demo data. They are intended as
  guardrails, not formal load tests.
- The API smoke script is safe for deployed demo services because it uses bundled
  demo endpoints and does not require credentials.
- Kubernetes smoke requires `kubectl` and a current cluster context.
