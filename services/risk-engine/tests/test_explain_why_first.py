"""
Tests for POST /explain/why-first and the structured explanation object.

Covers:
1. Critical confirmed finding
2. High-risk inconclusive finding
3. Not-confirmed finding
4. Unavailable validation
5. Missing CVE
6. Explanation text changes when important input factors change
7. Confidence warnings and the "never claim confirmed" rule
8. The existing /explain endpoint remains functional

Each test also verifies the full response shape:
  finding_id, title, risk_score, priority, evidence_confidence,
  risk_confidence_category, explanation
  (explanation contains summary, why_this_priority, priority_basis,
   key_drivers, risk_factors, evidence_factors, confidence_warning,
   recommended_next_step)
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(
    finding_id: str = "WF001",
    severity: str = "medium",
    cvss: float | None = 5.0,
    cve: str | None = None,
    criticality: float = 0.5,
    internet_exposed: bool = False,
    environment: str = "testing",
    validation_status: str = "UNAVAILABLE",
    confidence: float = 0.0,
) -> dict:
    return {
        "finding_id": finding_id,
        "title": f"Finding {finding_id}",
        "severity": severity,
        "cvss": cvss,
        "cve": cve,
        "asset": {
            "id": f"asset-{finding_id}",
            "criticality": criticality,
            "internet_exposed": internet_exposed,
            "environment": environment,
        },
        "validation": {"status": validation_status, "confidence": confidence},
    }


def _post_why_first(payload: dict) -> dict:
    response = client.post("/explain/why-first", json=payload)
    assert response.status_code == 200
    return response.json()


def _assert_response_shape(body: dict) -> None:
    """Every why-first response must carry all required fields."""
    for field in (
        "finding_id",
        "title",
        "risk_score",
        "priority",
        "evidence_confidence",
        "risk_confidence_category",
        "explanation",
    ):
        assert field in body, f"Missing field: {field}"
    for field in (
        "summary",
        "why_this_priority",
        "priority_basis",
        "key_drivers",
        "risk_factors",
        "evidence_factors",
        "confidence_warning",
        "recommended_next_step",
    ):
        assert field in body["explanation"], f"Missing explanation field: {field}"
    assert isinstance(body["explanation"]["key_drivers"], list)
    assert isinstance(body["explanation"]["risk_factors"], list)
    assert isinstance(body["explanation"]["evidence_factors"], list)


# ---------------------------------------------------------------------------
# 1. Critical confirmed finding
# ---------------------------------------------------------------------------


def test_why_first_critical_confirmed_finding():
    """
    critical / CVSS 10, crit 1.0, internet-exposed, production, CONFIRMED 0.95
    -> score 0.9925 -> P1, HIGH_RISK_HIGH_CONFIDENCE.
    """
    payload = _payload(
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )

    body = _post_why_first(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "WF001"
    assert body["title"] == "Finding WF001"
    assert body["risk_score"] == 0.9925
    assert body["priority"] == "P1"
    assert body["evidence_confidence"] == 0.95
    assert body["risk_confidence_category"] == "HIGH_RISK_HIGH_CONFIDENCE"

    explanation = body["explanation"]
    assert explanation["key_drivers"] == [
        "Critical severity",
        "Very high CVSS score (10.0)",
        "Internet-exposed asset",
        "Production environment",
        "High asset criticality (1.0)",
        "Evidence confirmed with 95% confidence",
        "No CVE identifier available",
    ]
    assert explanation["risk_factors"] == [
        "Severity: critical (CVSS 10.0)",
        "Asset criticality: 1.0",
        "Exposure: internet-exposed",
        "Environment: production",
    ]
    assert explanation["evidence_factors"] == [
        "Evidence status: CONFIRMED",
        "Evidence confirmed with 95% confidence",
        "Evidence confidence: 0.95",
    ]
    assert explanation["confidence_warning"] is None
    assert explanation["priority_basis"] == "P1 priority driven mainly by severity"
    assert "P1" in explanation["why_this_priority"]
    assert explanation["recommended_next_step"] == "Review and remediate"
    assert "confirmed" in explanation["summary"].lower()
    assert "IMMEDIATE_ACTION" in explanation["summary"]


# ---------------------------------------------------------------------------
# 2. High-risk inconclusive finding
# ---------------------------------------------------------------------------


def test_why_first_high_risk_inconclusive_finding():
    """
    high / CVSS 8.0, crit 0.5, internet-exposed, production, INCONCLUSIVE 0.80
    -> score 0.705 -> P2 (high risk), HIGH_RISK_LOW_CONFIDENCE.
    """
    payload = _payload(
        severity="high",
        cvss=8.0,
        criticality=0.5,
        internet_exposed=True,
        environment="production",
        validation_status="INCONCLUSIVE",
        confidence=0.80,
    )

    body = _post_why_first(payload)
    _assert_response_shape(body)

    assert body["risk_score"] == 0.705
    assert body["priority"] == "P2"
    assert body["evidence_confidence"] == 0.80
    assert body["risk_confidence_category"] == "HIGH_RISK_LOW_CONFIDENCE"

    explanation = body["explanation"]
    assert explanation["key_drivers"] == [
        "High severity",
        "Internet-exposed asset",
        "Production environment",
        "Evidence validation was inconclusive (80% confidence)",
        "No CVE identifier available",
    ]
    assert explanation["evidence_factors"] == [
        "Evidence status: INCONCLUSIVE",
        "Evidence validation was inconclusive (80% confidence)",
        "Evidence confidence: 0.8",
    ]
    assert (
        explanation["confidence_warning"]
        == "Inconclusive evidence: treat this finding as uncertain until further validation."
    )
    assert explanation["recommended_next_step"] == "Collect additional evidence"

    summary = explanation["summary"].lower()
    assert "inconclusive" in summary
    assert "confirmed with" not in summary


# ---------------------------------------------------------------------------
# 3. Not-confirmed finding
# ---------------------------------------------------------------------------


def test_why_first_not_confirmed_finding():
    """
    low / CVSS 2.0, crit 0.2, internal, development, NOT_CONFIRMED
    -> score 0.205 -> P4, LOW_RISK_LOW_CONFIDENCE.
    """
    payload = _payload(
        finding_id="WF003",
        severity="low",
        cvss=2.0,
        criticality=0.2,
        internet_exposed=False,
        environment="development",
        validation_status="NOT_CONFIRMED",
        confidence=0.0,
    )

    body = _post_why_first(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "WF003"
    assert body["risk_score"] == 0.205
    assert body["priority"] == "P4"
    assert body["evidence_confidence"] == 0.0
    assert body["risk_confidence_category"] == "LOW_RISK_LOW_CONFIDENCE"

    explanation = body["explanation"]
    assert explanation["key_drivers"] == [
        "Evidence was not confirmed",
        "No CVE identifier available",
    ]
    assert explanation["risk_factors"][2] == "Exposure: internal"
    assert explanation["evidence_factors"] == [
        "Evidence status: NOT_CONFIRMED",
        "Evidence was not confirmed",
        "Evidence confidence: 0.0",
    ]
    assert explanation["confidence_warning"] == (
        "Evidence was not confirmed: do not treat this finding as validated."
    )
    assert explanation["recommended_next_step"] == "Defer for later review"

    summary = explanation["summary"].lower()
    assert "not confirmed" in summary
    assert "confirmed with" not in summary
    assert "was confirmed with" not in explanation["summary"]


# ---------------------------------------------------------------------------
# 4. Unavailable validation
# ---------------------------------------------------------------------------


def test_why_first_unavailable_validation():
    """
    medium / CVSS 5.0, crit 0.5, internal, testing, UNAVAILABLE
    -> score 0.415 -> P3, LOW_RISK_LOW_CONFIDENCE.
    """
    payload = _payload(
        finding_id="WF004",
        severity="medium",
        cvss=5.0,
        criticality=0.5,
        internet_exposed=False,
        environment="testing",
        validation_status="UNAVAILABLE",
        confidence=0.0,
    )

    body = _post_why_first(payload)
    _assert_response_shape(body)

    assert body["finding_id"] == "WF004"
    assert body["risk_score"] == 0.415
    assert body["priority"] == "P3"
    assert body["evidence_confidence"] == 0.0
    assert body["risk_confidence_category"] == "LOW_RISK_LOW_CONFIDENCE"

    explanation = body["explanation"]
    assert explanation["key_drivers"] == [
        "Validation data unavailable",
        "No CVE identifier available",
    ]
    assert explanation["evidence_factors"] == [
        "Evidence status: UNAVAILABLE",
        "Validation data unavailable",
        "Evidence confidence: 0.0",
    ]
    assert explanation["confidence_warning"] == (
        "No validation data available: evidence confidence is treated as 0.0."
    )
    assert explanation["recommended_next_step"] == "Defer for later review"

    summary = explanation["summary"].lower()
    assert "unavailable" in summary
    assert "confirmed with" not in summary


# ---------------------------------------------------------------------------
# 5. Missing CVE
# ---------------------------------------------------------------------------


def test_why_first_missing_cve_driver_appears_and_disappears():
    """
    The "No CVE identifier available" driver must be generated only when the
    finding actually lacks a CVE identifier, never as generic filler text.
    """
    base = {
        "finding_id": "WFCVE",
        "title": "Log4Shell",
        "severity": "critical",
        "cvss": 9.8,
        "asset": {
            "id": "app",
            "criticality": 1.0,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.95},
    }

    without_cve = _post_why_first({**base, "cve": None})
    with_cve = _post_why_first({**base, "cve": "CVE-2021-44228"})

    assert "No CVE identifier available" in without_cve["explanation"]["key_drivers"]
    assert "No CVE identifier available" not in with_cve["explanation"]["key_drivers"]
    assert with_cve["explanation"]["key_drivers"] == [
        "Critical severity",
        "Very high CVSS score (9.8)",
        "Internet-exposed asset",
        "Production environment",
        "High asset criticality (1.0)",
        "Evidence confirmed with 95% confidence",
    ]
    # Otherwise-identical findings must produce identical risk factors
    assert (
        without_cve["explanation"]["risk_factors"]
        == with_cve["explanation"]["risk_factors"]
    )


# ---------------------------------------------------------------------------
# 6. Explanation text changes when input factors change
# ---------------------------------------------------------------------------


def test_explanation_changes_when_severity_changes():
    """Key drivers and summary must differ when the severity label changes."""
    low = _post_why_first(_payload(severity="medium", cvss=None))
    critical = _post_why_first(_payload(severity="critical", cvss=None))

    assert (
        low["explanation"]["key_drivers"]
        != critical["explanation"]["key_drivers"]
    )
    assert (
        low["explanation"]["summary"]
        != critical["explanation"]["summary"]
    )
    assert "critical severity" in critical["explanation"]["summary"].lower()


def test_priority_basis_changes_when_dominant_factor_changes():
    """
    The dominant factor must be derived from the weighted contributions, so
    raising asset criticality can flip the priority basis from exposure to
    asset criticality.
    """
    low_crit = _payload(
        finding_id="WFB1",
        severity="informational",
        cvss=None,
        criticality=0.5,
        internet_exposed=True,
        validation_status="UNAVAILABLE",
    )
    high_crit = _payload(
        finding_id="WFB2",
        severity="informational",
        cvss=None,
        criticality=0.9,
        internet_exposed=True,
        validation_status="UNAVAILABLE",
    )

    body_low = _post_why_first(low_crit)
    body_high = _post_why_first(high_crit)

    # informational severity (0.05) keeps both scores in P3 for a clean basis check
    assert body_low["priority"] == body_high["priority"] == "P3"
    assert body_low["explanation"]["priority_basis"] == (
        "P3 priority driven mainly by exposure"
    )
    assert body_high["explanation"]["priority_basis"] == (
        "P3 priority driven mainly by asset criticality"
    )
    assert (
        body_low["explanation"]["priority_basis"]
        != body_high["explanation"]["priority_basis"]
    )


# ---------------------------------------------------------------------------
# 7. Confidence warnings and the "never claim confirmed" rule
# ---------------------------------------------------------------------------


def test_confidence_warning_only_when_not_confirmed():
    """confidence_warning is null only for CONFIRMED evidence."""
    statuses = {
        "CONFIRMED": None,
        "INCONCLUSIVE": "Inconclusive evidence",
        "NOT_CONFIRMED": "Evidence was not confirmed",
        "UNAVAILABLE": "No validation data available",
    }
    for status, expected_fragment in statuses.items():
        body = _post_why_first(
            _payload(validation_status=status, confidence=0.90)
        )
        warning = body["explanation"]["confidence_warning"]
        if expected_fragment is None:
            assert warning is None, status
        else:
            assert warning is not None, status
            assert expected_fragment in warning, status


def test_non_confirmed_evidence_never_claims_confirmation():
    """For the three non-CONFIRMED statuses, no text in the explanation may
    claim the evidence was confirmed (positive confirmation only)."""
    for status in ("INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"):
        body = _post_why_first(_payload(validation_status=status, confidence=0.90))
        text = " ".join(
            [
                body["explanation"]["summary"],
                " ".join(body["explanation"]["key_drivers"]),
                " ".join(body["explanation"]["evidence_factors"]),
            ]
        )
        assert "confirmed with" not in text, status
        assert "was confirmed with" not in text, status


def test_why_first_is_deterministic():
    """The same input must always produce the identical response."""
    payload = _payload(
        severity="critical",
        cvss=9.8,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    first = _post_why_first(payload)
    second = _post_why_first(payload)
    assert first == second


def test_why_first_response_has_only_required_top_level_fields():
    body = _post_why_first(_payload())
    assert set(body.keys()) == {
        "finding_id",
        "title",
        "risk_score",
        "priority",
        "evidence_confidence",
        "risk_confidence_category",
        "explanation",
    }


# ---------------------------------------------------------------------------
# 8. Existing /explain endpoint remains functional
# ---------------------------------------------------------------------------


def test_explain_endpoint_still_works():
    payload = _payload(
        severity="critical",
        cvss=9.8,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    body = response.json()
    for field in (
        "finding_id",
        "title",
        "risk_score",
        "priority",
        "reasons",
        "factors",
        "evidence_confidence",
        "evidence_status",
        "decision_category",
        "summary",
    ):
        assert field in body, f"Missing field: {field}"
    assert "IMMEDIATE_ACTION" in body["summary"]
    assert isinstance(body["summary"], str)
    assert len(body["summary"]) > 0