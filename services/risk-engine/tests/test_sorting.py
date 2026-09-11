"""
Unit tests for deterministic priority sorting via POST /assess/batch/sorted.

Covers:
1. P1 appears before P2
2. P2 appears before P3
3. Higher risk_score appears first within the same priority band
4. Output is stable and deterministic (identical input → identical output on repeat calls)

All expected scores are pre-calculated using the formula:
    risk_score = 0.40 * severity + 0.25 * asset_criticality
               + 0.20 * exposure + 0.15 * validation

Thresholds: P1 >= 0.80 | P2 >= 0.60 | P3 >= 0.35 | P4 < 0.35
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# P1: cvss=10 (sev=1.0), crit=1.0, exposed (exp=1.0), confirmed 0.90 (val=0.90)
# score = 0.40*1.0 + 0.25*1.0 + 0.20*1.0 + 0.15*0.90 = 0.985  => P1
_P1_FINDING = {
    "finding_id": "S-P1",
    "title": "P1 Critical RCE",
    "severity": "critical",
    "cvss": 10.0,
    "asset": {
        "id": "prod-api",
        "criticality": 1.0,
        "internet_exposed": True,
        "environment": "production",
    },
    "validation": {"status": "CONFIRMED", "confidence": 0.90},
}

# P2: severity=high (sev=0.8), crit=0.6, exposed (exp=1.0), confirmed 0.80 (val=0.80)
# score = 0.40*0.8 + 0.25*0.6 + 0.20*1.0 + 0.15*0.80 = 0.79  => P2
_P2_FINDING = {
    "finding_id": "S-P2",
    "title": "P2 High XSS",
    "severity": "high",
    "asset": {
        "id": "staging-web",
        "criticality": 0.6,
        "internet_exposed": True,
        "environment": "staging",
    },
    "validation": {"status": "CONFIRMED", "confidence": 0.80},
}

# P3: severity=medium (sev=0.5), crit=0.4, not exposed (exp=0.3), inconclusive 0.5 (val=0.25)
# score = 0.40*0.5 + 0.25*0.4 + 0.20*0.3 + 0.15*0.25 = 0.3975  => P3
_P3_FINDING = {
    "finding_id": "S-P3",
    "title": "P3 Medium CSRF",
    "severity": "medium",
    "asset": {
        "id": "test-server",
        "criticality": 0.4,
        "internet_exposed": False,
        "environment": "testing",
    },
    "validation": {"status": "INCONCLUSIVE", "confidence": 0.50},
}

# P4: severity=low (sev=0.2), crit=0.1, not exposed (exp=0.3), not_confirmed (val=0.1)
# score = 0.40*0.2 + 0.25*0.1 + 0.20*0.3 + 0.15*0.1 = 0.18  => P4
_P4_FINDING = {
    "finding_id": "S-P4",
    "title": "P4 Info Disclosure",
    "severity": "low",
    "asset": {
        "id": "dev-server",
        "criticality": 0.1,
        "internet_exposed": False,
        "environment": "development",
    },
    "validation": {"status": "NOT_CONFIRMED", "confidence": 0.0},
}

# Same-priority pair (both P2), different scores:
# P2-higher: cvss=8.0 (sev=0.8), crit=0.7, not exposed (exp=0.3), confirmed 0.40 (val=0.40)
# score = 0.40*0.8 + 0.25*0.7 + 0.20*0.3 + 0.15*0.40 = 0.615  => P2
_P2_HIGH_SCORE = {
    "finding_id": "S-P2-H",
    "title": "P2 High-score finding",
    "severity": "high",
    "cvss": 8.0,
    "asset": {
        "id": "internal-api",
        "criticality": 0.7,
        "internet_exposed": False,
        "environment": "staging",
    },
    "validation": {"status": "CONFIRMED", "confidence": 0.40},
}

# P2-lower: cvss=8.0 (sev=0.8), crit=0.6, not exposed (exp=0.3), confirmed 0.50 (val=0.50)
# score = 0.40*0.8 + 0.25*0.6 + 0.20*0.3 + 0.15*0.50 = 0.605  => P2
_P2_LOW_SCORE = {
    "finding_id": "S-P2-L",
    "title": "P2 Low-score finding",
    "severity": "high",
    "cvss": 8.0,
    "asset": {
        "id": "internal-svc",
        "criticality": 0.6,
        "internet_exposed": False,
        "environment": "staging",
    },
    "validation": {"status": "CONFIRMED", "confidence": 0.50},
}


def _post_sorted(findings: list) -> list:
    """Helper: POST to /assess/batch/sorted and return the results list."""
    response = client.post("/assess/batch/sorted", json={"findings": findings})
    assert response.status_code == 200
    body = response.json()
    assert "count" in body
    assert "results" in body
    return body["results"]


# ---------------------------------------------------------------------------
# 1. P1 appears before P2
# ---------------------------------------------------------------------------

def test_p1_appears_before_p2():
    """When input contains a P2 followed by a P1, sorted output puts P1 first."""
    # Submit in reverse order (P2 first, then P1) to prove sorting is active
    results = _post_sorted([_P2_FINDING, _P1_FINDING])

    priorities = [r["priority"] for r in results]
    p1_idx = priorities.index("P1")
    p2_idx = priorities.index("P2")

    assert p1_idx < p2_idx, (
        f"Expected P1 before P2, got order: {priorities}"
    )


# ---------------------------------------------------------------------------
# 2. P2 appears before P3
# ---------------------------------------------------------------------------

def test_p2_appears_before_p3():
    """When input contains a P3 followed by a P2, sorted output puts P2 first."""
    results = _post_sorted([_P3_FINDING, _P2_FINDING])

    priorities = [r["priority"] for r in results]
    p2_idx = priorities.index("P2")
    p3_idx = priorities.index("P3")

    assert p2_idx < p3_idx, (
        f"Expected P2 before P3, got order: {priorities}"
    )


# ---------------------------------------------------------------------------
# 3. Higher risk_score appears first within the same priority band
# ---------------------------------------------------------------------------

def test_higher_score_first_within_same_priority():
    """Within the same priority band (both P2), the higher risk_score comes first."""
    # Submit lower-score P2 first, then higher-score P2 — sorting must reorder
    results = _post_sorted([_P2_LOW_SCORE, _P2_HIGH_SCORE])

    assert len(results) == 2
    p2_results = [r for r in results if r["priority"] == "P2"]
    assert len(p2_results) == 2, "Both findings must be P2"

    assert p2_results[0]["risk_score"] >= p2_results[1]["risk_score"], (
        f"Expected descending risk_scores within P2, got "
        f"{p2_results[0]['risk_score']} then {p2_results[1]['risk_score']}"
    )
    assert p2_results[0]["finding_id"] == "S-P2-H"


# ---------------------------------------------------------------------------
# 4. Stable and deterministic output
# ---------------------------------------------------------------------------

def test_sorting_is_stable_and_deterministic():
    """
    Calling /assess/batch/sorted twice with identical input must produce
    identical output — same order, same scores, same finding_ids.
    """
    findings = [_P4_FINDING, _P2_FINDING, _P1_FINDING, _P3_FINDING]

    first_call = _post_sorted(findings)
    second_call = _post_sorted(findings)

    assert len(first_call) == len(second_call) == 4

    for i, (a, b) in enumerate(zip(first_call, second_call)):
        assert a["finding_id"] == b["finding_id"], (
            f"Position {i}: finding_id mismatch — {a['finding_id']} vs {b['finding_id']}"
        )
        assert a["priority"] == b["priority"], (
            f"Position {i}: priority mismatch — {a['priority']} vs {b['priority']}"
        )
        assert a["risk_score"] == b["risk_score"], (
            f"Position {i}: risk_score mismatch — {a['risk_score']} vs {b['risk_score']}"
        )
