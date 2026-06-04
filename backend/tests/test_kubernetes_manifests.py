from pathlib import Path

import pytest

pytestmark = [pytest.mark.k8s, pytest.mark.security, pytest.mark.contract]

ROOT = Path(__file__).resolve().parents[2]
K8S = ROOT / "k8s" / "base"


def read(name: str) -> str:
    return (K8S / name).read_text(encoding="utf-8")


def test_kubernetes_base_contains_expected_resources():
    expected = {
        "kustomization.yaml",
        "namespace.yaml",
        "configmap.yaml",
        "deployment.yaml",
        "service.yaml",
        "hpa.yaml",
        "pdb.yaml",
        "networkpolicy.yaml",
        "ingress.yaml",
        "secret.example.yaml",
    }
    assert expected <= {path.name for path in K8S.iterdir()}
    kustomization = read("kustomization.yaml")
    for resource in expected - {"secret.example.yaml", "kustomization.yaml"}:
        assert f"- {resource}" in kustomization


def test_deployment_has_scalability_and_health_best_practices():
    deployment = read("deployment.yaml")
    assert "kind: Deployment" in deployment
    assert "replicas: 2" in deployment
    assert "maxUnavailable: 0" in deployment
    assert "startupProbe:" in deployment
    assert "readinessProbe:" in deployment
    assert "livenessProbe:" in deployment
    assert "path: /api/health" in deployment
    assert "resources:" in deployment
    assert "requests:" in deployment
    assert "limits:" in deployment
    assert "secretRef:" in deployment
    assert "optional: true" in deployment


def test_deployment_security_context_matches_non_root_image():
    deployment = read("deployment.yaml")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "runAsNonRoot: true" in deployment
    assert "runAsUser: 10001" in deployment
    assert "allowPrivilegeEscalation: false" in deployment
    assert "readOnlyRootFilesystem: true" in deployment
    assert "drop:" in deployment and "- ALL" in deployment
    assert "seccompProfile:" in deployment
    assert "USER 10001" in dockerfile


def test_service_hpa_pdb_and_network_policy_are_present():
    assert "kind: Service" in read("service.yaml")
    assert "targetPort: http" in read("service.yaml")

    hpa = read("hpa.yaml")
    assert "apiVersion: autoscaling/v2" in hpa
    assert "minReplicas: 2" in hpa
    assert "maxReplicas: 8" in hpa
    assert "averageUtilization: 70" in hpa

    pdb = read("pdb.yaml")
    assert "kind: PodDisruptionBudget" in pdb
    assert "minAvailable: 1" in pdb

    netpol = read("networkpolicy.yaml")
    assert "kind: NetworkPolicy" in netpol
    assert "policyTypes:" in netpol
    assert "Ingress" in netpol and "Egress" in netpol


def test_secret_example_does_not_contain_real_keys():
    secret = read("secret.example.yaml")
    assert "stringData:" in secret
    assert 'GEMINI_API_KEY: ""' in secret
    assert 'GOOGLE_MAPS_API_KEY: ""' in secret
    assert 'OPENWEATHER_API_KEY: ""' in secret
