"""
Tests for the sample datasets and README example accuracy.

Verifies that sample findings in the examples directory are valid JSON,
pass the Pydantic models, and contain the required number of items.
Also validates that the scoring engine produces the exact values shown
in the README documentation examples.
"""

import json
from pathlib import Path

from app.models import BatchFindingInput, FindingInput, AssetContext, ValidationResult
from app.scoring import calculate_risk_score

def test_sample_findings_dataset():
    base_dir = Path(__file__).resolve().parent.parent
    sample_file = base_dir / "examples" / "sample-findings.json"
    
    assert sample_file.exists(), "Sample findings file is missing"

    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    batch = BatchFindingInput(**data)
    
    assert len(batch.findings) >= 6, "Expected at least 6 findings in the sample dataset"


def test_readme_batch_f001_score():
    """README batch response example: F001 with CVSS 10.0 must score 0.9925."""
    finding = FindingInput(
        finding_id="F001",
        title="SQL Injection",
        severity="critical",
        cvss=10.0,
        asset=AssetContext(
            id="shop-api-01",
            criticality=1.0,
            internet_exposed=True,
            environment="production",
        ),
        validation=ValidationResult(status="CONFIRMED", confidence=0.95),
    )
    result = calculate_risk_score(finding)
    assert result.risk_score == 0.9925
    assert result.priority == "P1"
    assert result.factors == {
        "severity": 1.0,
        "asset_criticality": 1.0,
        "exposure": 1.0,
        "validation": 0.95,
    }


def test_readme_batch_f002_score():
    """README batch response example: F002 with CVSS 2.0 must score 0.205."""
    finding = FindingInput(
        finding_id="F002",
        title="Info Disclosure",
        severity="low",
        cvss=2.0,
        asset=AssetContext(
            id="dev-server",
            criticality=0.2,
            internet_exposed=False,
            environment="development",
        ),
        validation=ValidationResult(status="NOT_CONFIRMED", confidence=0.0),
    )
    result = calculate_risk_score(finding)
    assert result.risk_score == 0.205
    assert result.priority == "P4"


def test_readme_explain_example_score():
    """README /explain response example: CVSS 9.8 must score 0.9845."""
    finding = FindingInput(
        finding_id="F001",
        title="SQL Injection",
        severity="critical",
        cvss=9.8,
        cve="CVE-2021-44228",
        asset=AssetContext(
            id="shop-api-01",
            criticality=1.0,
            internet_exposed=True,
            environment="production",
        ),
        validation=ValidationResult(status="CONFIRMED", confidence=0.95),
    )
    result = calculate_risk_score(finding)
    assert result.risk_score == 0.9845
    assert result.priority == "P1"
    assert result.factors == {
        "severity": 0.98,
        "asset_criticality": 1.0,
        "exposure": 1.0,
        "validation": 0.95,
    }


def test_readme_scoring_formula():
    """Verify the documented formula: 0.40*severity + 0.25*criticality + 0.20*exposure + 0.15*validation."""
    finding = FindingInput(
        finding_id="FORMULA",
        title="Formula Check",
        severity="medium",
        asset=AssetContext(
            id="test",
            criticality=0.5,
            internet_exposed=True,
            environment="testing",
        ),
        validation=ValidationResult(status="CONFIRMED", confidence=0.8),
    )
    result = calculate_risk_score(finding)
    expected = round(0.40 * 0.5 + 0.25 * 0.5 + 0.20 * 1.0 + 0.15 * 0.8, 4)
    assert result.risk_score == expected
