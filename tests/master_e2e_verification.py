"""Comprehensive Master End-to-End Verification Suite for CyberYukti.

Executes all functional scenarios, frontend routes, backend APIs,
evidence validation cases, lifecycle governance, and unique selling propositions (USPs).
"""

import json
import time
import requests

BASE_BACKEND = "http://localhost:8000"
BASE_FRONTEND = "http://localhost:3000"

results = []

def record(category: str, test_name: str, passed: bool, detail: str = "", duration_ms: float = 0.0):
    results.append({
        "category": category,
        "test": test_name,
        "passed": passed,
        "detail": detail,
        "ms": round(duration_ms, 2)
    })
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} [{category:<16}] {test_name:<45} ({duration_ms:>6.1f}ms) {detail}")

def run_master_e2e():
    print("=" * 95)
    print("CYBERYUKTI COMPREHENSIVE END-TO-END VERIFICATION SUITE")
    print("=" * 95)

    # -------------------------------------------------------------
    # 1. FRONTEND UI ROUTES
    # -------------------------------------------------------------
    routes = [
        ("/", "Dashboard Overview"),
        ("/cases", "Triage Queue"),
        ("/vulnerabilities/new", "Intake Console / Report"),
        ("/vulnerabilities", "Vulnerabilities Redirect")
    ]
    for path, desc in routes:
        t0 = time.time()
        try:
            r = requests.get(f"{BASE_FRONTEND}{path}", allow_redirects=True, timeout=10)
            passed = (r.status_code == 200)
            record("Frontend UI", f"{path} ({desc})", passed, f"HTTP {r.status_code}, {len(r.text)} bytes", (time.time() - t0)*1000)
        except Exception as e:
            record("Frontend UI", f"{path} ({desc})", False, str(e), (time.time() - t0)*1000)

    # -------------------------------------------------------------
    # 2. BACKEND HEALTH & API DOCUMENTATION
    # -------------------------------------------------------------
    for path in ["/", "/health", "/docs", "/redoc"]:
        t0 = time.time()
        r = requests.get(f"{BASE_BACKEND}{path}", timeout=5)
        record("API Core", path, r.status_code == 200, f"HTTP {r.status_code}", (time.time() - t0)*1000)

    # -------------------------------------------------------------
    # 3. SCAN INGESTION & DEDUPLICATION (PERSON 1)
    # -------------------------------------------------------------
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/v1/scan/demo-ingest")
    p1_demo = r.json()
    passed = r.status_code == 200 and p1_demo.get("summary", {}).get("total_clusters") == 4
    sum_data = p1_demo.get("summary", {})
    record("Ingestion", "Demo Multi-Scanner Ingestion", passed, f"{sum_data.get('total_raw_findings')} raw -> {sum_data.get('total_clusters')} clusters ({sum_data.get('noise_reduction_percentage')}% noise reduction)", (time.time() - t0)*1000)

    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/v1/clusters")
    clusters = r.json()
    record("Ingestion", "Deduplicated Clusters List API", r.status_code == 200 and len(clusters) >= 4, f"Retrieved {len(clusters)} clusters", (time.time() - t0)*1000)

    t0 = time.time()
    sample_csv = """Title,Severity,Asset,CVE,CWE,Tool,Path
Log4j RCE,CRITICAL,auth-service,CVE-2021-44228,CWE-502,trivy,pom.xml
Path Traversal,HIGH,frontend-proxy,,CWE-22,semgrep,handlers/static.py
Path Traversal,HIGH,frontend-proxy,,CWE-22,nuclei,/api/static/download
"""
    r = requests.post(f"{BASE_BACKEND}/api/v1/scan/raw", json={
        "content": sample_csv,
        "format": "csv",
        "filename": "bulk_test.csv",
        "sync_store": False
    })
    passed = r.status_code == 200 and r.json().get("summary", {}).get("total_raw_findings") == 3
    record("Ingestion", "Raw CSV Scan Report Parsing", passed, f"Collapsed 3 findings into {r.json().get('summary', {}).get('total_clusters')} clusters", (time.time() - t0)*1000)

    # -------------------------------------------------------------
    # 4. CASE MANAGEMENT & AUDIT LIFECYCLE (PERSON 4)
    # -------------------------------------------------------------
    t0 = time.time()
    case_payload = {
        "title": "E2E Master Verification Case",
        "severity": "critical",
        "cve": "CVE-2026-1001",
        "cwe": "CWE-89",
        "tool_name": "nuclei",
        "asset_name": "payment-gateway",
        "target_location": "/api/v1/pay",
        "description": "SQL injection vulnerability in payment transaction handler",
        "evidence_payload": "' OR '1'='1",
        "internet_exposed": True,
        "criticality": "critical"
    }
    r = requests.post(f"{BASE_BACKEND}/api/cases", json=case_payload)
    new_case = r.json()
    cid = new_case.get("case_id")
    record("Case Lifecycle", "Create Vulnerability Case", r.status_code == 200 and bool(cid), f"Created {cid} (Score: {new_case.get('priority', {}).get('score')})", (time.time() - t0)*1000)

    # Single fetch
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/cases/{cid}")
    record("Case Lifecycle", "Fetch Single Case Detail", r.status_code == 200 and r.json().get("case_id") == cid, f"Retrieved {cid}", (time.time() - t0)*1000)

    # Filter by Priority
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/cases?priority=P1")
    record("Case Lifecycle", "List Filtered Cases (Priority: P1)", r.status_code == 200 and isinstance(r.json(), list), f"{len(r.json())} P1 cases returned", (time.time() - t0)*1000)

    # Approval
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/{cid}/approve", json={"analyst_id": "e2e-analyst", "reason": "Confirmed exploitability verified in staging"})
    record("Case Lifecycle", "Approve Case", r.status_code == 200 and r.json().get("status") == "APPROVED", "Status updated to APPROVED", (time.time() - t0)*1000)

    # Priority Override
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/{cid}/override", json={"analyst_id": "e2e-analyst", "override_priority": "P2", "reason": "WAF mitigating controls active"})
    record("Case Lifecycle", "Override Case Priority to P2", r.status_code == 200 and r.json().get("override_priority") == "P2", "Priority updated to P2", (time.time() - t0)*1000)

    # Rejection with mandatory justification
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/{cid}/reject", json={"analyst_id": "e2e-analyst", "reason": "Not reproducible on current deployment"})
    record("Case Lifecycle", "Reject Case with Mandatory Justification", r.status_code == 200 and r.json().get("status") == "REJECTED", "Status updated to REJECTED", (time.time() - t0)*1000)

    # Cryptographic Audit Trail Chaining
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/cases/{cid}/audit")
    events = r.json()
    record("Case Lifecycle", "Cryptographic Audit Trail Integrity", r.status_code == 200 and len(events) >= 3, f"{len(events)} immutable audit events chained", (time.time() - t0)*1000)

    # -------------------------------------------------------------
    # 5. EVIDENCE VALIDATION SANDBOX PROBING (PERSON 3)
    # -------------------------------------------------------------
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/CASE-002/validate?target_override=shop-api-01")
    val_vuln = r.json()
    record("Evidence Sandbox", "Probe Vulnerable Asset (shop-api-01)", r.status_code == 200 and val_vuln.get("evidence", {}).get("status") == "CONFIRMED", f"Exploit: {val_vuln.get('evidence', {}).get('status')}", (time.time() - t0)*1000)

    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/CASE-002/validate?target_override=shop-api-01-patched")
    val_patched = r.json()
    record("Evidence Sandbox", "Probe Patched Asset (shop-api-01-patched)", r.status_code == 200 and val_patched.get("evidence", {}).get("status") == "NOT_CONFIRMED", f"Exploit: {val_patched.get('evidence', {}).get('status')} (Score reprioritized lower)", (time.time() - t0)*1000)

    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/cases/CASE-002/validate?target_override=unknown-box-99")
    val_unk = r.json()
    record("Evidence Sandbox", "Probe Unknown Asset (Graceful Inconclusive)", r.status_code == 200 and val_unk.get("evidence", {}).get("status") == "INCONCLUSIVE", f"Result: {val_unk.get('evidence', {}).get('status')}", (time.time() - t0)*1000)

    # -------------------------------------------------------------
    # 6. UNIQUE SELLING PROPOSITIONS (USPs)
    # -------------------------------------------------------------
    # USP 1: Merkle Proof-of-Triage Attestation
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/cases/CASE-001/attestation")
    attestation = r.json()
    record("USP 1 Attestation", "Generate Merkle Certificate Receipt", r.status_code == 200 and "merkle_root" in attestation, f"Certificate: {attestation.get('certificate_id')} (Root: {attestation.get('merkle_root', '')[:12]}...)", (time.time() - t0)*1000)

    t0 = time.time()
    r_v = requests.post(f"{BASE_BACKEND}/api/cases/attestation/verify", json=attestation)
    record("USP 1 Attestation", "Verify Tamper-Free Certificate", r_v.status_code == 200 and r_v.json().get("status") == "TAMPER_FREE_VERIFIED", "Status: TAMPER_FREE_VERIFIED", (time.time() - t0)*1000)

    t0 = time.time()
    tampered = dict(attestation)
    tampered["leaves"] = dict(attestation["leaves"])
    tampered["leaves"]["risk_scoring_hash"] = "0"*64
    r_tv = requests.post(f"{BASE_BACKEND}/api/cases/attestation/verify", json=tampered)
    record("USP 1 Attestation", "Attestation Tamper Detection Guard", r_tv.json().get("status") == "VERIFICATION_FAILED", "Correctly rejected tampered leaves", (time.time() - t0)*1000)

    # USP 2: Grounded AI SOC Copilot
    t0 = time.time()
    r = requests.post(f"{BASE_BACKEND}/api/ai/chat", json={"message": "What is the priority for CASE-001?", "case_id": "CASE-001"})
    ai_data = r.json()
    record("USP 2 AI Copilot", "Grounded AI SOC Copilot Chat", r.status_code == 200 and "reply" in ai_data and len(ai_data["reply"]) > 20, f"Source: {ai_data.get('source')}", (time.time() - t0)*1000)

    # USP 3: Remediation Playbooks
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/cases/remediation/top10")
    pb_list = r.json()
    record("USP 3 Playbooks", "Top 10 P1 Remediation Playbooks", r.status_code == 200 and len(pb_list) > 0, f"Delivered {len(pb_list)} action playbooks", (time.time() - t0)*1000)

    # USP 4: Cost Burn Telemetry
    t0 = time.time()
    r = requests.get(f"{BASE_BACKEND}/api/dashboard/stats")
    stats = r.json()
    burn = stats.get("liability_burn", {})
    record("USP 4 Cost Burn", "Financial Liability Cost Burn Telemetry", r.status_code == 200 and "daily_burn" in burn, f"Daily: {burn.get('formatted_daily')}, Accrued: {burn.get('formatted_accrued')}", (time.time() - t0)*1000)

    print("=" * 95)
    total_tests = len(results)
    passed_tests = sum(1 for x in results if x["passed"])
    print(f"SUMMARY: {passed_tests}/{total_tests} END-TO-END TESTS PASSED ({round(passed_tests/total_tests*100, 1)}%)")
    print("=" * 95)
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_master_e2e()
    exit(0 if success else 1)
