"""
Explanation builder for the /explain endpoint.

build_summary() constructs a human-readable sentence that accurately
reflects what the scoring engine saw in the finding.  The sentence is
assembled from the original FindingInput so it cannot contradict the
actual input values (e.g. it never says "confirmed" unless the validation
status is CONFIRMED).
"""

from .models import FindingInput, PriorityResult, ExplanationDetail
from .scoring import (
    PRIORITY_P1_THRESHOLD,
    PRIORITY_P2_THRESHOLD,
    PRIORITY_P3_THRESHOLD,
    VERY_HIGH_CVSS_THRESHOLD,
    HIGH_ASSET_CRITICALITY_THRESHOLD,
    SEVERITY_WEIGHT,
    ASSET_CRITICALITY_WEIGHT,
    EXPOSURE_WEIGHT,
    VALIDATION_WEIGHT,
)

# Weight of each scoring factor, used (with the factor value) to decide which
# factor contributed most to the final risk score.
FACTOR_WEIGHTS = {
    "severity": SEVERITY_WEIGHT,
    "asset criticality": ASSET_CRITICALITY_WEIGHT,
    "exposure": EXPOSURE_WEIGHT,
    "validation": VALIDATION_WEIGHT,
}


def build_summary(finding: FindingInput, result: PriorityResult) -> str:
    """
Return a single readable sentence that explains why the finding
    received its priority and risk score.

    Example:
        "Finding F001 received priority P1 with a risk score of 0.9925
         because it has critical severity, affects an internet-exposed
         production asset, its evidence was confirmed with 95% confidence,
         and its decision category is IMMEDIATE_ACTION."
    """
    clauses: list[str] = []

    # --- Severity clause ---
    if finding.cvss is not None:
        clauses.append(f"it has a CVSS score of {finding.cvss}")
    else:
        clauses.append(f"it has {finding.severity} severity")

    # --- Asset / exposure clause ---
    if finding.asset.internet_exposed and finding.asset.environment == "production":
        clauses.append("affects an internet-exposed production asset")
    elif finding.asset.internet_exposed:
        clauses.append("the asset is internet-exposed")
    elif finding.asset.environment == "production":
        clauses.append("the asset is in the production environment")

# --- Validation clause (must be accurate to the actual status) ---
    status = finding.validation.status
    confidence = finding.validation.confidence

    if status == "CONFIRMED":
        clauses.append(
            f"its evidence was confirmed with {confidence:.0%} confidence"
        )
    elif status == "INCONCLUSIVE":
        clauses.append(
            f"its evidence validation was inconclusive "
            f"({confidence:.0%} confidence)"
        )
    elif status == "NOT_CONFIRMED":
        clauses.append("its evidence was not confirmed")
    else:
        clauses.append("validation data was unavailable")

    # --- Decision category clause ---
    clauses.append(f"its decision category is {result.decision_category}")

    # Build the sentence
    if not clauses:
        detail = "no specific high-impact factors were identified"
    elif len(clauses) == 1:
        detail = clauses[0]
    elif len(clauses) == 2:
        detail = f"{clauses[0]} and {clauses[1]}"
    else:
        detail = ", ".join(clauses[:-1]) + f", and {clauses[-1]}"

    return (
        f"Finding {result.finding_id} received priority {result.priority} "
        f"with a risk score of {result.risk_score} "
        f"because {detail}."
    )


def build_key_drivers(finding: FindingInput) -> list[str]:
    """Deterministic list of the drivers behind a finding, derived only from the
    actual input values."""
    drivers: list[str] = []

    if finding.severity == "critical":
        drivers.append("Critical severity")
    elif finding.severity == "high":
        drivers.append("High severity")

    if finding.cvss is not None and finding.cvss >= VERY_HIGH_CVSS_THRESHOLD:
        drivers.append(f"Very high CVSS score ({finding.cvss})")

    if finding.asset.internet_exposed:
        drivers.append("Internet-exposed asset")

    if finding.asset.environment == "production":
        drivers.append("Production environment")

    if finding.asset.criticality >= HIGH_ASSET_CRITICALITY_THRESHOLD:
        drivers.append(f"High asset criticality ({finding.asset.criticality})")

    status = finding.validation.status
    confidence = finding.validation.confidence
    if status == "CONFIRMED":
        drivers.append(f"Evidence confirmed with {confidence:.0%} confidence")
    elif status == "INCONCLUSIVE":
        drivers.append(
            f"Evidence validation was inconclusive "
            f"({confidence:.0%} confidence)"
        )
    elif status == "NOT_CONFIRMED":
        drivers.append("Evidence was not confirmed")
    else:
        drivers.append("Validation data unavailable")

    if not finding.cve:
        drivers.append("No CVE identifier available")

    return drivers


def build_risk_factors(finding: FindingInput) -> list[str]:
    """The risk-side inputs the engine used, verbatim from the finding."""
    factors: list[str] = []

    if finding.cvss is not None:
        factors.append(f"Severity: {finding.severity} (CVSS {finding.cvss})")
    else:
        factors.append(f"Severity: {finding.severity}")

    factors.append(f"Asset criticality: {finding.asset.criticality}")

    exposure = "internet-exposed" if finding.asset.internet_exposed else "internal"
    factors.append(f"Exposure: {exposure}")

    factors.append(f"Environment: {finding.asset.environment}")

    return factors


def build_evidence_factors(
    finding: FindingInput, result: PriorityResult
) -> list[str]:
    """The evidence-side inputs and the computed evidence confidence."""
    status = finding.validation.status
    confidence = finding.validation.confidence

    factors: list[str] = [f"Evidence status: {status}"]

    if status == "CONFIRMED":
        factors.append(f"Evidence confirmed with {confidence:.0%} confidence")
    elif status == "INCONCLUSIVE":
        factors.append(
            f"Evidence validation was inconclusive "
            f"({confidence:.0%} confidence)"
        )
    elif status == "NOT_CONFIRMED":
        factors.append("Evidence was not confirmed")
    else:
        factors.append("Validation data unavailable")

    factors.append(f"Evidence confidence: {result.evidence_confidence}")

    return factors


def build_confidence_warning(finding: FindingInput) -> str | None:
    """A warning surfaced whenever evidence is not confirmed. Returns None only
    when the validation status is exactly CONFIRMED."""
    status = finding.validation.status

    if status == "INCONCLUSIVE":
        return (
            "Inconclusive evidence: treat this finding as uncertain until "
            "further validation."
        )
    if status == "NOT_CONFIRMED":
        return "Evidence was not confirmed: do not treat this finding as validated."
    if status == "UNAVAILABLE":
        return "No validation data available: evidence confidence is treated as 0.0."

    return None


def build_why_this_priority(result: PriorityResult) -> str:
    """A single sentence stating how the assigned priority follows from the
    risk score against the priority thresholds."""
    score = result.risk_score

    if result.priority == "P1":
        return (
            f"P1 was assigned because the risk score ({score}) is at or "
            f"above the P1 threshold ({PRIORITY_P1_THRESHOLD})."
        )
    if result.priority == "P2":
        return (
            f"P2 was assigned because the risk score ({score}) is at or above "
            f"the P2 threshold ({PRIORITY_P2_THRESHOLD}) and below the P1 "
            f"threshold ({PRIORITY_P1_THRESHOLD})."
        )
    if result.priority == "P3":
        return (
            f"P3 was assigned because the risk score ({score}) is at or above "
            f"the P3 threshold ({PRIORITY_P3_THRESHOLD}) and below the P2 "
            f"threshold ({PRIORITY_P2_THRESHOLD})."
        )
    return (
        f"P4 was assigned because the risk score ({score}) is below the P3 "
        f"threshold ({PRIORITY_P3_THRESHOLD})."
    )


def build_priority_basis(result: PriorityResult) -> str:
    """A short, comparison-friendly phrase naming the factor that contributed
    most to the risk score and therefore the assigned priority.

    On a tie the factor with the larger formula weight wins, so the result is
    deterministic."""
    contributions = {
        name: weight * result.factors[factor_key]
        for name, weight, factor_key in (
            ("severity", FACTOR_WEIGHTS["severity"], "severity"),
            (
                "asset criticality",
                FACTOR_WEIGHTS["asset criticality"],
                "asset_criticality",
            ),
            ("exposure", FACTOR_WEIGHTS["exposure"], "exposure"),
            ("validation", FACTOR_WEIGHTS["validation"], "validation"),
        )
    }
    dominant = max(
        contributions,
        key=lambda name: (contributions[name], FACTOR_WEIGHTS[name]),
    )
    return f"{result.priority} priority driven mainly by {dominant}"


def build_explanation(
    finding: FindingInput, result: PriorityResult
) -> ExplanationDetail:
    """Build the full structured explanation for a finding."""
    return ExplanationDetail(
        summary=build_summary(finding, result),
        why_this_priority=build_why_this_priority(result),
        priority_basis=build_priority_basis(result),
        key_drivers=build_key_drivers(finding),
        risk_factors=build_risk_factors(finding),
        evidence_factors=build_evidence_factors(finding, result),
        confidence_warning=build_confidence_warning(finding),
        recommended_next_step=result.recommended_next_step,
    )
