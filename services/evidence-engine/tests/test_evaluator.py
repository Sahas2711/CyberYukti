"""Tests for Deterministic Evaluator."""

import pytest
from models import EvidenceClaim, ValidationStatus
from validator.evaluator import evaluate, evaluate_evidence_match


def test_evaluator_never_turns_execution_failure_into_not_confirmed():
    # Crucial Hackathon requirement (Section 10 & 21):
    # Even if expected and observed don't match, an execution error or timeout MUST be INCONCLUSIVE.
    claim = EvidenceClaim(claimed_version="1.2.3")
    observed = {"version": "9.9.9"}

    # Timeout case
    val_status, conf, reasons = evaluate(claim, observed, "TIMEOUT", "PACKAGE_VERSION")
    assert val_status == ValidationStatus.INCONCLUSIVE
    assert conf < 0.50

    # Target unavailable case
    val_status, conf, reasons = evaluate(claim, observed, "TARGET_UNAVAILABLE", "PACKAGE_VERSION")
    assert val_status == ValidationStatus.INCONCLUSIVE

    # Generic error case
    val_status, conf, reasons = evaluate(claim, observed, "ERROR", "PACKAGE_VERSION")
    assert val_status == ValidationStatus.INCONCLUSIVE


def test_evaluator_package_match_and_contradiction():
    claim = EvidenceClaim(claimed_version="1.2.3")

    # Exact match -> CONFIRMED
    val_status, conf, reasons = evaluate(claim, {"version": "1.2.3"}, "SUCCESS", "PACKAGE_VERSION")
    assert val_status == ValidationStatus.CONFIRMED
    assert conf == 0.96
    assert any("matches claimed version" in r for r in reasons)

    # Contradiction -> NOT_CONFIRMED
    val_status, conf, reasons = evaluate(claim, {"version": "1.2.9"}, "SUCCESS", "PACKAGE_VERSION")
    assert val_status == ValidationStatus.NOT_CONFIRMED
    assert conf == 0.96
    assert any("contradicts claimed version" in r for r in reasons)


def test_evaluator_http_match_and_contradiction():
    claim = EvidenceClaim(expected_status=200)

    val_status, conf, _ = evaluate(claim, {"reachable": True, "status_code": 200}, "SUCCESS", "HTTP_ENDPOINT")
    assert val_status == ValidationStatus.CONFIRMED

    val_status, conf, _ = evaluate(claim, {"reachable": True, "status_code": 404}, "SUCCESS", "HTTP_ENDPOINT")
    assert val_status == ValidationStatus.NOT_CONFIRMED

    val_status, conf, _ = evaluate(claim, {"reachable": False, "status_code": None}, "SUCCESS", "HTTP_ENDPOINT")
    assert val_status == ValidationStatus.NOT_CONFIRMED


def test_evaluator_port_match_and_contradiction():
    claim = EvidenceClaim(expected_state="OPEN")

    val_status, conf, _ = evaluate(claim, {"state": "OPEN"}, "SUCCESS", "PORT_CHECK")
    assert val_status == ValidationStatus.CONFIRMED

    val_status, conf, _ = evaluate(claim, {"state": "CLOSED"}, "SUCCESS", "PORT_CHECK")
    assert val_status == ValidationStatus.NOT_CONFIRMED


def test_evaluator_file_match_and_contradiction():
    claim = EvidenceClaim(expected_exists=True)

    val_status, conf, _ = evaluate(claim, {"exists": True}, "SUCCESS", "FILE_EXISTS")
    assert val_status == ValidationStatus.CONFIRMED

    val_status, conf, _ = evaluate(claim, {"exists": False}, "SUCCESS", "FILE_EXISTS")
    assert val_status == ValidationStatus.NOT_CONFIRMED
