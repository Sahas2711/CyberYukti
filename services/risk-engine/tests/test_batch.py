"""
Tests for POST /assess/batch endpoint.

Covers:
- Empty batch validation
- Batch with multiple findings
- Correct result count in the response envelope
- Correct priority values for each finding
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_finding(
    finding_id: str,
    title: str,
    severity: str,
    cvss: float,
    criticality: float,
    internet_exposed: bool,
    environment: str,
    validation_status: str,
    confidence: float,
) -> dict:
    return {
        "finding_id": finding_id,
        "title": title,
        "severity": severity,
        "cvss": cvss,
        "asset": {
            "id": f"asset-{finding_id}",
            "criticality": criticality,
            "internet_exposed": internet_exposed,
            "environment": environment,
        },
        "validation": {
            "status": validation_status,
            "confidence": confidence,
        },
    }


# ---------------------------------------------------------------------------
# 1. Empty batch validation
# ---------------------------------------------------------------------------

def test_batch_empty_findings_returns_zero_count():
    """An empty findings list should succeed and return count=0 with no results."""
    payload = {"findings": []}
    response = client.post("/assess/batch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["results"] == []


# ---------------------------------------------------------------------------
# 2. Batch with multiple findings
# ---------------------------------------------------------------------------

def test_batch_with_multiple_findings_succeeds():
    """A batch of two findings should return HTTP 200 with a results list."""
    payload = {
        "findings": [
            _make_finding(
                "B001", "RCE in prod", "critical", 9.8,
                1.0, True, "production", "CONFIRMED", 0.9,
            ),
            _make_finding(
                "B002", "Info disclosure on dev", "low", 2.1,
                0.1, False, "development", "NOT_CONFIRMED", 0.0,
            ),
        ]
    }

    response = client.post("/assess/batch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "count" in body
    assert "results" in body
    assert len(body["results"]) == 2


# ---------------------------------------------------------------------------
# 3. Correct result count
# ---------------------------------------------------------------------------

def test_batch_count_matches_number_of_findings():
    """The `count` field must equal the number of findings submitted."""
    findings = [
        _make_finding(
            f"C00{i}", f"Finding {i}", "medium", 5.0,
            0.5, False, "staging", "UNAVAILABLE", 0.0,
        )
        for i in range(5)
    ]
    payload = {"findings": findings}

    response = client.post("/assess/batch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert len(body["results"]) == 5


# ---------------------------------------------------------------------------
# 4. Correct priority values
# ---------------------------------------------------------------------------

def test_batch_priority_values_are_correct():
    """
    A critical, internet-exposed, production finding with CONFIRMED evidence
    should be P1.  A low, non-exposed, dev finding with NOT_CONFIRMED evidence
    should be P4.
    """
    payload = {
        "findings": [
            _make_finding(
                "D001", "SQL Injection", "critical", 10.0,
                1.0, True, "production", "CONFIRMED", 0.95,
            ),
            _make_finding(
                "D002", "Low dev issue", "low", 1.5,
                0.1, False, "development", "NOT_CONFIRMED", 0.0,
            ),
        ]
    }

    response = client.post("/assess/batch", json=payload)

    assert response.status_code == 200
    results = {r["finding_id"]: r for r in response.json()["results"]}

    assert results["D001"]["priority"] == "P1"
    assert results["D001"]["risk_score"] >= 0.80

    assert results["D002"]["priority"] == "P4"
    assert results["D002"]["risk_score"] < 0.35
