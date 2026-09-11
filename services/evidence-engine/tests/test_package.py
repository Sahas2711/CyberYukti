"""Tests for PACKAGE_VERSION probe."""

import pytest
from models import AssetRef, CanonicalFinding, EvidenceClaim, LocationRef, VulnerabilityRef, InvalidInputException
from probes.package_version import run_package_version_probe, sanitize_package_name
from validator.evaluator import evaluate
from validator.target_registry import resolve_target


def make_package_finding(asset_id: str, package: str, claimed_version: str) -> CanonicalFinding:
    return CanonicalFinding(
        finding_id="F-PKG-001",
        asset=AssetRef(id=asset_id),
        vulnerability=VulnerabilityRef(title="Outdated dependency", cve="CVE-2023-0001"),
        location=LocationRef(type="package", package=package),
        evidence=EvidenceClaim(claimed_version=claimed_version),
    )


def test_package_name_sanitization():
    # Valid package names
    assert sanitize_package_name("requests") == "requests"
    assert sanitize_package_name("urllib3-core_1.2") == "urllib3-core_1.2"
    assert sanitize_package_name("example-package") == "example-package"

    # Malicious package names with shell metacharacters
    with pytest.raises(InvalidInputException):
        sanitize_package_name("requests; rm -rf /")

    with pytest.raises(InvalidInputException):
        sanitize_package_name("pkg$(whoami)")

    with pytest.raises(InvalidInputException):
        sanitize_package_name("pkg && reboot")

    with pytest.raises(InvalidInputException):
        sanitize_package_name("pkg|cat /etc/passwd")

    with pytest.raises(InvalidInputException):
        sanitize_package_name("   ")


def test_package_probe_vulnerable_target_confirmed():
    finding = make_package_finding("shop-api-01", "example-package", "1.2.3")
    target = resolve_target("shop-api-01")
    assert target is not None

    status, observed, error = run_package_version_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["package"] == "example-package"
    assert observed["version"] == "1.2.3"

    val_status, confidence, reasons = evaluate(finding.evidence, observed, status, "PACKAGE_VERSION")
    assert val_status == "CONFIRMED"
    assert confidence >= 0.95


def test_package_probe_patched_target_not_confirmed():
    finding = make_package_finding("shop-api-01-patched", "example-package", "1.2.3")
    target = resolve_target("shop-api-01-patched")
    assert target is not None

    status, observed, error = run_package_version_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["package"] == "example-package"
    assert observed["version"] == "1.2.9"  # Patched target has 1.2.9

    val_status, confidence, reasons = evaluate(finding.evidence, observed, status, "PACKAGE_VERSION")
    assert val_status == "NOT_CONFIRMED"
    assert confidence >= 0.95


def test_package_probe_semver_range_support():
    # Claim: vulnerable if < 1.2.5
    finding_vuln = make_package_finding("shop-api-01", "example-package", "< 1.2.5")
    target_vuln = resolve_target("shop-api-01")
    status, observed, _ = run_package_version_probe(finding_vuln, target_vuln)
    val_status, confidence, _ = evaluate(finding_vuln.evidence, observed, status, "PACKAGE_VERSION")
    assert val_status == "CONFIRMED"

    # Same claim on patched target (version is 1.2.9, which is not < 1.2.5)
    finding_patched = make_package_finding("shop-api-01-patched", "example-package", "< 1.2.5")
    target_patched = resolve_target("shop-api-01-patched")
    status, observed, _ = run_package_version_probe(finding_patched, target_patched)
    val_status, confidence, _ = evaluate(finding_patched.evidence, observed, status, "PACKAGE_VERSION")
    assert val_status == "NOT_CONFIRMED"


def test_package_probe_missing_package_on_target():
    finding = make_package_finding("shop-api-01", "nonexistent-lib", "1.0.0")
    target = resolve_target("shop-api-01")
    status, observed, error = run_package_version_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["version"] is None

    val_status, _, _ = evaluate(finding.evidence, observed, status, "PACKAGE_VERSION")
    assert val_status == "NOT_CONFIRMED"
