"""Tests for PORT_CHECK probe."""

import socket
from unittest.mock import patch
import pytest

from models import AssetRef, CanonicalFinding, EvidenceClaim, LocationRef, VulnerabilityRef, InvalidInputException
from probes.port_check import run_port_check_probe
from validator.evaluator import evaluate
from validator.target_registry import resolve_target


def make_port_finding(asset_id: str, port: int, expected_state: str = "OPEN") -> CanonicalFinding:
    return CanonicalFinding(
        finding_id="F-PORT-001",
        asset=AssetRef(id=asset_id),
        vulnerability=VulnerabilityRef(title="Unfiltered administrative port exposed", cve=None),
        location=LocationRef(type="port", port=port),
        evidence=EvidenceClaim(expected_state=expected_state),
    )


@patch("socket.socket.connect_ex")
def test_port_check_open_confirmed(mock_connect):
    mock_connect.return_value = 0  # 0 indicates success / open

    finding = make_port_finding("shop-api-01", 8080, expected_state="OPEN")
    target = resolve_target("shop-api-01")

    status, observed, error = run_port_check_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["state"] == "OPEN"

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "PORT_CHECK")
    assert val_status == "CONFIRMED"
    assert confidence >= 0.95


@patch("socket.socket.connect_ex")
def test_port_check_closed_not_confirmed(mock_connect):
    mock_connect.return_value = 111  # ECONNREFUSED / closed

    finding = make_port_finding("shop-api-01", 8080, expected_state="OPEN")
    target = resolve_target("shop-api-01")

    status, observed, error = run_port_check_probe(finding, target)
    assert status == "SUCCESS"
    assert observed["state"] == "CLOSED"

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "PORT_CHECK")
    assert val_status == "NOT_CONFIRMED"
    assert confidence >= 0.95


def test_port_check_unauthorized_port_rejected():
    # Asset shop-api-01 allows [8080, 8081]; port 22 or 445 should be rejected
    finding = make_port_finding("shop-api-01", 22, expected_state="OPEN")
    target = resolve_target("shop-api-01")

    with pytest.raises(InvalidInputException) as exc_info:
        run_port_check_probe(finding, target)
    assert "not in the allowed_ports whitelist" in str(exc_info.value)


def test_port_check_out_of_range_rejected():
    finding = make_port_finding("shop-api-01", 99999, expected_state="OPEN")
    target = resolve_target("shop-api-01")

    with pytest.raises(InvalidInputException):
        run_port_check_probe(finding, target)


@patch("socket.socket.connect_ex")
def test_port_check_timeout_inconclusive(mock_connect):
    mock_connect.side_effect = socket.timeout("Timed out")

    finding = make_port_finding("shop-api-01", 8080, expected_state="OPEN")
    target = resolve_target("shop-api-01")

    status, observed, error = run_port_check_probe(finding, target)
    assert status == "TIMEOUT"

    val_status, confidence, _ = evaluate(finding.evidence, observed, status, "PORT_CHECK")
    assert val_status == "INCONCLUSIVE"
