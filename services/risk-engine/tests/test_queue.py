"""
Tests for the analyst action queue endpoint POST /queue.

Covers:
1. Queue ordering (action category, then descending risk score)
2. Correct category counts in the summary
3. Filtering by category
4. Filtering by priority
5. Empty batch behavior
6. Deterministic repeated results
7. Invalid filter values produce a clear validation error
8. Item shape and action-category / next-step consistency
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

# Six findings that map to all four action queue categories:
#   Q1 IMMEDIATE_ACTION 0.9925 | Q2 VALIDATE_EVIDENCE 0.805
#   Q5 REMEDIATE 0.44          | Q3 REMEDIATE 0.415
#   Q6 DEFER 0.415             | Q4 DEFER 0.205
QUEUE_FINDINGS = [
    {
        "finding_id": "Q1",
        "title": "SQL Injection",
        "severity": "critical",
        "cvss": 10.0,
        "asset": {
            "id": "a",
            "criticality": 1.0,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.95},
    },
    {
        "finding_id": "Q2",
        "title": "RCE Candidate",
        "severity": "high",
        "cvss": 8.0,
        "asset": {
            "id": "b",
            "criticality": 0.9,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {"status": "INCONCLUSIVE", "confidence": 0.80},
    },
    {
        "finding_id": "Q3",
        "title": "Outdated Library",
        "severity": "low",
        "cvss": 3.0,
        "asset": {
            "id": "c",
            "criticality": 0.4,
            "internet_exposed": False,
            "environment": "development",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.90},
    },
    {
        "finding_id": "Q4",
        "title": "Info Disclosure",
        "severity": "low",
        "cvss": 2.0,
        "asset": {
            "id": "d",
            "criticality": 0.2,
            "internet_exposed": False,
            "environment": "development",
        },
        "validation": {"status": "NOT_CONFIRMED", "confidence": 0.0},
    },
    {
        "finding_id": "Q5",
        "title": "Missing Header",
        "severity": "medium",
        "cvss": 5.0,
        "asset": {
            "id": "e",
            "criticality": 0.3,
            "internet_exposed": False,
            "environment": "testing",
        },
        "validation": {"status": "CONFIRMED", "confidence": 0.70},
    },
    {
        "finding_id": "Q6",
        "title": "Deprecated Endpoint",
        "severity": "medium",
        "cvss": 5.0,
        "asset": {
            "id": "f",
            "criticality": 0.5,
            "internet_exposed": False,
            "environment": "testing",
        },
        "validation": {"status": "UNAVAILABLE", "confidence": 0.0},
    },
]


def _post_queue(findings: list[dict], params: dict | None = None) -> dict:
    response = client.post("/queue", json={"findings": findings}, params=params)
    assert response.status_code == 200, response.text
    return response.json()


NEXT_STEP_BY_CATEGORY = {
    "IMMEDIATE_ACTION": "Review and remediate",
    "VALIDATE_EVIDENCE": "Collect additional evidence",
    "REMEDIATE": "Validate asset and finding context",
    "DEFER": "Defer for later review",
}


# ---------------------------------------------------------------------------
# 1. Queue ordering
# ---------------------------------------------------------------------------


def test_queue_orders_by_category_then_risk_score():
    """IMMEDIATE_ACTION, VALIDATE_EVIDENCE, REMEDIATE, then DEFER; descending
    risk score within each category."""
    body = _post_queue(QUEUE_FINDINGS)

    ids = [item["finding_id"] for item in body["items"]]
    assert ids == ["Q1", "Q2", "Q5", "Q3", "Q6", "Q4"]

    categories = [item["decision_category"] for item in body["items"]]
    assert categories == [
        "IMMEDIATE_ACTION",
        "VALIDATE_EVIDENCE",
        "REMEDIATE",
        "REMEDIATE",
        "DEFER",
        "DEFER",
    ]

    scores = [item["risk_score"] for item in body["items"]]
    assert scores == [0.9925, 0.805, 0.44, 0.415, 0.415, 0.205]


def test_queue_is_stable_within_category_for_equal_scores():
    """Equal risk scores inside one category keep a stable, input-consistent
    order (deterministic sort)."""
    findings = [
        dict(QUEUE_FINDINGS[3]),  # Q4 DEFER 0.205
        dict(QUEUE_FINDINGS[2]),  # Q3 REMEDIATE 0.415
        dict(QUEUE_FINDINGS[5]),  # Q6 DEFER 0.415
    ]
    first = _post_queue(findings)
    second = _post_queue(list(reversed(list(findings))))
    assert [i["finding_id"] for i in first["items"]] == ["Q3", "Q6", "Q4"]
    assert first["items"] == second["items"]


# ---------------------------------------------------------------------------
# 2. Category counts in the summary
# ---------------------------------------------------------------------------


def test_queue_summary_counts_each_category():
    body = _post_queue(QUEUE_FINDINGS)
    assert body["count"] == 6
    assert body["summary"]["total"] == 6
    assert body["summary"]["categories"] == {
        "IMMEDIATE_ACTION": 1,
        "VALIDATE_EVIDENCE": 1,
        "REMEDIATE": 2,
        "DEFER": 2,
    }


def test_queue_summary_always_contains_all_four_categories():
    """Every summary includes all four category keys, even with zero items."""
    body = _post_queue(QUEUE_FINDINGS[:1])
    assert set(body["summary"]["categories"].keys()) == {
        "IMMEDIATE_ACTION",
        "VALIDATE_EVIDENCE",
        "REMEDIATE",
        "DEFER",
    }


# ---------------------------------------------------------------------------
# 3. Filtering by category
# ---------------------------------------------------------------------------


def test_queue_filter_by_category():
    body = _post_queue(QUEUE_FINDINGS, params={"category": "REMEDIATE"})
    assert body["count"] == 2
    assert body["summary"]["categories"] == {
        "IMMEDIATE_ACTION": 0,
        "VALIDATE_EVIDENCE": 0,
        "REMEDIATE": 2,
        "DEFER": 0,
    }
    assert [item["finding_id"] for item in body["items"]] == ["Q5", "Q3"]
    assert all(
        item["decision_category"] == "REMEDIATE" for item in body["items"]
    )


def test_queue_filter_by_category_immediate_action():
    body = _post_queue(QUEUE_FINDINGS, params={"category": "IMMEDIATE_ACTION"})
    assert body["count"] == 1
    assert body["items"][0]["finding_id"] == "Q1"


def test_queue_filter_by_category_no_matches():
    body = _post_queue(QUEUE_FINDINGS[:1], params={"category": "DEFER"})
    assert body["count"] == 0
    assert body["summary"]["total"] == 0
    assert body["items"] == []


# ---------------------------------------------------------------------------
# 4. Filtering by priority
# ---------------------------------------------------------------------------


def test_queue_filter_by_priority():
    body = _post_queue(QUEUE_FINDINGS, params={"priority": "P3"})
    assert body["count"] == 3
    assert [item["finding_id"] for item in body["items"]] == ["Q5", "Q3", "Q6"]
    assert all(item["priority"] == "P3" for item in body["items"])
    assert body["summary"]["categories"] == {
        "IMMEDIATE_ACTION": 0,
        "VALIDATE_EVIDENCE": 0,
        "REMEDIATE": 2,
        "DEFER": 1,
    }


def test_queue_filter_by_category_and_priority_together():
    body = _post_queue(
        QUEUE_FINDINGS,
        params={"category": "VALIDATE_EVIDENCE", "priority": "P1"},
    )
    assert body["count"] == 1
    assert body["items"][0]["finding_id"] == "Q2"


# ---------------------------------------------------------------------------
# 5. Empty batch behavior
# ---------------------------------------------------------------------------


def test_queue_empty_batch():
    body = _post_queue([])
    assert body["count"] == 0
    assert body["summary"]["total"] == 0
    assert body["summary"]["categories"] == {
        "IMMEDIATE_ACTION": 0,
        "VALIDATE_EVIDENCE": 0,
        "REMEDIATE": 0,
        "DEFER": 0,
    }
    assert body["items"] == []


# ---------------------------------------------------------------------------
# 6. Deterministic repeated results
# ---------------------------------------------------------------------------


def test_queue_is_deterministic():
    first = _post_queue(QUEUE_FINDINGS)
    second = _post_queue(QUEUE_FINDINGS)
    assert first == second


# ---------------------------------------------------------------------------
# 7. Invalid filter values
# ---------------------------------------------------------------------------


def test_queue_invalid_category_returns_validation_error():
    response = client.post(
        "/queue", json={"findings": QUEUE_FINDINGS}, params={"category": "BOGUS"}
    )
    assert response.status_code == 422
    body = response.json()
    assert any("category" in str(detail.get("loc")) for detail in body["detail"])
    assert any(
        "IMMEDIATE_ACTION" in str(detail.get("msg")) for detail in body["detail"]
    )


def test_queue_invalid_priority_returns_validation_error():
    response = client.post(
        "/queue", json={"findings": QUEUE_FINDINGS}, params={"priority": "P5"}
    )
    assert response.status_code == 422
    body = response.json()
    assert any("priority" in str(detail.get("loc")) for detail in body["detail"])
    assert any("P4" in str(detail.get("msg")) for detail in body["detail"])


# ---------------------------------------------------------------------------
# 8. Item shape and action-category consistency
# ---------------------------------------------------------------------------


def test_queue_item_contains_all_required_fields():
    body = _post_queue(QUEUE_FINDINGS[:1])
    item = body["items"][0]
    assert set(item.keys()) == {
        "finding_id",
        "title",
        "risk_score",
        "priority",
        "evidence_confidence",
        "evidence_status",
        "risk_confidence_category",
        "decision_category",
        "reasons",
        "recommended_next_step",
    }


def test_queue_next_step_matches_decision_category():
    body = _post_queue(QUEUE_FINDINGS)
    for item in body["items"]:
        assert (
            item["recommended_next_step"]
            == NEXT_STEP_BY_CATEGORY[item["decision_category"]]
        )


def test_queue_items_have_expected_values():
    """Verify a sampled item carries the exact scoring values."""
    body = _post_queue(QUEUE_FINDINGS)
    by_id = {item["finding_id"]: item for item in body["items"]}

    q1 = by_id["Q1"]
    assert q1["risk_score"] == 0.9925
    assert q1["priority"] == "P1"
    assert q1["evidence_confidence"] == 0.95
    assert q1["evidence_status"] == "CONFIRMED"
    assert q1["risk_confidence_category"] == "HIGH_RISK_HIGH_CONFIDENCE"
    assert q1["decision_category"] == "IMMEDIATE_ACTION"
    assert "Critical severity" in q1["reasons"]

    q2 = by_id["Q2"]
    assert q2["risk_score"] == 0.805
    assert q2["priority"] == "P1"
    assert q2["evidence_confidence"] == 0.80
    assert q2["evidence_status"] == "INCONCLUSIVE"
    assert q2["risk_confidence_category"] == "HIGH_RISK_LOW_CONFIDENCE"
    assert q2["decision_category"] == "VALIDATE_EVIDENCE"