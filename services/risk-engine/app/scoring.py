from .models import FindingInput, PriorityResult


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
    return 1.0 if finding.asset.internet_exposed else 0.3


def calculate_validation_factor(finding: FindingInput) -> float:
    if finding.validation.status == "CONFIRMED":
        return finding.validation.confidence

    if finding.validation.status == "INCONCLUSIVE":
        return finding.validation.confidence * 0.5

    if finding.validation.status == "NOT_CONFIRMED":
        return 0.1

    return 0.2


def calculate_risk_score(finding: FindingInput) -> PriorityResult:
    severity_factor = calculate_severity_factor(finding)
    exposure_factor = calculate_exposure_factor(finding)
    validation_factor = calculate_validation_factor(finding)
    asset_factor = finding.asset.criticality

    base_score = (
        0.40 * severity_factor
        + 0.25 * asset_factor
        + 0.20 * exposure_factor
        + 0.15 * validation_factor
    )

    risk_score = round(min(max(base_score, 0.0), 1.0), 4)

    if risk_score >= 0.80:
        priority = "P1"
    elif risk_score >= 0.60:
        priority = "P2"
    elif risk_score >= 0.35:
        priority = "P3"
    else:
        priority = "P4"

    reasons = []

    if finding.severity == "critical":
        reasons.append("Critical severity")

    if finding.cvss is not None and finding.cvss >= 9.0:
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
            "severity": round(severity_factor, 4),
            "asset_criticality": round(asset_factor, 4),
            "exposure": round(exposure_factor, 4),
            "validation": round(validation_factor, 4),
        },
    )