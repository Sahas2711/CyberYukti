"""Unit and integration tests for CyberYukti USPs:
- Cryptographic Proof-of-Triage Attestation (SHA-256 Merkle root & tamper detection)
- Top 10 P1 Remediation Playbooks
- Financial Liability Cost Burn Telemetry
- Grounded AI SOC Chat Assistant
"""

import pytest
from backend.app.attestation import generate_case_attestation, verify_attestation
from backend.app.remediation import get_top_p1_remediation_playbooks, get_remediation_for_case
from backend.app.store import compute_cost_burn, init_store, get_cases, get_case


@pytest.fixture(autouse=True)
def ensure_store():
    init_store()


def test_attestation_generation_and_merkle_root():
    case = get_case("CASE-001")
    assert case is not None

    receipt = generate_case_attestation(case)
    assert receipt["case_id"] == "CASE-001"
    assert "merkle_root" in receipt
    assert len(receipt["merkle_root"]) == 64  # SHA-256 hex digest
    assert "digital_signature" in receipt
    assert len(receipt["state_transitions"]) == 4

    # Verify authentic receipt
    verification = verify_attestation(receipt)
    assert verification["valid"] is True
    assert verification["status"] == "TAMPER_FREE_VERIFIED"
    assert verification["merkle_root_matches"] is True
    assert verification["digital_signature_matches"] is True


def test_attestation_tamper_detection():
    case = get_case("CASE-001")
    receipt = generate_case_attestation(case)

    # Tamper with scanner evidence leaf hash
    tampered_receipt = dict(receipt)
    tampered_receipt["leaves"] = dict(receipt["leaves"])
    tampered_receipt["leaves"]["scanner_evidence_hash"] = "0" * 64

    # Verification must detect the tampering
    verification = verify_attestation(tampered_receipt)
    assert verification["valid"] is False
    assert verification["status"] == "VERIFICATION_FAILED"
    assert verification["merkle_root_matches"] is False


def test_top10_remediation_playbooks():
    cases = get_cases()
    playbooks = get_top_p1_remediation_playbooks(cases, limit=10)
    assert len(playbooks) > 0

    p1 = playbooks[0]
    assert "title" in p1
    assert "virtual_patch_waf" in p1
    assert "permanent_code_patch" in p1
    assert "verification_probe" in p1
    assert "liability_saved_usd" in p1
    assert p1["liability_saved_usd"] > 0


def test_cost_burn_telemetry():
    p1_case = {
        "case_id": "CASE-TEST-P1",
        "priority": {"level": "P1", "score": 95.0},
        "asset": {"criticality": "critical", "internet_exposed": True},
        "threat_intelligence": {"cisa_kev": True},
    }
    burn_p1 = compute_cost_burn(p1_case)
    assert burn_p1["hourly_burn"] > 1000
    assert burn_p1["daily_burn"] > 30000
    assert burn_p1["sla_window_hours"] == 4
    assert burn_p1["formatted_daily"].startswith("$")

    p4_case = {
        "case_id": "CASE-TEST-P4",
        "priority": {"level": "P4", "score": 20.0},
        "asset": {"criticality": "low", "internet_exposed": False},
        "threat_intelligence": {"cisa_kev": False},
    }
    burn_p4 = compute_cost_burn(p4_case)
    assert burn_p4["hourly_burn"] < burn_p1["hourly_burn"]
    assert burn_p4["sla_window_hours"] == 72
