"""
Tests for the Evidence Confidence Score, evidence status, and decision categories.

Covers:
1. evidence_confidence per validation status (CONFIRMED / INCONCLUSIVE /
   NOT_CONFIRMED / UNAVAILABLE)
2. evidence_status is preserved and never upgraded
3. All four decision categories (IMMEDIATE_ACTION, VALIDATE_EVIDENCE,
   REMEDIATE, DEFER)
4. New fields are present in /assess, /assess/batch, /assess/batch/sorted
   and /explain responses
5. Backward compatibility of the existing risk_score formula
6. NOT_CONFIRMED / UNAVAILABLE evidence is never described as confirmed
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models import FindingInput, AssetContext, ValidationResult, PriorityResult
from app.scoring import (
    calculate_risk_score,
    calculate_evidence_confidence,
    determine_decision_category,
    DECISION_CATEGORY_IMMEDIATE_ACTION,
    DECISION_CATEGORY_VALIDATE_EVIDENCE,
    DECISION_CATEGORY_REMEDIATE,
    DECISION_CATEGORY_DEFER,
)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(
    finding_id: str = "EV001",
    severity: str = "medium",
    cvss: float | None = 5.0,
    criticality: float = 0.5,
    internet_exposed: bool = False,
    environment: str = "testing",
    validation_status: str = "UNAVAILABLE",
    confidence: float = 0.0,
) -> FindingInput:
    return FindingInput(
        finding_id=finding_id,
        title=f"Finding {finding_id}",
        severity=severity,
        cvss=cvss,
        asset=AssetContext(
            id=f"asset-{finding_id}",
            criticality=criticality,
            internet_exposed=internet_exposed,
            environment=environment,
        ),
        validation=ValidationResult(status=validation_status, confidence=confidence),
    )


# ---------------------------------------------------------------------------
# 1. evidence_confidence per validation status
# ---------------------------------------------------------------------------


def test_evidence_confidence_confirmed_uses_supplied_confidence():
    """CONFIRMED evidence confidence must use the supplied confidence value."""
    finding = _make_finding(
        validation_status="CONFIRMED", confidence=0.95,
    )
    result = calculate_risk_score(finding)
    assert result.evidence_confidence == 0.95
    assert result.evidence_status == "CONFIRMED"


def test_evidence_confidence_inconclusive_preserves_value_and_status():
    """
    INCONCLUSIVE evidence keeps the numeric confidence but must remain
    INCONCLUSIVE in evidence_status (never upgraded to confirmed).
    """
    finding = _make_finding(
        validation_status="INCONCLUSIVE", confidence=0.60,
    )
    result = calculate_risk_score(finding)
    assert result.evidence_confidence == 0.60
    assert result.evidence_status == "INCONCLUSIVE"


def test_evidence_confidence_not_confirmed_is_zero():
    """
    NOT_CONFIRMED evidence must not be treated as confirmed: confidence is 0.0
    regardless of any supplied confidence value.
    """
    finding = _make_finding(
        validation_status="NOT_CONFIRMED", confidence=0.90,
    )
    result = calculate_risk_score(finding)
    assert result.evidence_confidence == 0.0
    assert result.evidence_status == "NOT_CONFIRMED"
    assert "confirmed with" not in " ".join(result.reasons).lower()


def test_evidence_confidence_unavailable_is_zero():
    """
    UNAVAILABLE validation yields an evidence confidence of 0.0 even when a
    confidence value was supplied in the input.
    """
    finding = _make_finding(
        validation_status="UNAVAILABLE", confidence=0.80,
    )
    result = calculate_risk_score(finding)
    assert result.evidence_confidence == 0.0
    assert result.evidence_status == "UNAVAILABLE"


def test_evidence_confidence_is_between_zero_and_one():
    """Every evidence confidence value must stay within [0.0, 1.0]."""
    for status in ("CONFIRMED", "INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"):
        for confidence in (0.0, 0.5, 1.0):
            finding = _make_finding(
                validation_status=status, confidence=confidence,
            )
            result = calculate_risk_score(finding)
            assert 0.0 <= result.evidence_confidence <= 1.0, (
                f"{status}/{confidence} produced "
                f"{result.evidence_confidence}"
            )


def test_evidence_confidence_helper_matches_result():
    """The standalone helper produces the same value as the result field."""
    for status in ("CONFIRMED", "INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"):
        finding = _make_finding(validation_status=status, confidence=0.85)
        assert (
            calculate_evidence_confidence(finding)
            == calculate_risk_score(finding).evidence_confidence
        ), f"Mismatch for status {status}"


# ---------------------------------------------------------------------------
# 2. Decision categories
# ---------------------------------------------------------------------------


def test_high_risk_confirmed_is_immediate_action():
    """
    High risk + high evidence confidence => IMMEDIATE_ACTION.
    critical, CVSS 10, exposed, production, CONFIRMED 0.95 => P1 (>= 0.80).
    """
    finding = _make_finding(
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score == 0.9925
    assert result.priority == "P1"
    assert result.decision_category == DECISION_CATEGORY_IMMEDIATE_ACTION


def test_high_risk_confirmed_low_confidence_is_validate_evidence():
    """
    High risk + low confirmed confidence => VALIDATE_EVIDENCE.
    high, CVSS 8.0, criticality 0.7, exposed, CONFIRMED 0.30 => score 0.74.
    """
    finding = _make_finding(
        severity="high",
        cvss=8.0,
        criticality=0.7,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.30,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score >= 0.60
    assert result.decision_category == DECISION_CATEGORY_VALIDATE_EVIDENCE


def test_high_risk_inconclusive_is_validate_evidence():
    """
    High risk + INCONCLUSIVE evidence is uncertain even with a high numeric
    confidence => VALIDATE_EVIDENCE.
    high, CVSS 8.0, criticality 0.9, exposed, INCONCLUSIVE 0.80 => score 0.805.
    """
    finding = _make_finding(
        severity="high",
        cvss=8.0,
        criticality=0.9,
        internet_exposed=True,
        environment="production",
        validation_status="INCONCLUSIVE",
        confidence=0.80,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score >= 0.60
    assert result.evidence_confidence == 0.80
    assert result.evidence_status == "INCONCLUSIVE"
    assert result.decision_category == DECISION_CATEGORY_VALIDATE_EVIDENCE


def test_high_risk_unavailable_is_validate_evidence():
    """
    High risk + UNAVAILABLE validation => VALIDATE_EVIDENCE.
    critical, CVSS 10, crit 1.0, exposed, UNAVAILABLE => score 0.88.
    """
    finding = _make_finding(
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="UNAVAILABLE",
        confidence=0.0,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score >= 0.60
    assert result.evidence_confidence == 0.0
    assert result.decision_category == DECISION_CATEGORY_VALIDATE_EVIDENCE


def test_low_risk_confirmed_high_confidence_is_remediate():
    """
    Lower risk + high evidence confidence => REMEDIATE.
    cvss 3.0, criticality 0.4, internal, CONFIRMED 0.90 => score 0.415.
    """
    finding = _make_finding(
        severity="low",
        cvss=3.0,
        criticality=0.4,
        internet_exposed=False,
        environment="development",
        validation_status="CONFIRMED",
        confidence=0.90,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score < 0.60
    assert result.decision_category == DECISION_CATEGORY_REMEDIATE


def test_low_risk_not_confirmed_is_defer():
    """
    Lower risk + NOT_CONFIRMED evidence => DEFER.
    low, CVSS 2.0, criticality 0.2, internal, NOT_CONFIRMED => score 0.205.
    """
    finding = _make_finding(
        severity="low",
        cvss=2.0,
        criticality=0.2,
        internet_exposed=False,
        environment="development",
        validation_status="NOT_CONFIRMED",
        confidence=0.0,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score < 0.60
    assert result.evidence_confidence == 0.0
    assert result.decision_category == DECISION_CATEGORY_DEFER


def test_low_risk_inconclusive_is_defer():
    """Lower risk + INCONCLUSIVE evidence => DEFER (uncertain)."""
    finding = _make_finding(
        severity="medium",
        cvss=5.0,
        criticality=0.5,
        internet_exposed=False,
        environment="testing",
        validation_status="INCONCLUSIVE",
        confidence=0.50,
    )
    result = calculate_risk_score(finding)
    assert result.risk_score < 0.60
    assert result.decision_category == DECISION_CATEGORY_DEFER


def test_determine_decision_category_helper():
    """The decision helper returns all four categories as documented."""
    assert (
        determine_decision_category(0.90, 0.95, "CONFIRMED")
        == DECISION_CATEGORY_IMMEDIATE_ACTION
    )
    assert (
        determine_decision_category(0.90, 0.40, "CONFIRMED")
        == DECISION_CATEGORY_VALIDATE_EVIDENCE
    )
    assert (
        determine_decision_category(0.90, 0.95, "INCONCLUSIVE")
        == DECISION_CATEGORY_VALIDATE_EVIDENCE
    )
    assert (
        determine_decision_category(0.40, 0.95, "CONFIRMED")
        == DECISION_CATEGORY_REMEDIATE
    )
    assert (
        determine_decision_category(0.40, 0.0, "NOT_CONFIRMED")
        == DECISION_CATEGORY_DEFER
    )
    assert (
        determine_decision_category(0.40, 0.0, "UNAVAILABLE")
        == DECISION_CATEGORY_DEFER
    )


# ---------------------------------------------------------------------------
# 3. New fields present across all endpoints
# ---------------------------------------------------------------------------


def test_assess_response_contains_new_fields():
    payload = {
        "finding_id": "EVS",
        "title": "Endpoint Field Check",
        "severity": "high",
        "cvss": 8.0,
        "asset": {
            "id": "a1",
            "criticality": 0.8,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.90},
    }
    response = client.post("/assess", json=payload)
    assert response.status_code == 200
    body = response.json()
    for field in ("evidence_confidence", "evidence_status", "decision_category"):
        assert field in body, f"Missing {field} in /assess"
    assert body["evidence_status"] == "CONFIRMED"
    assert body["decision_category"] == "IMMEDIATE_ACTION"


def test_batch_responses_contain_new_fields():
    payload = {
        "findings": [
            {
                "finding_id": "B1",
                "title": "Critical",
                "severity": "critical",
                "cvss": 10.0,
                "asset": {
                    "id": "a",
                    "criticality": 1.0,
                    "internet_exposed": True,
                    "environment": "production",
                },
                "validation": {"status": "CONFIRMED", "confidence": 0.95},
            },
            {
                "finding_id": "B2",
                "title": "Low",
                "severity": "low",
                "cvss": 2.0,
                "asset": {
                    "id": "b",
                    "criticality": 0.2,
                    "internet_exposed": False,
                    "environment": "development",
                },
                "validation": {"status": "NOT_CONFIRMED", "confidence": 0.0},
            },
        ]
    }
    for endpoint in ("/assess/batch", "/assess/batch/sorted"):
        response = client.post(endpoint, json=payload)
        assert response.status_code == 200
        for result in response.json()["results"]:
            for field in (
                "evidence_confidence",
                "evidence_status",
                "decision_category",
            ):
                assert field in result, f"Missing {field} in {endpoint}"

    unsorted = client.post("/assess/batch", json=payload).json()["results"]
    by_id = {r["finding_id"]: r for r in unsorted}
    assert by_id["B1"]["decision_category"] == "IMMEDIATE_ACTION"
    assert by_id["B1"]["evidence_confidence"] == 0.95
    assert by_id["B2"]["decision_category"] == "DEFER"
    assert by_id["B2"]["evidence_confidence"] == 0.0


def test_explain_response_contains_new_fields_and_decision_category():
    payload = {
        "finding_id": "EVX",
        "title": "SQL Injection",
        "severity": "critical",
        "cvss": 9.8,
        "asset": {
            "id": "shop-api",
            "criticality": 1.0,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.95},
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    body = response.json()
    for field in ("evidence_confidence", "evidence_status", "decision_category"):
        assert field in body, f"Missing {field} in /explain"
    assert body["evidence_confidence"] == 0.95
    assert body["evidence_status"] == "CONFIRMED"
    assert body["decision_category"] == "IMMEDIATE_ACTION"
    assert "IMMEDIATE_ACTION" in body["summary"]


# ---------------------------------------------------------------------------
# 4. Backward compatibility
# ---------------------------------------------------------------------------


def test_risk_score_formula_unchanged():
    """The original risk_score values must be identical to before."""
    # F001 from README: critical, CVSS 10, crit 1.0, exposed, prod, conf 0.95
    f001 = _make_finding(
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    result = calculate_risk_score(f001)
    assert result.risk_score == 0.9925
    assert result.factors == {
        "severity": 1.0,
        "asset_criticality": 1.0,
        "exposure": 1.0,
        "validation": 0.95,
    }

    # F002 from README: low, CVSS 2.0, crit 0.2, internal, dev, NOT_CONFIRMED
    f002 = _make_finding(
        severity="low",
        cvss=2.0,
        criticality=0.2,
        internet_exposed=False,
        environment="development",
        validation_status="NOT_CONFIRMED",
        confidence=0.0,
    )
    result = calculate_risk_score(f002)
    assert result.risk_score == 0.205
    assert result.priority == "P4"


def test_priorities_still_p1_to_p4():
    """Every result still carries a valid priority band."""
    for status in ("CONFIRMED", "INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"):
        for severity, cvss in (
            ("critical", 10.0),
            ("high", 8.0),
            ("medium", 5.0),
            ("low", 2.0),
        ):
            finding = _make_finding(
                severity=severity,
                cvss=cvss,
                criticality=0.5,
                validation_status=status,
                confidence=0.7,
            )
            result = calculate_risk_score(finding)
            assert result.priority in ("P1", "P2", "P3", "P4")


def test_unconfirmed_never_described_as_confirmed_in_reasons():
    """
    For NOT_CONFIRMED / UNAVAILABLE evidence, reasons and evidence_confidence
    must never claim confirmation.
    """
    for status in ("NOT_CONFIRMED", "UNAVAILABLE"):
        finding = _make_finding(
            validation_status=status, confidence=0.90,
        )
        result = calculate_risk_score(finding)
        assert result.evidence_confidence == 0.0
        joined = " ".join(result.reasons).lower()
        assert "confirmed with" not in joined
        assert "evidence confirmed" not in joined


def test_priority_result_model_has_new_fields():
    """PriorityResult must serialize all three new fields."""
    finding = _make_finding(
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    result = calculate_risk_score(finding)
    exported = PriorityResult.model_validate(result)
    assert exported.evidence_confidence == 0.95
    assert exported.evidence_status == "CONFIRMED"
    assert exported.decision_category == DECISION_CATEGORY_IMMEDIATE_ACTION