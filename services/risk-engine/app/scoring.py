from .models import FindingInput, PriorityResult

# ---------------------------------------------------------------------------
# Risk score formula weights
# ---------------------------------------------------------------------------
SEVERITY_WEIGHT = 0.40
ASSET_CRITICALITY_WEIGHT = 0.25
EXPOSURE_WEIGHT = 0.20
VALIDATION_WEIGHT = 0.15

# ---------------------------------------------------------------------------
# Priority thresholds
# ---------------------------------------------------------------------------
PRIORITY_P1_THRESHOLD = 0.80
PRIORITY_P2_THRESHOLD = 0.60
PRIORITY_P3_THRESHOLD = 0.35

# ---------------------------------------------------------------------------
# Evidence confidence & decision category thresholds
# ---------------------------------------------------------------------------
# A finding counts as "high risk" when it sits at or above the P2 threshold.
HIGH_RISK_THRESHOLD = PRIORITY_P2_THRESHOLD
# Evidence is only treated as strongly reliable when the validation status is
# CONFIRMED and the reported confidence is at least this value.
HIGH_CONFIDENCE_THRESHOLD = 0.70

DECISION_CATEGORY_IMMEDIATE_ACTION = "IMMEDIATE_ACTION"
DECISION_CATEGORY_VALIDATE_EVIDENCE = "VALIDATE_EVIDENCE"
DECISION_CATEGORY_REMEDIATE = "REMEDIATE"
DECISION_CATEGORY_DEFER = "DEFER"

# ---------------------------------------------------------------------------
# Risk-confidence classification matrix
# ---------------------------------------------------------------------------
# The matrix combines the risk band (>= HIGH_RISK_THRESHOLD is high risk) with
# evidence confidence to give a deterministic category, a human-readable label,
# and a recommended (safe, non-exploitative) next step.
RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE = "HIGH_RISK_HIGH_CONFIDENCE"
RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE = "HIGH_RISK_LOW_CONFIDENCE"
RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE = "LOW_RISK_HIGH_CONFIDENCE"
RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE = "LOW_RISK_LOW_CONFIDENCE"

MATRIX_LABEL_IMMEDIATE_ACTION = "Immediate action"
MATRIX_LABEL_VALIDATE_EVIDENCE = "Validate evidence"
MATRIX_LABEL_ROUTINE_REMEDIATION = "Routine remediation"
MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE = "Defer and collect evidence"

RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE = "Review and remediate"
RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE = "Collect additional evidence"
RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT = (
    "Validate asset and finding context"
)
RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW = "Defer for later review"

# Risk-confidence category -> (matrix label, recommended next step)
MATRIX_METADATA = {
    RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE: (
        MATRIX_LABEL_IMMEDIATE_ACTION,
        RECOMMENDED_NEXT_STEP_REVIEW_AND_REMEDIATE,
    ),
    RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE: (
        MATRIX_LABEL_VALIDATE_EVIDENCE,
        RECOMMENDED_NEXT_STEP_COLLECT_ADDITIONAL_EVIDENCE,
    ),
    RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE: (
        MATRIX_LABEL_ROUTINE_REMEDIATION,
        RECOMMENDED_NEXT_STEP_VALIDATE_ASSET_AND_FINDING_CONTEXT,
    ),
    RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE: (
        MATRIX_LABEL_DEFER_AND_COLLECT_EVIDENCE,
        RECOMMENDED_NEXT_STEP_DEFER_FOR_LATER_REVIEW,
    ),
}

# ---------------------------------------------------------------------------
# Supporting constants
# ---------------------------------------------------------------------------
SCORE_PRECISION = 4
INCONCLUSIVE_CONFIDENCE_MULTIPLIER = 0.5
NOT_CONFIRMED_VALIDATION_FACTOR = 0.1
UNAVAILABLE_VALIDATION_FACTOR = 0.2
INTERNET_EXPOSED_FACTOR = 1.0
INTERNAL_EXPOSURE_FACTOR = 0.3
# A CVSS at or above this value is described as "very high".
VERY_HIGH_CVSS_THRESHOLD = 9.0
# Asset criticality at or above this value is described as "high".
HIGH_ASSET_CRITICALITY_THRESHOLD = 0.7

SEVERITY_FACTORS = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
    "informational": 0.05,
    "unknown": 0.3,
}


def calculate_severity_factor(finding: FindingInput) -> float:
    if finding.cvss is not None:
        return finding.cvss / 10.0

    return SEVERITY_FACTORS.get(finding.severity, 0.3)


def calculate_exposure_factor(finding: FindingInput) -> float:
    if finding.asset.internet_exposed:
        return INTERNET_EXPOSED_FACTOR

    return INTERNAL_EXPOSURE_FACTOR


def calculate_validation_factor(finding: FindingInput) -> float:
    """Risk-scoring contribution of the validation result (unchanged)."""
    status = finding.validation.status
    confidence = finding.validation.confidence

    if status == "CONFIRMED":
        return confidence

    if status == "INCONCLUSIVE":
        return confidence * INCONCLUSIVE_CONFIDENCE_MULTIPLIER

    if status == "NOT_CONFIRMED":
        return NOT_CONFIRMED_VALIDATION_FACTOR

    return UNAVAILABLE_VALIDATION_FACTOR


def calculate_evidence_confidence(finding: FindingInput) -> float:
    """
    Evidence confidence is calculated separately from the risk score.

    * CONFIRMED     -> the reported confidence is used directly.
    * INCONCLUSIVE  -> the numeric confidence is preserved, but the finding
                       remains INCONCLUSIVE; the status is never upgraded.
    * NOT_CONFIRMED -> 0.0; unconfirmed evidence is not treated as confirmed.
    * UNAVAILABLE   -> 0.0; no validation data means no evidence confidence.
    """
    status = finding.validation.status

    if status in ("CONFIRMED", "INCONCLUSIVE"):
        confidence = min(max(finding.validation.confidence, 0.0), 1.0)
        return round(confidence, SCORE_PRECISION)

    return 0.0


def is_high_confidence_evidence(
    evidence_confidence: float,
    evidence_status: str,
) -> bool:
    """Evidence is only treated as strongly reliable when the validation status
    is CONFIRMED and the reported confidence reaches HIGH_CONFIDENCE_THRESHOLD.
    INCONCLUSIVE, NOT_CONFIRMED, and UNAVAILABLE evidence is never high
    confidence, regardless of any numeric confidence supplied."""
    return (
        evidence_status == "CONFIRMED"
        and evidence_confidence >= HIGH_CONFIDENCE_THRESHOLD
    )


def determine_decision_category(
    risk_score: float,
    evidence_confidence: float,
    evidence_status: str,
) -> str:
    """Map combined risk and evidence confidence to a decision category:

    * High risk + confident evidence        -> IMMEDIATE_ACTION
    * High risk + low / uncertain evidence  -> VALIDATE_EVIDENCE
    * Lower risk + confident evidence       -> REMEDIATE
    * Lower risk + low / uncertain evidence -> DEFER
    """
    high_risk = risk_score >= HIGH_RISK_THRESHOLD
    confident_evidence = is_high_confidence_evidence(
        evidence_confidence=evidence_confidence,
        evidence_status=evidence_status,
    )

    if high_risk and confident_evidence:
        return DECISION_CATEGORY_IMMEDIATE_ACTION

    if high_risk:
        return DECISION_CATEGORY_VALIDATE_EVIDENCE

    if confident_evidence:
        return DECISION_CATEGORY_REMEDIATE

    return DECISION_CATEGORY_DEFER


def classify_risk_confidence(
    risk_score: float,
    evidence_confidence: float,
    evidence_status: str,
) -> tuple[str, str, str]:
    """
    Classify a finding into the risk-confidence matrix.

    Returns (risk_confidence_category, matrix_label, recommended_next_step).

    The classification is deterministic: it is a pure function of risk_score,
    evidence_confidence, and evidence_status, and reuses the same thresholds as
    the risk score and decision category logic (HIGH_RISK_THRESHOLD and
    HIGH_CONFIDENCE_THRESHOLD, with the CONFIRMED-only high-confidence rule), so
    it stays compatible with the existing IMMEDIATE_ACTION / VALIDATE_EVIDENCE /
    REMEDIATE / DEFER decision categories.
    """
    high_risk = risk_score >= HIGH_RISK_THRESHOLD
    high_confidence = is_high_confidence_evidence(
        evidence_confidence=evidence_confidence,
        evidence_status=evidence_status,
    )

    if high_risk and high_confidence:
        category = RISK_CONFIDENCE_CATEGORY_HIGH_RISK_HIGH_CONFIDENCE
    elif high_risk:
        category = RISK_CONFIDENCE_CATEGORY_HIGH_RISK_LOW_CONFIDENCE
    elif high_confidence:
        category = RISK_CONFIDENCE_CATEGORY_LOW_RISK_HIGH_CONFIDENCE
    else:
        category = RISK_CONFIDENCE_CATEGORY_LOW_RISK_LOW_CONFIDENCE

    matrix_label, recommended_next_step = MATRIX_METADATA[category]
    return category, matrix_label, recommended_next_step


def calculate_risk_score(finding: FindingInput) -> PriorityResult:
    severity_factor = calculate_severity_factor(finding)
    exposure_factor = calculate_exposure_factor(finding)
    validation_factor = calculate_validation_factor(finding)
    asset_factor = finding.asset.criticality

    base_score = (
        SEVERITY_WEIGHT * severity_factor
        + ASSET_CRITICALITY_WEIGHT * asset_factor
        + EXPOSURE_WEIGHT * exposure_factor
        + VALIDATION_WEIGHT * validation_factor
    )

    risk_score = round(min(max(base_score, 0.0), 1.0), SCORE_PRECISION)

    if risk_score >= PRIORITY_P1_THRESHOLD:
        priority = "P1"
    elif risk_score >= PRIORITY_P2_THRESHOLD:
        priority = "P2"
    elif risk_score >= PRIORITY_P3_THRESHOLD:
        priority = "P3"
    else:
        priority = "P4"

    evidence_confidence = calculate_evidence_confidence(finding)
    evidence_status = finding.validation.status
    decision_category = determine_decision_category(
        risk_score=risk_score,
        evidence_confidence=evidence_confidence,
        evidence_status=evidence_status,
    )
    risk_confidence_category, matrix_label, recommended_next_step = (
        classify_risk_confidence(
            risk_score=risk_score,
            evidence_confidence=evidence_confidence,
            evidence_status=evidence_status,
        )
    )

    reasons = []

    if finding.severity == "critical":
        reasons.append("Critical severity")

    if finding.cvss is not None and finding.cvss >= VERY_HIGH_CVSS_THRESHOLD:
        reasons.append("Very high CVSS score")

    if finding.asset.internet_exposed:
        reasons.append("Internet-exposed asset")

    if finding.asset.environment == "production":
        reasons.append("Production environment")

    if finding.validation.status == "CONFIRMED":
        reasons.append(
            f"Evidence confirmed with "
            f"{finding.validation.confidence:.0%} confidence"
        )
    elif finding.validation.status == "NOT_CONFIRMED":
        reasons.append("Evidence was not confirmed")
    elif finding.validation.status == "INCONCLUSIVE":
        reasons.append("Evidence validation was inconclusive")
    else:
        reasons.append("Evidence validation unavailable")

    if not finding.cve:
        reasons.append("No CVE identifier available")

    return PriorityResult(
        finding_id=finding.finding_id,
        risk_score=risk_score,
        priority=priority,
        reasons=reasons,
        factors={
            "severity": round(severity_factor, SCORE_PRECISION),
            "asset_criticality": round(asset_factor, SCORE_PRECISION),
            "exposure": round(exposure_factor, SCORE_PRECISION),
            "validation": round(validation_factor, SCORE_PRECISION),
        },
        evidence_confidence=evidence_confidence,
        evidence_status=evidence_status,
        decision_category=decision_category,
        risk_confidence_category=risk_confidence_category,
        matrix_label=matrix_label,
        recommended_next_step=recommended_next_step,
    )