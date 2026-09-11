"""
Tests for POST /explain endpoint.

Covers:
1. Confirmed critical finding  — summary says "confirmed"
2. Inconclusive finding        — summary says "inconclusive", never "confirmed"
3. Not-confirmed finding       — summary says "not confirmed", never "confirmed"
4. Unavailable validation      — summary says "unavailable", never "confirmed"

Each test also verifies the full response shape:
  finding_id, title, risk_score, priority, reasons, factors, summary
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_explain(payload: dict) -> dict:
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    return response.json()


def _assert_response_shape(body: dict) -> None:
    """Every /explain response must carry all required fields."""
    for field in (
        "finding_id", "title", "risk_score", "priority",
        "reasons", "factors", "summary",
        "evidence_confidence", "evidence_status", "decision_category",
    ):
        assert field in body, f"Missing field: {field}"
    assert isinstance(body["reasons"], list)
    assert isinstance(body["factors"], dict)
    assert isinstance(body["summary"], str)
    assert len(body["summary"]) > 0


# ---------------------------------------------------------------------------
# 1. Confirmed critical finding
# ---------------------------------------------------------------------------

def test_explain_confirmed_critical_finding():
    """
    A critical, internet-exposed, production finding with CONFIRMED evidence
    must return P1, include confirmed language in the summary, and never
    mention inconclusive or unavailable.
    """
    payload = {
        "finding_id": "E001",
        "title": "Remote Code Execution",
        "severity": "critical",
        "cvss": 9.8,
        "asset": {
            "id": "prod-api",
            "criticality": 1.0,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.90},
    }

    body = _post_explain(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "E001"
    assert body["title"] == "Remote Code Execution"
    assert body["priority"] == "P1"
    assert body["risk_score"] >= 0.80

    summary = body["summary"].lower()
    assert "e001" in summary
    assert "p1" in summary
    assert "confirmed" in summary
    assert "inconclusive" not in summary
    assert "unavailable" not in summary
    assert "not confirmed" not in summary


# ---------------------------------------------------------------------------
# 2. Inconclusive validation
# ---------------------------------------------------------------------------

def test_explain_inconclusive_finding():
    """
    A finding with INCONCLUSIVE validation must say "inconclusive" in the
    summary and must never claim the evidence was confirmed.
    """
    payload = {
        "finding_id": "E002",
        "title": "Cross-Site Scripting",
        "severity": "high",
        "asset": {
            "id": "staging-web",
            "criticality": 0.5,
            "internet_exposed": False,
            "environment": "staging",
        },
        "validation": {"status": "INCONCLUSIVE", "confidence": 0.50},
    }

    body = _post_explain(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "E002"
    assert body["title"] == "Cross-Site Scripting"

    summary = body["summary"].lower()
    assert "e002" in summary
    assert "inconclusive" in summary
    # Must NOT claim confirmation
    assert "confirmed with" not in summary
    assert "was confirmed" not in summary


# ---------------------------------------------------------------------------
# 3. Not-confirmed validation
# ---------------------------------------------------------------------------

def test_explain_not_confirmed_finding():
    """
    A finding with NOT_CONFIRMED validation must say the evidence was not
    confirmed and must never use the word "confirmed" in a positive context.
    """
    payload = {
        "finding_id": "E003",
        "title": "Path Traversal",
        "severity": "medium",
        "asset": {
            "id": "dev-server",
            "criticality": 0.3,
            "internet_exposed": False,
            "environment": "development",
        },
        "validation": {"status": "NOT_CONFIRMED", "confidence": 0.0},
    }

    body = _post_explain(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "E003"
    assert body["title"] == "Path Traversal"

    summary = body["summary"].lower()
    assert "e003" in summary
    assert "not confirmed" in summary
    # Must NOT positively claim confirmation
    assert "was confirmed with" not in summary
    assert "inconclusive" not in summary
    assert "unavailable" not in summary


# ---------------------------------------------------------------------------
# 4. Unavailable validation
# ---------------------------------------------------------------------------

def test_explain_unavailable_validation():
    """
    A finding with UNAVAILABLE validation must say validation data was
    unavailable.  It must never claim confirmation or inconclusive status.
    """
    payload = {
        "finding_id": "E004",
        "title": "Missing Security Header",
        "severity": "low",
        "asset": {
            "id": "test-server",
            "criticality": 0.1,
            "internet_exposed": False,
            "environment": "testing",
        },
        "validation": {"status": "UNAVAILABLE", "confidence": 0.0},
    }

    body = _post_explain(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "E004"
    assert body["title"] == "Missing Security Header"

    summary = body["summary"].lower()
    assert "e004" in summary
    assert "unavailable" in summary
    assert "confirmed with" not in summary
    assert "was confirmed" not in summary
    assert "inconclusive" not in summary
    assert "not confirmed" not in summary
