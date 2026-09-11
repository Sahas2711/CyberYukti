"""End-to-end API tests for Evidence Validation Engine.

Tests all endpoints (/health, /probes, /validate), the three primary demo scenarios
(A: CONFIRMED, B: NOT_CONFIRMED, C: INCONCLUSIVE), and error contracts.
"""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_probes_endpoint():
    resp = client.get("/probes")
    assert resp.status_code == 200
    probes = resp.json()["probes"]
    assert "PACKAGE_VERSION" in probes
    assert "HTTP_ENDPOINT" in probes
    assert "PORT_CHECK" in probes
    assert "FILE_EXISTS" in probes


def test_scenario_a_real_vulnerability_confirmed():
    # Scenario A: Real vulnerability claim against vulnerable target
    # Expected: CONFIRMED with high confidence
    finding_payload = {
        "finding_id": "F-SCENARIO-A",
        "cluster_id": "CL-001",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "Outdated example-package", "cve": "CVE-2023-1111"},
        "location": {"type": "package", "package": "example-package"},
        "evidence": {"claimed_version": "1.2.3"},
    }
    resp = client.post("/validate", json=finding_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_id"] == "F-SCENARIO-A"
    assert data["status"] == "CONFIRMED"
    assert data["confidence"] >= 0.95
    assert data["observed"]["package"] == "example-package"
    assert data["observed"]["version"] == "1.2.3"
    assert data["probe"]["type"] == "PACKAGE_VERSION"
    assert data["probe"]["status"] == "PASS"
    assert data["execution"]["duration_ms"] >= 0
    assert data["validation_id"].startswith("V-")


def test_scenario_b_false_stale_finding_not_confirmed():
    # Scenario B: Stale finding against patched target
    # Finding claims 1.2.3, but patched target has 1.2.9
    # Expected: NOT_CONFIRMED with high confidence
    finding_payload = {
        "finding_id": "F-SCENARIO-B",
        "cluster_id": "CL-002",
        "asset": {"id": "shop-api-01-patched"},
        "vulnerability": {"title": "Outdated example-package", "cve": "CVE-2023-1111"},
        "location": {"type": "package", "package": "example-package"},
        "evidence": {"claimed_version": "1.2.3"},
    }
    resp = client.post("/validate", json=finding_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_id"] == "F-SCENARIO-B"
    assert data["status"] == "NOT_CONFIRMED"
    assert data["confidence"] >= 0.95
    assert data["observed"]["package"] == "example-package"
    assert data["observed"]["version"] == "1.2.9"
    assert any("contradicts claimed version" in r for r in data["reason"])


def test_scenario_c_unregistered_asset_inconclusive():
    # Scenario C: Target asset cannot be established / unregistered
    # Expected: INCONCLUSIVE with low confidence
    finding_payload = {
        "finding_id": "F-SCENARIO-C",
        "cluster_id": "CL-003",
        "asset": {"id": "shop-api-missing-09"},
        "vulnerability": {"title": "Outdated example-package", "cve": "CVE-2023-1111"},
        "location": {"type": "package", "package": "example-package"},
        "evidence": {"claimed_version": "1.2.3"},
    }
    resp = client.post("/validate", json=finding_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_id"] == "F-SCENARIO-C"
    assert data["status"] == "INCONCLUSIVE"
    assert data["confidence"] <= 0.20
    assert any("not in the controlled lab target registry" in r for r in data["reason"])


def test_unmapped_location_type_returns_inconclusive():
    # Legitimate finding with a location type that has no registered probe
    finding_payload = {
        "finding_id": "F-UNMAPPED",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "Unknown config issue"},
        "location": {"type": "firmware_rom"},
        "evidence": {"claimed_version": "v1.0"},
    }
    resp = client.post("/validate", json=finding_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INCONCLUSIVE"
    assert data["probe"]["status"] == "UNSUPPORTED"


def test_malformed_json_returns_400():
    resp = client.post("/validate", content="{bad_json: true", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "malformed_input"


def test_missing_required_fields_returns_400():
    resp = client.post("/validate", json={"finding_id": "F-MISSING-FIELDS"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "malformed_input"
