import json

import pytest

from ..providers.mock_provider import MockProvider
from ..validator import validate_analysis

NO_KEV_CASE: dict = {
    "case_id": "TC-HAL-001",
    "cluster_id": "CL-HAL-001",
    "title": "SQL injection in user search",
    "finding_count": 1,
    "asset": {
        "asset_id": "ASSET-100",
        "hostname": "app.internal.com",
        "environment": "production",
        "internet_exposed": False,
        "criticality": "critical",
    },
    "vulnerability": {
        "cve": "CVE-2024-99999",
        "cvss_score": 8.6,
        "severity": "CRITICAL",
        "description": "SQL injection in user search endpoint",
    },
    "threat_intelligence": {},
    "evidence": {"status": "VALIDATED"},
    "priority": {"level": "P1", "score": 9.2},
}

CORRECT_CVSS_CASE: dict = {
    "case_id": "TC-HAL-002",
    "cluster_id": "CL-HAL-002",
    "title": "XSS in comment form",
    "finding_count": 1,
    "asset": {
        "asset_id": "ASSET-200",
        "hostname": "blog.example.com",
        "environment": "production",
        "internet_exposed": True,
        "criticality": "medium",
    },
    "vulnerability": {
        "cve": "CVE-2024-88888",
        "cvss_score": 5.4,
        "severity": "MEDIUM",
        "description": "Reflected XSS in comment submission form",
    },
    "threat_intelligence": {},
    "evidence": {"status": "VALIDATED"},
    "priority": {"level": "P3", "score": 4.0},
}

NO_CVE_INVENT_CASE: dict = {
    "case_id": "TC-HAL-003",
    "cluster_id": "CL-HAL-003",
    "title": "Misconfigured security headers",
    "finding_count": 2,
    "asset": {
        "asset_id": "ASSET-300",
        "hostname": "api.example.com",
        "environment": "staging",
        "internet_exposed": True,
        "criticality": "low",
    },
    "vulnerability": {
        "cve": None,
        "cvss_score": 3.1,
        "severity": "LOW",
        "description": "Missing security headers including X-Frame-Options and CSP",
    },
    "threat_intelligence": {},
    "evidence": {"status": "VALIDATED"},
    "priority": {"level": "P4", "score": 2.0},
}


def test_no_kev_claimed_when_none_in_input() -> None:
    provider = MockProvider()
    raw = provider.analyze(NO_KEV_CASE)
    analysis, issues = validate_analysis(raw, NO_KEV_CASE)

    assert analysis is not None, f"Validation failed: {issues}"
    full_text = (
        analysis.summary
        + analysis.why_it_matters
        + analysis.evidence_summary
        + analysis.priority_explanation
    ).lower()

    assert "kev" not in full_text, (
        "Mock analysis incorrectly references KEV when none was in input"
    )


def test_correct_cvss_referenced() -> None:
    provider = MockProvider()
    raw = provider.analyze(CORRECT_CVSS_CASE)
    analysis, issues = validate_analysis(raw, CORRECT_CVSS_CASE)

    assert analysis is not None, f"Validation failed: {issues}"
    full_text = (
        analysis.summary
        + analysis.why_it_matters
        + analysis.evidence_summary
        + analysis.priority_explanation
    )

    assert "5.4" in full_text, (
        "Analysis does not reference the correct CVSS score 5.4 from input"
    )
    assert "8.6" not in full_text, (
        "Analysis incorrectly references CVSS 8.6 from a different case"
    )


def test_no_cve_invented() -> None:
    provider = MockProvider()
    raw = provider.analyze(NO_CVE_INVENT_CASE)
    analysis, issues = validate_analysis(raw, NO_CVE_INVENT_CASE)

    assert analysis is not None, f"Validation failed: {issues}"

    full_text = (
        analysis.summary
        + analysis.why_it_matters
        + analysis.evidence_summary
        + analysis.priority_explanation
    )

    import re
    cves_found = re.findall(r"CVE-\d{4}-\d{4,}", full_text, re.IGNORECASE)
    assert len(cves_found) == 0, (
        f"Analysis invented CVE references {cves_found} when input had no CVE"
    )
