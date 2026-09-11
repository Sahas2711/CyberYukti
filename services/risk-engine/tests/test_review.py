"""
Tests for evidence provenance and the human-in-the-loop review workflow.

Covers:
1. Default PENDING_REVIEW status
2. Provenance validation (source type, timestamp, lengths, secrets)
3. Review preparation (required fields, scoring consistency)
4. Valid review decisions (all supported statuses)
5. Invalid review status
6. Accurate audit metadata
7. Statelessness: prepare never automatically approves or rejects
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

SUPPORTED_REVIEW_STATUSES = [
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    "NEEDS_MORE_EVIDENCE",
    "DEFERRED",
    "RESOLVED",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(
    finding_id: str = "RV001",
    severity: str = "critical",
    cvss: float | None = 10.0,
    criticality: float = 1.0,
    internet_exposed: bool = True,
    environment: str = "production",
    validation_status: str = "CONFIRMED",
    confidence: float = 0.95,
    provenance: dict | None = None,
) -> dict:
    payload = {
        "finding_id": finding_id,
        "title": f"Finding {finding_id}",
        "severity": severity,
        "cvss": cvss,
        "asset": {
            "id": f"asset-{finding_id}",
            "criticality": criticality,
            "internet_exposed": internet_exposed,
            "environment": environment,
        },
        "validation": {"status": validation_status, "confidence": confidence},
    }
    if provenance is not None:
        payload["evidence_provenance"] = provenance
    return payload


def _valid_provenance() -> dict:
    return {
        "source": "tenable-scanner-01",
        "source_type": "SCANNER",
        "observed_at": "2026-09-10T08:15:30Z",
        "validation_method": "static-analysis + manual review",
        "evidence_reference": "report-2026-09-10-0042",
    }


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _post_prepare(payload: dict) -> dict:
    response = client.post("/review/prepare", json=payload)
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# Default pending review status
# ---------------------------------------------------------------------------

def test_prepare_defaults_to_pending_review() -> None:
    body = _post_prepare(_payload())
    assert body["review_status"] == "PENDING_REVIEW"
    assert body["audit_metadata"]["action"] == "PREPARED_FOR_REVIEW"
    assert body["finding_id"] == "RV001"


def test_prepare_is_never_an_automatic_approval() -> None:
    for severity, confidence in (
        ("critical", 1.0),
        ("high", 0.85),
        ("medium", 0.5),
    ):
        body = _post_prepare(_payload(severity=severity, confidence=confidence))
        assert body["review_status"] == "PENDING_REVIEW"


def test_prepare_without_provenance_returns_defaults() -> None:
    body = _post_prepare(_payload())
    prov = body["evidence_provenance"]
    assert prov["source_type"] == "UNKNOWN"
    assert prov["source"] == ""
    assert prov["validation_method"] == ""
    assert prov["evidence_reference"] == ""
    assert prov["observed_at"] is None


# ---------------------------------------------------------------------------
# Provenance validation
# ---------------------------------------------------------------------------

def test_valid_provenance_is_accepted_and_returned() -> None:
    provenance = _valid_provenance()
    body = _post_prepare(_payload(provenance=provenance))
    assert body["evidence_provenance"] == provenance


def test_invalid_source_type_is_rejected() -> None:
    provenance = _valid_provenance()
    provenance["source_type"] = "DARKWEB_CREDENTIALS"
    response = client.post(
        "/review/prepare", json=_payload(provenance=provenance)
    )
    assert response.status_code == 422


def test_invalid_timestamp_is_rejected() -> None:
    provenance = _valid_provenance()
    provenance["observed_at"] = "not-a-timestamp"
    response = client.post(
        "/review/prepare", json=_payload(provenance=provenance)
    )
    assert response.status_code == 422


def test_overlong_provenance_source_is_rejected() -> None:
    provenance = _valid_provenance()
    provenance["source"] = "x" * 500
    response = client.post(
        "/review/prepare", json=_payload(provenance=provenance)
    )
    assert response.status_code == 422


def test_secret_like_content_in_provenance_is_rejected() -> None:
    provenance = _valid_provenance()
    provenance["source"] = "scanner using token=supersecretvalue"
    response = client.post(
        "/review/prepare", json=_payload(provenance=provenance)
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Review preparation
# ---------------------------------------------------------------------------

def test_prepare_returns_required_fields() -> None:
    body = _post_prepare(_payload())
    expected = {
        "finding_id",
        "risk_score",
        "priority",
        "evidence_confidence",
        "evidence_provenance",
        "audit_metadata",
        "review_status",
        "recommended_next_step",
    }
    assert set(body.keys()) == expected


def test_prepare_matches_assess_scoring_and_next_step() -> None:
    body = _post_prepare(_payload())
    scored = client.post("/assess", json=_payload()).json()
    assert body["risk_score"] == scored["risk_score"]
    assert body["priority"] == scored["priority"]
    assert body["evidence_confidence"] == scored["evidence_confidence"]
    assert body["recommended_next_step"] == scored["recommended_next_step"]


# ---------------------------------------------------------------------------
# Valid review decisions
# ---------------------------------------------------------------------------

def test_all_supported_review_statuses_accepted() -> None:
    for status in SUPPORTED_REVIEW_STATUSES:
        response = client.post(
            "/review/decision",
            json={
                "finding_id": "RV001",
                "review_status": status,
                "reviewer": "analyst-alice",
                "review_note": f"Marked as {status} after triage.",
            },
        )
        assert response.status_code == 200, status
        body = response.json()
        assert body["review_status"] == status
        assert body["finding_id"] == "RV001"
        assert body["audit_metadata"]["reviewer"] == "analyst-alice"


def test_decision_without_note_is_allowed() -> None:
    response = client.post(
        "/review/decision",
        json={
            "finding_id": "RV002",
            "review_status": "APPROVED",
            "reviewer": "analyst-bob",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["audit_metadata"]["review_note"] is None


def test_secret_like_reviewer_or_note_is_rejected() -> None:
    for bad_field in ("reviewer", "review_note"):
        request = {
            "finding_id": "RV003",
            "review_status": "APPROVED",
            "reviewer": "analyst-carla",
        }
        request[bad_field] = "rotate password=supersecret now"
        response = client.post("/review/decision", json=request)
        assert response.status_code == 422, bad_field


# ---------------------------------------------------------------------------
# Invalid review status
# ---------------------------------------------------------------------------

def test_invalid_review_status_is_rejected() -> None:
    response = client.post(
        "/review/decision",
        json={
            "finding_id": "RV001",
            "review_status": "AUTO_APPROVE",
            "reviewer": "analyst-alice",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Accurate audit metadata
# ---------------------------------------------------------------------------

def test_prepare_audit_metadata_is_accurate() -> None:
    before = datetime.now(timezone.utc) - timedelta(seconds=30)
    body = _post_prepare(_payload())
    after = datetime.now(timezone.utc) + timedelta(seconds=30)

    metadata = body["audit_metadata"]
    assert metadata["action"] == "PREPARED_FOR_REVIEW"
    assert metadata["reviewer"] is None
    assert metadata["review_note"] is None
    created_at = _parse_dt(metadata["created_at"])
    changed_at = _parse_dt(metadata["status_changed_at"])
    assert before <= created_at <= after
    assert before <= changed_at <= after


def test_decision_audit_metadata_is_accurate() -> None:
    before = datetime.now(timezone.utc) - timedelta(seconds=30)
    response = client.post(
        "/review/decision",
        json={
            "finding_id": "RV004",
            "review_status": "NEEDS_MORE_EVIDENCE",
            "reviewer": "analyst-dana",
            "review_note": "Reproduce on staging before deciding.",
        },
    )
    assert response.status_code == 200
    after = datetime.now(timezone.utc) + timedelta(seconds=30)

    body = response.json()
    metadata = body["audit_metadata"]
    assert metadata["action"] == "REVIEW_DECISION"
    assert metadata["reviewer"] == "analyst-dana"
    assert metadata["review_note"] == "Reproduce on staging before deciding."
    created_at = _parse_dt(metadata["created_at"])
    changed_at = _parse_dt(metadata["status_changed_at"])
    assert before <= created_at <= after
    assert before <= changed_at <= after