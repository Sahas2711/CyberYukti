from pydantic import BaseModel
from typing import Optional


class Asset(BaseModel):
    asset_id: str
    hostname: str
    environment: str
    internet_exposed: bool
    criticality: str


class Finding(BaseModel):
    finding_id: str
    cluster_id: str
    scanner: str
    scanner_rule_id: Optional[str] = None
    cve: Optional[str] = None
    cwe: Optional[str] = None
    title: str
    description: Optional[str] = None
    asset: Asset
    raw_evidence: Optional[str] = None
    observed_at: str


class Cluster(BaseModel):
    cluster_id: str
    finding_ids: list[str]
    primary_finding_id: str
    dedup_confidence: float
    dedup_method: str


class EvidenceObservation(BaseModel):
    observation_id: str
    type: str
    target: str
    observed_value: str
    expected_value: Optional[str] = None
    method: str


class ValidationResult(BaseModel):
    cluster_id: str
    status: str
    confidence: float
    observations: list[EvidenceObservation]
    validated_at: str
    validator_version: str


class PriorityResult(BaseModel):
    cluster_id: str
    score: float
    level: str
    factors: dict
    formula_version: str


class AIAnalysis(BaseModel):
    summary: str
    why_it_matters: str
    evidence_summary: str
    priority_explanation: str
    investigation_questions: list[str]
    recommended_remediation: list[str]
    confidence_notes: list[str]
    limitations: list[str]
    model: str
    generated_at: str
    grounded_on: list[str]


class ApprovalState(BaseModel):
    status: str = "PENDING"
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    override_priority: Optional[str] = None
    reason: Optional[str] = None


class AuditEvent(BaseModel):
    event_id: str
    case_id: str
    timestamp: str
    actor: str
    actor_id: Optional[str] = None
    action: str
    previous_state: Optional[dict] = None
    new_state: Optional[dict] = None
    metadata: Optional[dict] = None
    prev_hash: Optional[str] = None


class TriageCase(BaseModel):
    case_id: str
    cluster_id: str
    title: str
    asset: Asset
    sources: list[str]
    finding_count: int
    vulnerability: dict
    evidence: ValidationResult
    threat_intelligence: dict
    priority: PriorityResult
    ai_analysis: Optional[AIAnalysis] = None
    approval: ApprovalState = ApprovalState()
    audit: list[AuditEvent] = []
