from typing import Literal, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Query

from .models import (
    FindingInput,
    PriorityResult,
    BatchFindingInput,
    BatchResult,
    ExplainResult,
    MatrixClassificationResult,
    WhyFirstResult,
    QueueItem,
    QueueSummary,
    QueueResponse,
    EvidenceProvenance,
    AuditMetadata,
    ReviewPrepareResult,
    ReviewDecisionRequest,
    ReviewDecisionResult,
)
from .scoring import (
    calculate_risk_score,
    DECISION_CATEGORY_IMMEDIATE_ACTION,
    DECISION_CATEGORY_VALIDATE_EVIDENCE,
    DECISION_CATEGORY_REMEDIATE,
    DECISION_CATEGORY_DEFER,
)
from .prioritization import sort_results, sort_results_for_queue
from .explanation import build_summary, build_explanation


QUEUE_CATEGORIES = [
    DECISION_CATEGORY_IMMEDIATE_ACTION,
    DECISION_CATEGORY_VALIDATE_EVIDENCE,
    DECISION_CATEGORY_REMEDIATE,
    DECISION_CATEGORY_DEFER,
]


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


@app.post("/matrix/classify", response_model=MatrixClassificationResult)
def classify_finding(finding: FindingInput) -> MatrixClassificationResult:
    result = calculate_risk_score(finding)

    return MatrixClassificationResult(
        finding_id=result.finding_id,
        risk_score=result.risk_score,
        evidence_confidence=result.evidence_confidence,
        risk_confidence_category=result.risk_confidence_category,
        matrix_label=result.matrix_label,
        recommended_next_step=result.recommended_next_step,
    )


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
        evidence_confidence=result.evidence_confidence,
        evidence_status=result.evidence_status,
        decision_category=result.decision_category,
        risk_confidence_category=result.risk_confidence_category,
        matrix_label=result.matrix_label,
        recommended_next_step=result.recommended_next_step,
        summary=build_summary(finding, result),
    )


@app.post("/explain/why-first", response_model=WhyFirstResult)
def explain_why_first(finding: FindingInput) -> WhyFirstResult:
    result = calculate_risk_score(finding)

    return WhyFirstResult(
        finding_id=result.finding_id,
        title=finding.title,
        risk_score=result.risk_score,
        priority=result.priority,
        evidence_confidence=result.evidence_confidence,
        risk_confidence_category=result.risk_confidence_category,
        explanation=build_explanation(finding, result),
    )


@app.post("/queue", response_model=QueueResponse)
def action_queue(
    batch: BatchFindingInput,
    category: Optional[
        Literal[
            "IMMEDIATE_ACTION", "VALIDATE_EVIDENCE", "REMEDIATE", "DEFER"
        ]
    ] = Query(default=None),
    priority: Optional[Literal["P1", "P2", "P3", "P4"]] = Query(
        default=None
    ),
) -> QueueResponse:
    items = []
    for finding in batch.findings:
        result = calculate_risk_score(finding)
        items.append(
            QueueItem(
                finding_id=result.finding_id,
                title=finding.title,
                risk_score=result.risk_score,
                priority=result.priority,
                evidence_confidence=result.evidence_confidence,
                evidence_status=result.evidence_status,
                risk_confidence_category=result.risk_confidence_category,
                decision_category=result.decision_category,
                reasons=result.reasons,
                recommended_next_step=result.recommended_next_step,
            )
        )

    if category is not None:
        items = [item for item in items if item.decision_category == category]
    if priority is not None:
        items = [item for item in items if item.priority == priority]

    items = sort_results_for_queue(items)

    counts = {category_name: 0 for category_name in QUEUE_CATEGORIES}
    for item in items:
        counts[item.decision_category] += 1

    return QueueResponse(
        count=len(items),
        summary=QueueSummary(total=len(items), categories=counts),
        items=items,
    )


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@app.post("/review/prepare", response_model=ReviewPrepareResult)
def review_prepare(finding: FindingInput) -> ReviewPrepareResult:
    """Prepare a finding for human review.

    This never approves, rejects, or changes any verdict: it only packages the
    finding with provenance and audit metadata and leaves it PENDING_REVIEW.
    The service is stateless, so the preparation record is returned but not
    permanently persisted unless a storage layer is added.
    """
    result = calculate_risk_score(finding)
    now = _now_utc()
    provenance = (
        finding.evidence_provenance
        if finding.evidence_provenance is not None
        else EvidenceProvenance()
    )

    return ReviewPrepareResult(
        finding_id=result.finding_id,
        risk_score=result.risk_score,
        priority=result.priority,
        evidence_confidence=result.evidence_confidence,
        evidence_provenance=provenance,
        audit_metadata=AuditMetadata(
            created_at=now,
            status_changed_at=now,
            action="PREPARED_FOR_REVIEW",
        ),
        review_status="PENDING_REVIEW",
        recommended_next_step=result.recommended_next_step,
    )


@app.post("/review/decision", response_model=ReviewDecisionResult)
def review_decision(request: ReviewDecisionRequest) -> ReviewDecisionResult:
    """Record a human review decision.

    The review status must be one of the supported values; anything else is
    rejected with HTTP 422. Decisions are returned but not permanently
    persisted while the service is stateless — a storage layer is required to
    retain the audit trail across calls.
    """
    now = _now_utc()

    return ReviewDecisionResult(
        finding_id=request.finding_id,
        review_status=request.review_status,
        audit_metadata=AuditMetadata(
            created_at=now,
            status_changed_at=now,
            action="REVIEW_DECISION",
            reviewer=request.reviewer,
            review_note=request.review_note,
        ),
    )