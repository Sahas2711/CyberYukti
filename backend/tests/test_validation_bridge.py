"""Tests for live bridge between backend and Evidence Validation Engine."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "cyberyukti-backend"


def test_mounted_evidence_engine_endpoints(client):
    resp = client.get("/api/evidence-engine/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp_probes = client.get("/api/evidence-engine/probes")
    assert resp_probes.status_code == 200
    probes = resp_probes.json()["probes"]
    assert "PACKAGE_VERSION" in probes
    assert "HTTP_ENDPOINT" in probes
    assert "PORT_CHECK" in probes
    assert "FILE_EXISTS" in probes


def test_validate_vulnerable_target_confirmed(client):
    # Validate CASE-002 (jquery) on vulnerable target shop-api-01
    resp = client.post("/api/cases/CASE-002/validate?target_override=shop-api-01")
    assert resp.status_code == 200
    case = resp.json()

    assert case["evidence"]["status"] == "CONFIRMED"
    assert case["evidence"]["confidence"] >= 0.90
    assert case["priority"]["level"] == "P2"
    assert case["priority"]["score"] >= 60.0

    # Observation details
    obs = case["evidence"]["observations"]
    assert len(obs) >= 1
    assert "1.12.4" in obs[0]["observed_value"]


def test_validate_patched_target_not_confirmed_and_reprioritized(client):
    # Validate CASE-002 (jquery) on patched target shop-api-01-patched
    # Installed version is 3.6.0, claimed is 1.12.4 -> NOT_CONFIRMED
    resp = client.post("/api/cases/CASE-002/validate?target_override=shop-api-01-patched")
    assert resp.status_code == 200
    case = resp.json()

    assert case["evidence"]["status"] == "NOT_CONFIRMED"
    assert case["evidence"]["confidence"] >= 0.90
    # Priority drops because evidence is contradictory
    assert case["priority"]["level"] in ("P3", "P4")
    assert case["priority"]["score"] < 55.0

    obs = case["evidence"]["observations"]
    assert len(obs) >= 1
    assert "3.6.0" in obs[0]["observed_value"]


def test_validate_unregistered_asset_inconclusive(client):
    resp = client.post("/api/cases/CASE-002/validate?target_override=unregistered-c2-host")
    assert resp.status_code == 200
    case = resp.json()

    assert case["evidence"]["status"] == "INCONCLUSIVE"
    assert case["evidence"]["confidence"] <= 0.20


def test_validate_appends_audit_trail(client):
    client.post("/api/cases/CASE-002/validate?target_override=shop-api-01")
    resp = client.get("/api/cases/CASE-002/audit")
    assert resp.status_code == 200
    audit_events = resp.json()

    assert len(audit_events) >= 1
    latest = audit_events[-1]
    assert latest["action"] == "EVIDENCE_VALIDATED"
    assert latest["actor"] == "evidence-engine"
    assert "evidence_status" in latest["new_state"]


def test_validate_nonexistent_case_returns_404(client):
    resp = client.post("/api/cases/CASE-DOES-NOT-EXIST/validate")
    assert resp.status_code == 404
