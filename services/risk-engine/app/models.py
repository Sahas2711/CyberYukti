from typing import Literal, Optional
from pydantic import BaseModel, Field


class AssetContext(BaseModel):
    id: str
    criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    internet_exposed: bool = False
    environment: Literal[
        "development", "testing", "staging", "production", "unknown"
    ] = "unknown"


class ValidationResult(BaseModel):
    status: Literal[
        "CONFIRMED", "INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"
    ] = "UNAVAILABLE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FindingInput(BaseModel):
    finding_id: str
    cluster_id: Optional[str] = None
    title: str
    severity: Literal[
        "critical", "high", "medium", "low", "informational", "unknown"
    ] = "unknown"
    cve: Optional[str] = None
    cvss: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    asset: AssetContext
    validation: ValidationResult = ValidationResult()


class PriorityResult(BaseModel):
    finding_id: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    reasons: list[str]
    factors: dict[str, float]