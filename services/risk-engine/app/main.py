from fastapi import FastAPI

from .models import FindingInput, PriorityResult
from .scoring import calculate_risk_score


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