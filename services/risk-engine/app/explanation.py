"""
Explanation builder for the /explain endpoint.

build_summary() constructs a human-readable sentence that accurately
reflects what the scoring engine saw in the finding.  The sentence is
assembled from the original FindingInput so it cannot contradict the
actual input values (e.g. it never says "confirmed" unless the validation
status is CONFIRMED).
"""

from .models import FindingInput, PriorityResult


def build_summary(finding: FindingInput, result: PriorityResult) -> str:
    """
    Return a single readable sentence that explains why the finding
    received its priority and risk score.

    Example:
        "Finding F001 received priority P1 with a risk score of 0.9925
         because it has critical severity, affects an internet-exposed
         production asset, and its evidence was confirmed with 95% confidence."
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
