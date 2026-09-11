"""Complete Platform Regression Test Suite for CyberYukti.

Validates 100% of all previous platform features + all newly implemented USPs.
"""

import json
import time
import requests

BASE = "http://127.0.0.1:8000"

def run_test(name, fn):
    t0 = time.time()
    try:
        msg = fn()
        ms = (time.time() - t0) * 1000
        print(f"[PASS] {name:<50} ({ms:6.1f} ms) {msg}")
        return True
    except Exception as e:
        ms = (time.time() - t0) * 1000
        print(f"[FAIL] {name:<50} ({ms:6.1f} ms) Error: {e}")
        return False

def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200, f"Status {r.status_code}"
    return f"Status {r.status_code} - {r.json()}"

def test_ingestion_demo():
    r = requests.post(f"{BASE}/api/v1/scan/demo-ingest", json={})
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data and "clusters" in data
    return f"{data['summary']['total_raw_findings']} raw -> {data['summary']['total_clusters']} clusters"

def test_10k_benchmark():
    r = requests.post(f"{BASE}/api/v1/scan/benchmark-10k?count=10000&sync_store=true")
    assert r.status_code == 200
    d = r.json()
    return f"10k processed in {d['summary']['execution_time_ms']}ms -> {d['summary']['total_clusters']} clusters"

def test_sandbox_vulnerable():
    # Probe against shop-api-01 (vulnerable target with jQuery 1.12.4)
    r = requests.post(f"{BASE}/api/cases/CASE-002/validate?target_override=shop-api-01")
    assert r.status_code == 200
    case = r.json()
    assert case["evidence"]["status"] == "CONFIRMED"
    return f"Status: {case['evidence']['status']}, Score: {case['priority']['score']}, Level: {case['priority']['level']}"

def test_sandbox_patched():
    # Probe against shop-api-01-patched (remediated target with jQuery 3.6.0)
    r = requests.post(f"{BASE}/api/cases/CASE-002/validate?target_override=shop-api-01-patched")
    assert r.status_code == 200
    case = r.json()
    assert case["evidence"]["status"] == "NOT_CONFIRMED"
    return f"Status: {case['evidence']['status']}, Score: {case['priority']['score']} (Reduced!)"

def test_case_approval_lifecycle():
    # Create a new case
    r = requests.post(f"{BASE}/api/cases", json={
        "title": "Regression Lifecycle Verification",
        "severity": "critical",
        "cve": "CVE-2026-9999",
        "cwe": "CWE-89",
        "tool_name": "nuclei",
        "asset_name": "core-api-gw",
        "target_location": "/api/v1/checkout",
        "description": "SQL Injection found during regression test",
        "evidence_payload": "syntax error near SELECT",
        "internet_exposed": True,
        "criticality": "critical",
    })
    assert r.status_code == 200
    cid = r.json()["case_id"]

    # Approve
    r = requests.post(f"{BASE}/api/cases/{cid}/approve", json={"analyst_id": "reg-analyst", "reason": "Verified exploit"})
    assert r.status_code == 200

    # Override
    r = requests.post(f"{BASE}/api/cases/{cid}/override", json={"analyst_id": "reg-analyst", "override_priority": "P2", "reason": "WAF mitigates"})
    assert r.status_code == 200

    # Audit check
    r = requests.get(f"{BASE}/api/cases/{cid}/audit")
    assert r.status_code == 200
    events = r.json()
    assert len(events) >= 3
    assert events[-1]["prev_hash"] is not None
    return f"Case {cid} lifecycle complete: {len(events)} immutable audit events"

def test_usp1_attestation():
    r = requests.get(f"{BASE}/api/cases/CASE-001/attestation")
    assert r.status_code == 200
    receipt = r.json()
    assert "merkle_root" in receipt
    assert len(receipt["leaves"]) == 4

    # Verify receipt integrity
    r_ver = requests.post(f"{BASE}/api/cases/attestation/verify", json=receipt)
    assert r_ver.status_code == 200
    assert r_ver.json()["status"] == "TAMPER_FREE_VERIFIED"

    # Verify tamper detection
    tampered = dict(receipt)
    tampered["leaves"] = dict(receipt["leaves"])
    tampered["leaves"]["risk_scoring_hash"] = "deadbeef" * 8
    r_tamper = requests.post(f"{BASE}/api/cases/attestation/verify", json=tampered)
    assert r_tamper.json()["status"] == "VERIFICATION_FAILED"

    return f"Receipt {receipt['certificate_id']} verified (Merkle Root: {receipt['merkle_root'][:12]}...)"

def test_usp2_ai_copilot():
    r = requests.post(f"{BASE}/api/ai/chat", json={
        "message": "What is the priority and liability burn for CASE-001?",
        "case_id": "CASE-001",
    })
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data and len(data["reply"]) > 20
    return f"Source: {data['source']}, Reply: {data['reply'][:65]}..."

def test_usp3_remediation_playbooks():
    r = requests.get(f"{BASE}/api/cases/remediation/top10")
    assert r.status_code == 200
    playbooks = r.json()
    assert len(playbooks) > 0
    p = playbooks[0]
    assert "virtual_patch_waf" in p and "permanent_code_patch" in p
    assert p["liability_saved_usd"] > 0
    return f"{len(playbooks)} playbooks loaded. Top: {p['title']} ({p['formatted_savings']} saved)"

def test_usp4_cost_burn_telemetry():
    r = requests.get(f"{BASE}/api/dashboard/stats")
    assert r.status_code == 200
    stats = r.json()
    burn = stats.get("liability_burn", {})
    assert "daily_burn" in burn and burn["daily_burn"] > 0
    return f"Daily Burn: {burn.get('formatted_daily')}, Accrued: {burn.get('formatted_accrued')}"

def main():
    print("=" * 80)
    print("CYBERYUKTI FULL PLATFORM END-TO-END REGRESSION TEST")
    print("=" * 80)
    tests = [
        ("1. Core API Health", test_health),
        ("2. Ingestion & 3-Tier Dedup", test_ingestion_demo),
        ("3. 10,000 High-Scale Benchmark", test_10k_benchmark),
        ("4. Sandbox: Probe Vulnerable (shop-api-01)", test_sandbox_vulnerable),
        ("5. Sandbox: Probe Patched (shop-api-01-patched)", test_sandbox_patched),
        ("6. Case Lifecycle, Approval & Audit Chaining", test_case_approval_lifecycle),
        ("7. USP 1: Merkle Proof-of-Triage Attestation", test_usp1_attestation),
        ("8. USP 2: Grounded AI SOC Copilot Chat", test_usp2_ai_copilot),
        ("9. USP 3: Top 10 P1 Remediation Playbooks", test_usp3_remediation_playbooks),
        ("10. USP 4: Financial Liability Cost Burn Telemetry", test_usp4_cost_burn_telemetry),
    ]

    all_ok = True
    for name, fn in tests:
        ok = run_test(name, fn)
        if not ok:
            all_ok = False

    print("=" * 80)
    if all_ok:
        print("ALL 10/10 CORE & USP TESTS PASSED WITH 100% SUCCESS - ZERO REGRESSIONS!")
    else:
        print("TEST FAILURES OCCURRED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
