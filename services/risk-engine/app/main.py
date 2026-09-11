from fastapi import FastAPI

from .models import FindingInput, PriorityResult, BatchFindingInput, BatchResult, ExplainResult
from .scoring import calculate_risk_score
from .prioritization import sort_results
from .explanation import build_summary


app = FastAPI(
    title="ACSC Risk Intelligence Engine",
    version="0.1.0",
    description="Risk scoring and prioritization service for the ACSC system.",
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "risk-engine",
        "version": "0.1.0",
    }


@app.post("/assess", response_model=PriorityResult)
def assess_finding(finding: FindingInput) -> PriorityResult:
    return calculate_risk_score(finding)



@app.post("/assess/batch", response_model=BatchResult)
def assess_batch(batch: BatchFindingInput) -> BatchResult:
    results = [calculate_risk_score(finding) for finding in batch.findings]
    return BatchResult(count=len(results), results=results)

@app.post("/assess/batch/sorted", response_model=BatchResult)
def assess_batch_sorted(batch: BatchFindingInput) -> BatchResult:
    results = [calculate_risk_score(finding) for finding in batch.findings]
    sorted_results = sort_results(results)
    return BatchResult(count=len(sorted_results), results=sorted_results)

@app.post("/explain", response_model=ExplainResult)
def explain_finding(finding: FindingInput) -> ExplainResult:
    result = calculate_risk_score(finding)

    return ExplainResult(
        finding_id=result.finding_id,
        title=finding.title,
        risk_score=result.risk_score,
        priority=result.priority,
        reasons=result.reasons,
        factors=result.factors,
        summary=build_summary(finding, result),
    )