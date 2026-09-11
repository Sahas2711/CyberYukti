from fastapi import FastAPI

from .models import FindingInput, PriorityResult
from .scoring import calculate_risk_score
from .prioritization import sort_results


app = FastAPI(
    title="ACSC Risk Intelligence Engine",
    version="0.1.0",
    description="Risk scoring and prioritization service for the ACSC system.",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "risk-engine",
        "version": "0.1.0",
    }


@app.post("/assess", response_model=PriorityResult)
def assess_finding(finding: FindingInput):
    return calculate_risk_score(finding)


@app.post("/assess/batch", response_model=list[PriorityResult])
def assess_batch(findings: list[FindingInput]):
    return [calculate_risk_score(finding) for finding in findings]

@app.post("/assess/batch/sorted", response_model=list[PriorityResult])
def assess_batch_sorted(findings: list[FindingInput]):
    results = [calculate_risk_score(finding) for finding in findings]
    return sort_results(results)

@app.post("/explain", response_model=dict)
def explain_finding(finding: FindingInput):
    result = calculate_risk_score(finding)

    return {
        "finding_id": result.finding_id,
        "priority": result.priority,
        "risk_score": result.risk_score,
        "summary": (
            f"{result.priority} finding with risk score "
            f"{result.risk_score:.4f}"
        ),
        "reasons": result.reasons,
        "factors": result.factors,
    }