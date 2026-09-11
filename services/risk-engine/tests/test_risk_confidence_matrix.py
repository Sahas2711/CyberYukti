"""
Tests for the risk-confidence classification matrix.

Covers:
1. classify_risk_confidence() returns all four matrix categories with the
   expected matrix label and recommended next step
2. The thresholds are inclusive: risk_score exactly HIGH_RISK_THRESHOLD is
   high risk and evidence_confidence exactly HIGH_CONFIDENCE_THRESHOLD is
   high confidence, while values just below are not
3. Evidence status is part of the classification: INCONCLUSIVE, NOT_CONFIRMED
   and UNAVAILABLE can never be high confidence, even with a numeric value at
   or above the threshold
4. POST /matrix/classify returns exactly the required six fields
   (finding_id, risk_score, evidence_confidence, risk_confidence_category,
   matrix_label, recommended_next_step)
5. Every endpoint (/assess, /assess/batch, /assess/batch/sorted, /explain)
   exposes the three matrix fields
6. The matrix category stays compatible with the existing decision category
   (HIGH_RISK_HIGH_CONFIDENCE <-> IMMEDIATE_ACTION, etc.)
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models import AssetContext, FindingInput, ValidationResult
from app.scoring import (
    classify_risk_confidence,
    HIGH_RISK_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE,
    RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE,
    RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE,
    RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE,
    MATRIX_LABEL_IMMEDIATE_ACTION,
    MATRIX_LABEL_VALIDATE_EVIDENCE,
    MATRIX_LABEL_ROUTINE_REMEDIATION,
    MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE,
    RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE,
    RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE,
    RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT,
    RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(
    finding_id: str,
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
        validation=ValidationResult(
            status=validation_status, confidence=confidence,
        ),
    )


def _post_matrix(payload: dict) -> dict:
    response = client.post("/matrix/classify", json=payload)
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# 1. All four matrix categories
# ---------------------------------------------------------------------------


def test_classify_risk_confidence_all_four_categories():
    """Each combination of high/low risk and high/low confidence maps to the
    expected category with the documented label and next step."""
    cases = [
        (
            (0.90, 0.95, "CONFIRMED"),
            RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE,
            MATRIX_LABEL_IMMEDIATE_ACTION,
            RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE,
        ),
        (
            (0.90, 0.40, "CONFIRMED"),
            RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE,
            MATRIX_LABEL_VALIDATE_EVIDENCE,
            RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE,
        ),
        (
            (0.40, 0.95, "CONFIRMED"),
            RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE,
            MATRIX_LABEL_ROUTINE_REMEDIATION,
            RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT,
        ),
        (
            (0.40, 0.0, "NOT_CONFIRMED"),
            RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE,
            MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE,
            RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW,
        ),
    ]

    for (risk_score, confidence, status), category, label, step in cases:
        assert classify_risk_confidence(risk_score, confidence, status) == (
            category,
            label,
            step,
        )


def test_high_risk_high_confidence_matrix_category():
    """critical / CVSS 10, crit 1.0, exposed, prod, CONFIRMED 0.95 -> score
    0.9925 -> HIGH_RISK_HIGH_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MX01",
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="CONFIRMED",
        confidence=0.95,
    )
    payload = finding.model_dump()
    body = _post_matrix(payload)
    assert body["finding_id"] == "MX01"
    assert body["risk_score"] == 0.9925
    assert body["evidence_confidence"] == 0.95
    assert body == {
        "finding_id": "MX01",
        "risk_score": 0.9925,
        "evidence_confidence": 0.95,
        "risk_confidence_category": RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE,
        "matrix_label": MATRIX_LABEL_IMMEDIATE_ACTION,
        "recommended_next_step": RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE,
    }


def test_high_risk_low_confidence_matrix_category():
    """critical / CVSS 10, crit 1.0, exposed, prod, UNAVAILABLE -> HIGH risk,
    evidence_confidence 0.0 -> HIGH_RISK_LOW_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MX02",
        severity="critical",
        cvss=10.0,
        criticality=1.0,
        internet_exposed=True,
        environment="production",
        validation_status="UNAVAILABLE",
        confidence=0.0,
    )
    body = _post_matrix(finding.model_dump())
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE
    assert body["matrix_label"] == MATRIX_LABEL_VALIDATE_EVIDENCE
    assert body["recommended_next_step"] == RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE


def test_low_risk_high_confidence_matrix_category():
    """cvss 3.0, crit 0.4, internal, dev, CONFIRMED 0.90 -> score 0.415 ->
    LOW_RISK_HIGH_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MX03",
        severity="low",
        cvss=3.0,
        criticality=0.4,
        internet_exposed=False,
        environment="development",
        validation_status="CONFIRMED",
        confidence=0.90,
    )
    body = _post_matrix(finding.model_dump())
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE
    assert body["matrix_label"] == MATRIX_LABEL_ROUTINE_REMEDIATION
    assert (
        body["recommended_next_step"]
        == RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT
    )


def test_low_risk_low_confidence_matrix_category():
    """cvss 2.0, crit 0.2, internal, dev, NOT_CONFIRMED -> score 0.205 ->
    LOW_RISK_LOW_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MX04",
        severity="low",
        cvss=2.0,
        criticality=0.2,
        internet_exposed=False,
        environment="development",
        validation_status="NOT_CONFIRMED",
        confidence=0.0,
    )
    body = _post_matrix(finding.model_dump())
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE
    assert body["matrix_label"] == MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE
    assert body["recommended_next_step"] == RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW


# ---------------------------------------------------------------------------
# 2. Boundary values exactly at the thresholds
# ---------------------------------------------------------------------------


def test_boundary_risk_and_confidence_exactly_at_threshold_is_high():
    """risk_score exactly HIGH_RISK_THRESHOLD and evidence_confidence exactly
    HIGH_CONFIDENCE_THRESHOLD are both HIGH (inclusive thresholds)."""
    assert classify_risk_confidence(
        HIGH_RISK_THRESHOLD,
        HIGH_CONFIDENCE_THRESHOLD,
        "CONFIRMED",
    ) == (
        RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE,
        MATRIX_LABEL_IMMEDIATE_ACTION,
        RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE,
    )


def test_boundary_just_below_risk_threshold_is_low_risk():
    """risk_score just below HIGH_RISK_THRESHOLD must be LOW risk even when
    evidence confidence is high."""
    below = HIGH_RISK_THRESHOLD - 0.0001
    assert classify_risk_confidence(below, HIGH_CONFIDENCE_THRESHOLD, "CONFIRMED") == (
        RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE,
        MATRIX_LABEL_ROUTINE_REMEDIATION,
        RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT,
    )


def test_boundary_just_below_confidence_threshold_is_low_confidence():
    """evidence_confidence just below HIGH_CONFIDENCE_THRESHOLD must be LOW
    confidence even when risk is high."""
    below = HIGH_CONFIDENCE_THRESHOLD - 0.0001
    assert classify_risk_confidence(HIGH_RISK_THRESHOLD, below, "CONFIRMED") == (
        RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE,
        MATRIX_LABEL_VALIDATE_EVIDENCE,
        RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE,
    )


def test_boundary_both_just_below_thresholds_is_low_low():
    below_risk = HIGH_RISK_THRESHOLD - 0.0001
    below_confidence = HIGH_CONFIDENCE_THRESHOLD - 0.0001
    assert classify_risk_confidence(
        below_risk, below_confidence, "CONFIRMED",
    ) == (
        RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE,
        MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE,
        RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW,
    )


def test_endpoint_boundary_risk_exactly_at_threshold():
    """cvss 8.0, crit 0.2, exposed, UNAVAILABLE -> risk_score exactly 0.60
    (HIGH_RISK_THRESHOLD) -> HIGH_RISK_LOW_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MXB1",
        severity="high",
        cvss=8.0,
        criticality=0.2,
        internet_exposed=True,
        environment="staging",
        validation_status="UNAVAILABLE",
        confidence=0.0,
    )
    body = _post_matrix(finding.model_dump())
    assert body["risk_score"] == HIGH_RISK_THRESHOLD
    assert body["evidence_confidence"] == 0.0
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE


def test_endpoint_boundary_confidence_exactly_at_threshold():
    """cvss 5.0, crit 0.3, internal, CONFIRMED 0.70 -> evidence_confidence
    exactly HIGH_CONFIDENCE_THRESHOLD with low risk ->
    LOW_RISK_HIGH_CONFIDENCE."""
    finding = _make_finding(
        finding_id="MXB2",
        severity="medium",
        cvss=5.0,
        criticality=0.3,
        internet_exposed=False,
        environment="testing",
        validation_status="CONFIRMED",
        confidence=0.70,
    )
    body = _post_matrix(finding.model_dump())
    assert body["evidence_confidence"] == HIGH_CONFIDENCE_THRESHOLD
    assert body["risk_score"] < HIGH_RISK_THRESHOLD
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE


# ---------------------------------------------------------------------------
# 3. Evidence status gates high confidence
# ---------------------------------------------------------------------------


def test_status_gates_confidence_even_at_threshold():
    """INCONCLUSIVE, NOT_CONFIRMED and UNAVAILABLE evidence is never high
    confidence, even when the numeric confidence equals the threshold."""
    for status in ("INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"):
        category, _, _ = classify_risk_confidence(
            HIGH_RISK_THRESHOLD,
            HIGH_CONFIDENCE_THRESHOLD,
            status,
        )
        assert category == RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE, status


def test_inconclusive_high_numeric_confidence_is_never_high_confidence():
    """INCONCLUSIVE evidence preserves the numeric confidence but stays in the
    LOW confidence column of the matrix."""
    finding = _make_finding(
        finding_id="MX05",
        severity="high",
        cvss=8.0,
        criticality=0.9,
        internet_exposed=True,
        environment="production",
        validation_status="INCONCLUSIVE",
        confidence=0.80,
    )
    body = _post_matrix(finding.model_dump())
    assert body["evidence_confidence"] == 0.80
    assert body["risk_confidence_category"] == RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE


# ---------------------------------------------------------------------------
# 4. POST /matrix/classify returns exactly the required fields
# ---------------------------------------------------------------------------


def test_matrix_classify_response_contains_only_required_fields():
    payload = {
        "finding_id": "MXF",
        "title": "Matrix Field Check",
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
    body = _post_matrix(payload)
    assert set(body.keys()) == {
        "finding_id",
        "risk_score",
        "evidence_confidence",
        "risk_confidence_category",
        "matrix_label",
        "recommended_next_step",
    }


# ---------------------------------------------------------------------------
# 5. Matrix fields exposed across all other endpoints
# ---------------------------------------------------------------------------

MATRIX_FIELDS = (
    "risk_confidence_category",
    "matrix_label",
    "recommended_next_step",
)


def _matrix_payload() -> dict:
    return {
        "findings": [
            {
                "finding_id": "M1",
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
                "finding_id": "M2",
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


def test_assess_exposes_matrix_fields():
    payload = _matrix_payload()["findings"][0]
    response = client.post("/assess", json=payload)
    assert response.status_code == 200
    body = response.json()
    for field in MATRIX_FIELDS:
        assert field in body, f"Missing {field} in /assess"


def test_batch_endpoints_expose_matrix_fields():
    payload = _matrix_payload()
    for endpoint in ("/assess/batch", "/assess/batch/sorted"):
        response = client.post(endpoint, json=payload)
        assert response.status_code == 200
        for result in response.json()["results"]:
            for field in MATRIX_FIELDS:
                assert field in result, f"Missing {field} in {endpoint}"


def test_explain_exposes_matrix_fields():
    payload = _matrix_payload()["findings"][0]
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    body = response.json()
    for field in MATRIX_FIELDS:
        assert field in body, f"Missing {field} in /explain"


# ---------------------------------------------------------------------------
# 6. Compatibility with the existing decision categories
# ---------------------------------------------------------------------------


def test_matrix_category_matches_decision_category():
    """The matrix category must be compatible with decision_category:
    HIGH_RISK_HIGH_CONFIDENCE <-> IMMEDIATE_ACTION,
    HIGH_RISK_LOW_CONFIDENCE <-> VALIDATE_EVIDENCE,
    LOW_RISK_HIGH_CONFIDENCE <-> REMEDIATE,
    LOW_RISK_LOW_CONFIDENCE <-> DEFER."""
    expected = {
        ("0.9925", "0.95", "CONFIRMED"): (
            "IMMEDIATE_ACTION",
            RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE,
        ),
        ("0.88", "0.0", "UNAVAILABLE"): (
            "VALIDATE_EVIDENCE",
            RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE,
        ),
        ("0.415", "0.9", "CONFIRMED"): (
            "REMEDIATE",
            RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE,
        ),
        ("0.205", "0.0", "NOT_CONFIRMED"): (
            "DEFER",
            RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE,
        ),
    }

    scenarios = {
        "0.9925": _make_finding(
            finding_id="c1",
            severity="critical",
            cvss=10.0,
            criticality=1.0,
            internet_exposed=True,
            environment="production",
            validation_status="CONFIRMED",
            confidence=0.95,
        ),
        "0.88": _make_finding(
            finding_id="c2",
            severity="critical",
            cvss=10.0,
            criticality=1.0,
            internet_exposed=True,
            environment="production",
            validation_status="UNAVAILABLE",
            confidence=0.0,
        ),
        "0.415": _make_finding(
            finding_id="c3",
            severity="low",
            cvss=3.0,
            criticality=0.4,
            internet_exposed=False,
            environment="development",
            validation_status="CONFIRMED",
            confidence=0.90,
        ),
        "0.205": _make_finding(
            finding_id="c4",
            severity="low",
            cvss=2.0,
            criticality=0.2,
            internet_exposed=False,
            environment="development",
            validation_status="NOT_CONFIRMED",
            confidence=0.0,
        ),
    }

    for score, finding in scenarios.items():
        payload = finding.model_dump()
        body = client.post("/assess", json=payload).json()
        key = (
            str(body["risk_score"]),
            str(body["evidence_confidence"]),
            body["evidence_status"],
        )
        assert key in expected
        expected_decision, expected_category = expected[key]
        assert body["decision_category"] == expected_decision
        assert body["risk_confidence_category"] == expected_category