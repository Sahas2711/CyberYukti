from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


VALIDATION_STATUS = Literal[
    "CONFIRMED", "INCONCLUSIVE", "NOT_CONFIRMED", "UNAVAILABLE"
]
DECISION_CATEGORY = Literal[
    "IMMEDIATE_ACTION", "VALIDATE_EVIDENCE", "REMEDIATE", "DEFER"
]
RISK_CONFIDENCE_CATEGORY = Literal[
    "HIGH_RISK_HIGH_CONFIDENCE",
    "HIGH_RISK_LOW_CONFIDENCE",
    "LOW_RISK_HIGH_CONFIDENCE",
    "LOW_RISK_LOW_CONFIDENCE",
]
MATRIX_LABEL = Literal[
    "Immediate action",
    "Validate evidence",
    "Routine remediation",
    "Defer and collect evidence",
]
RECOMMENDED_NEXT_STEP = Literal[
    "Review and remediate",
    "Collect additional evidence",
    "Validate asset and finding context",
    "Defer for later review",
]
REVIEW_STATUS = Literal[
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    "NEEDS_MORE_EVIDENCE",
    "DEFERRED",
    "RESOLVED",
]

# High-confidence markers for credentials or secrets that must never enter the
# system. Free-text provenance and review fields are rejected when they match.
SENSITIVE_PATTERNS = [
    "-----begin",
    "begin private key",
    "begin rsa private key",
    "begin openssh private key",
    "begin pgp private key",
    "authorization: bearer",
    "bearer ",
    "password=",
    "secret=",
    "token=",
    "client_secret",
    "api_key",
    "github_pat_",
    "ghp_",
]


def reject_sensitive_content(value: str) -> str:
    """Reject obvious secrets, credentials, or tokens in free-text fields."""
    lowered = value.lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern in lowered:
            raise ValueError(
                "value may contain a secret, credential, or token and is "
                "not accepted"
            )
    return value


class AssetContext(BaseModel):
    id: str
    criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    internet_exposed: bool = False
    environment: Literal[
        "development", "testing", "staging", "production", "unknown"
    ] = "unknown"


class ValidationResult(BaseModel):
    status: VALIDATION_STATUS = "UNAVAILABLE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class EvidenceProvenance(BaseModel):
    """Non-sensitive metadata about where a finding came from."""

    source: str = Field(default="", max_length=100)
    source_type: Literal[
        "SCANNER", "MANUAL", "OSINT", "EXTERNAL", "UNKNOWN"
    ] = "UNKNOWN"
    observed_at: Optional[datetime] = None
    validation_method: str = Field(default="", max_length=150)
    evidence_reference: str = Field(default="", max_length=250)

    @field_validator("source", "validation_method", "evidence_reference")
    @classmethod
    def _no_sensitive_content(cls, value: str) -> str:
        return reject_sensitive_content(value)


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
    evidence_provenance: Optional[EvidenceProvenance] = None


class PriorityResult(BaseModel):
    finding_id: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    reasons: list[str]
    factors: dict[str, float]
    evidence_confidence: float
    evidence_status: VALIDATION_STATUS
    decision_category: DECISION_CATEGORY
    risk_confidence_category: RISK_CONFIDENCE_CATEGORY
    matrix_label: MATRIX_LABEL
    recommended_next_step: RECOMMENDED_NEXT_STEP


class BatchFindingInput(BaseModel):
    findings: list[FindingInput]


class BatchResult(BaseModel):
    count: int
    results: list[PriorityResult]


class ExplainResult(BaseModel):
    finding_id: str
    title: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    reasons: list[str]
    factors: dict[str, float]
    evidence_confidence: float
    evidence_status: VALIDATION_STATUS
    decision_category: DECISION_CATEGORY
    risk_confidence_category: RISK_CONFIDENCE_CATEGORY
    matrix_label: MATRIX_LABEL
    recommended_next_step: RECOMMENDED_NEXT_STEP
    summary: str


class MatrixClassificationResult(BaseModel):
    finding_id: str
    risk_score: float
    evidence_confidence: float
    risk_confidence_category: RISK_CONFIDENCE_CATEGORY
    matrix_label: MATRIX_LABEL
    recommended_next_step: RECOMMENDED_NEXT_STEP


class ExplanationDetail(BaseModel):
    summary: str
    why_this_priority: str
    priority_basis: str
    key_drivers: list[str]
    risk_factors: list[str]
    evidence_factors: list[str]
    confidence_warning: Optional[str] = None
    recommended_next_step: str


class WhyFirstResult(BaseModel):
    finding_id: str
    title: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    evidence_confidence: float
    risk_confidence_category: RISK_CONFIDENCE_CATEGORY
    explanation: ExplanationDetail


class QueueItem(BaseModel):
    finding_id: str
    title: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    evidence_confidence: float
    evidence_status: VALIDATION_STATUS
    risk_confidence_category: RISK_CONFIDENCE_CATEGORY
    decision_category: DECISION_CATEGORY
    reasons: list[str]
    recommended_next_step: RECOMMENDED_NEXT_STEP


class QueueSummary(BaseModel):
    total: int
    categories: dict[str, int]


class QueueResponse(BaseModel):
    count: int
    summary: QueueSummary
    items: list[QueueItem]


class AuditMetadata(BaseModel):
    created_at: datetime
    status_changed_at: datetime
    action: str
    reviewer: Optional[str] = None
    review_note: Optional[str] = None


class ReviewPrepareResult(BaseModel):
    finding_id: str
    risk_score: float
    priority: Literal["P1", "P2", "P3", "P4"]
    evidence_confidence: float
    evidence_provenance: EvidenceProvenance
    audit_metadata: AuditMetadata
    review_status: REVIEW_STATUS
    recommended_next_step: RECOMMENDED_NEXT_STEP


class ReviewDecisionRequest(BaseModel):
    finding_id: str = Field(min_length=1, max_length=100)
    review_status: REVIEW_STATUS
    reviewer: str = Field(min_length=1, max_length=50)
    review_note: Optional[str] = Field(default=None, max_length=500)

    @field_validator("reviewer", "review_note")
    @classmethod
    def _no_sensitive_content(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return reject_sensitive_content(value)


class ReviewDecisionResult(BaseModel):
    finding_id: str
    review_status: REVIEW_STATUS
    audit_metadata: AuditMetadata