"""Tests for HTTP_ENDPOINT probe."""

from unittest.mock import MagicMock, patch
import httpx
import pytest

from models import AssetRef, CanonicalFinding, EvidenceClaim, LocationRef, VulnerabilityRef, InvalidInputException
from probes.http_endpoint import run_http_endpoint_probe, sanitize_endpoint_path
from validator.evaluator import evaluate
from validator.target_registry import resolve_target


def make_http_finding(asset_id: str, endpoint: str, expected_status: int = 200) -> CanonicalFinding:
    return CanonicalFinding(
        finding_id="F-HTTP-001",
        asset=AssetRef(id=asset_id),
        vulnerability=VulnerabilityRef(title="Exposed debug endpoint", cve=None),
        location=LocationRef(type="endpoint", endpoint=endpoint),
        evidence=EvidenceClaim(expected_status=expected_status),
    )


def test_endpoint_path_sanitization():
    # Valid paths
    assert sanitize_endpoint_path("/api/health") == "/api/health"
    assert sanitize_endpoint_path("api/status") == "/api/status"
    assert sanitize_endpoint_path("") == "/"

    # SSRF protocol and host smuggling attempts
    with pytest.raises(InvalidInputException):
        sanitize_endpoint_path("http://evil.com/leak")

    with pytest.raises(InvalidInputException):
        sanitize_endpoint_path("https://internal.vault/secret")

    with pytest.raises(InvalidInputException):
        sanitize_endpoint_path("//169.254.169.254/latest/meta-data")

    # Control character injection
    with pytest.raises(InvalidInputException):
        sanitize_endpoint_path("/api/health\x00extra")


@patch("httpx.Client.get")
def test_http_endpoint_confirmed(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_get.return_value = mock_resp

    finding = make_http_finding("shop-api-01", "/api/health", expected_status=200)
    target = resolve_target("shop-api-01")

    status, observed, error = run_http_endpoint_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["status_code"] == 200

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "HTTP_ENDPOINT")
    assert val_status == "CONFIRMED"
    assert confidence >= 0.95


@patch("httpx.Client.get")
def test_http_endpoint_not_confirmed(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_get.return_value = mock_resp

    finding = make_http_finding("shop-api-01", "/api/admin-secret", expected_status=200)
    target = resolve_target("shop-api-01")

    status, observed, error = run_http_endpoint_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["status_code"] == 404

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "HTTP_ENDPOINT")
    assert val_status == "NOT_CONFIRMED"


@patch("httpx.Client.get")
def test_http_endpoint_unreachable_inconclusive(mock_get):
    mock_get.side_effect = httpx.ConnectError("Connection refused")

    finding = make_http_finding("shop-api-01", "/api/health", expected_status=200)
    target = resolve_target("shop-api-01")

    status, observed, error = run_http_endpoint_probe(finding, target)
    assert status == "TARGET_UNAVAILABLE"

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "HTTP_ENDPOINT")
    assert val_status == "INCONCLUSIVE"
    assert confidence <= 0.35


@patch("httpx.Client.get")
def test_http_endpoint_timeout_inconclusive(mock_get):
    mock_get.side_effect = httpx.ConnectTimeout("Connection timed out")

    finding = make_http_finding("shop-api-01", "/api/health", expected_status=200)
    target = resolve_target("shop-api-01")

    status, observed, error = run_http_endpoint_probe(finding, target)
    assert status == "TIMEOUT"

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "HTTP_ENDPOINT")
    assert val_status == "INCONCLUSIVE"
