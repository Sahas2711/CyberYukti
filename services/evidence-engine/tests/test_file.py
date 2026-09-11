"""Tests for FILE_EXISTS probe."""

import pytest
from models import AssetRef, CanonicalFinding, EvidenceClaim, LocationRef, VulnerabilityRef, InvalidInputException
from probes.file_check import run_file_check_probe, sanitize_and_resolve_file_path
from validator.evaluator import evaluate
from validator.target_registry import resolve_target


def make_file_finding(asset_id: str, path: str, expected_exists: bool = True) -> CanonicalFinding:
    return CanonicalFinding(
        finding_id="F-FILE-001",
        asset=AssetRef(id=asset_id),
        vulnerability=VulnerabilityRef(title="Sensitive file exposed", cve=None),
        location=LocationRef(type="file", path=path),
        evidence=EvidenceClaim(expected_exists=expected_exists),
    )


def test_file_probe_existing_file_confirmed():
    finding = make_file_finding("shop-api-01", "flag.txt", expected_exists=True)
    target = resolve_target("shop-api-01")

    status, observed, error = run_file_check_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["exists"] is True
    assert observed["size_bytes"] > 0

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "FILE_EXISTS")
    assert val_status == "CONFIRMED"
    assert confidence >= 0.95


def test_file_probe_missing_file_not_confirmed():
    finding = make_file_finding("shop-api-01", "does_not_exist.txt", expected_exists=True)
    target = resolve_target("shop-api-01")

    status, observed, error = run_file_check_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["exists"] is False

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "FILE_EXISTS")
    assert val_status == "NOT_CONFIRMED"
    assert confidence >= 0.95


def test_file_probe_directory_traversal_rejected():
    finding = make_file_finding("shop-api-01", "../../etc/passwd", expected_exists=True)
    target = resolve_target("shop-api-01")

    with pytest.raises(InvalidInputException) as exc_info:
        run_file_check_probe(finding, target)
    assert "Directory traversal detected" in str(exc_info.value) or "outside lab root" in str(exc_info.value)


def test_file_probe_null_byte_rejected():
    finding = make_file_finding("shop-api-01", "flag.txt\x00.png", expected_exists=True)
    target = resolve_target("shop-api-01")

    with pytest.raises(InvalidInputException):
        run_file_check_probe(finding, target)
