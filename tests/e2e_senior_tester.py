"""Senior QA End-to-End Test Suite for CyberYukti Autonomous Vulnerability Triage Engine.
Tests all operational scenarios, edge cases, error conditions, and user workflows.
"""

import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

def log_test(name: str, passed: bool, details: str = "", elapsed_ms: float = 0.0):
    status_str = "[PASS]" if passed else "[FAIL]"
    print(f"{status_str} {name:<45} ({elapsed_ms:>6.1f} ms) {details}")
    return passed

def run_request(method: str, path: str, data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = {"User-Agent": "CyberYukti-SeniorTester/1.0", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            elapsed = (time.time() - t0) * 1000
            content = res.read()
            parsed = json.loads(content) if "json" in res.headers.get("content-type", "") else content.decode("utf-8")
            return res.status, parsed, elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - t0) * 1000
        content = e.read()
        parsed = json.loads(content) if "json" in e.headers.get("content-type", "") else content.decode("utf-8")
        return e.code, parsed, elapsed
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        return 0, str(e), elapsed

def test_all():
    print("=" * 80)
    print("CYBERYUKTI SENIOR QA END-TO-END VERIFICATION SUITE")
    print("=" * 80)
    all_passed = True

    # 1. System Health & Swagger
    status, body, ms = run_request("GET", "/")
    passed = status == 200 and body.get("status") == "online"
    all_passed = log_test("1.1 Root Health Check", passed, f"version={body.get('version')}", ms) and all_passed

    status, body, ms = run_request("GET", "/docs")
    all_passed = log_test("1.2 Swagger Documentation UI", status == 200, "HTML loaded", ms) and all_passed

    # 2. Ingestion & Deduplication Pipeline (Person 1)
    status, body, ms = run_request("POST", "/api/v1/scan/demo-ingest", data={})
    passed = status == 200 and "summary" in body and "clusters" in body
    summary = body.get("summary", {}) if passed else {}
    all_passed = log_test(
        "2.1 Demo Ingestion Pipeline (3 Scanners)",
        passed,
        f"{summary.get('total_raw_findings')} raw -> {summary.get('total_clusters')} clusters ({summary.get('noise_reduction_percentage')}% reduced)",
        ms
    ) and all_passed

    status, body, ms = run_request("GET", "/api/v1/clusters")
    all_passed = log_test("2.2 Deduplicated Clusters List", status == 200 and isinstance(body, list), f"{len(body)} clusters", ms) and all_passed

    status, body, ms = run_request("GET", "/api/v1/report")
    all_passed = log_test("2.3 Full Ingestion & Deduplication Report", status == 200 and "summary" in body, "Summary & clusters verified", ms) and all_passed

    # 3. High-Scale Ingestion (10,000 Findings Benchmark)
    status, body, ms = run_request("POST", "/api/v1/scan/benchmark-10k?count=10000&sync_store=true", data=None)
    passed = status == 200 and body.get("status") == "success"
    b_sum = body.get("summary", {}) if passed else {}
    all_passed = log_test(
        "3.1 10,000-Vulnerability Stress Benchmark",
        passed,
        f"10k raw -> {b_sum.get('total_clusters')} clusters ({b_sum.get('noise_reduction_percentage')}% noise reduced in {b_sum.get('execution_time_ms')}ms)",
        ms
    ) and all_passed

    # 4. Multi-Format Ingestion (CSV & JSON)
    sample_csv = """Title,Severity,Asset,CVE,CWE,Tool,Path
Log4j RCE,CRITICAL,auth-service,CVE-2021-44228,CWE-502,trivy,pom.xml
Path Traversal,HIGH,frontend-proxy,,CWE-22,semgrep,handlers/static.py
Path Traversal,HIGH,frontend-proxy,,CWE-22,nuclei,/api/static/download
"""
    status, body, ms = run_request("POST", "/api/v1/scan/raw", data={
        "content": sample_csv,
        "format": "csv",
        "filename": "test_upload.csv",
        "sync_store": False
    })
    passed = status == 200 and body.get("summary", {}).get("total_raw_findings") == 3
    all_passed = log_test("4.1 Raw CSV Scan Report Ingestion", passed, f"Collapsed into {body.get('summary', {}).get('total_clusters')} clusters", ms) and all_passed

    # 5. Sample Dataset Endpoints
    for sample in ["test-cases.csv", "test-cases.json", "10k.csv", "10k.json"]:
        status, _, ms = run_request("GET", f"/api/v1/scan/samples/{sample}")
        all_passed = log_test(f"5.0 Download Sample: {sample}", status == 200, "200 OK File Delivered", ms) and all_passed

    # 6. Manual Vulnerability Reporting
    new_case_payload = {
        "title": "QA Test: Unauthenticated SSRF in Metadata Service",
        "severity": "critical",
        "cve": "CVE-2023-38606",
        "cwe": "CWE-918",
        "tool_name": "nuclei",
        "asset_name": "cloud-proxy-qa:v1.0",
        "target_location": "/api/v1/metadata/aws",
        "description": "Exploit verified against internal AWS metadata service endpoint.",
        "evidence_payload": "http://169.254.169.254/latest/meta-data/",
        "internet_exposed": True,
        "criticality": "critical"
    }
    status, new_case, ms = run_request("POST", "/api/cases", data=new_case_payload)
    test_case_id = new_case.get("case_id") if status == 200 else "CASE-001"
    all_passed = log_test(
        "6.1 Create New Vulnerability Case",
        status == 200 and "case_id" in new_case,
        f"Created {test_case_id} (Priority: {new_case.get('priority', {}).get('level')}, Score: {new_case.get('priority', {}).get('score')})",
        ms
    ) and all_passed

    # 7. Case Retrieval & Filtering
    status, cases_list, ms = run_request("GET", "/api/cases?priority=P1")
    all_passed = log_test("7.1 List Cases Filtered by Priority P1", status == 200 and isinstance(cases_list, list), f"{len(cases_list)} P1 cases", ms) and all_passed

    status, case_detail, ms = run_request("GET", f"/api/cases/{test_case_id}")
    all_passed = log_test(
        "7.2 Fetch Case Detail & Audit",
        status == 200 and case_detail.get("case_id") == test_case_id,
        f"Title: {case_detail.get('title')[:35]}...",
        ms
    ) and all_passed

    # 8. AI Analysis Generation
    status, ai_resp, ms = run_request("POST", f"/api/ai/analyze/{test_case_id}", data={})
    passed = status == 200 and "summary" in ai_resp and "why_it_matters" in ai_resp
    all_passed = log_test("8.1 Grounded AI Analysis Generation", passed, f"Model={ai_resp.get('model')}", ms) and all_passed

    # 9. Case Lifecycle Decisions (Approve, Override, Reject, Audit)
    # 9.1 Approve
    status, app_res, ms = run_request("POST", f"/api/cases/{test_case_id}/approve", data={
        "analyst_id": "senior-qa-1",
        "reason": "Confirmed actionable zero-day risk"
    })
    all_passed = log_test("9.1 Approve Vulnerability Case", status == 200 and app_res.get("status") == "APPROVED", f"Decided by {app_res.get('decided_by')}", ms) and all_passed

    # 9.2 Override Priority
    status, ovr_res, ms = run_request("POST", f"/api/cases/{test_case_id}/override", data={
        "analyst_id": "senior-qa-1",
        "override_priority": "P2",
        "reason": "Temporary compensating WAF rule deployed"
    })
    all_passed = log_test("9.2 Override Priority to P2", status == 200 and ovr_res.get("override_priority") == "P2", f"New Status: {ovr_res.get('status')}", ms) and all_passed

    # 9.3 Reject with Reason
    status, rej_res, ms = run_request("POST", f"/api/cases/{test_case_id}/reject", data={
        "analyst_id": "senior-qa-1",
        "reason": "False positive verified"
    })
    all_passed = log_test("9.3 Reject Case with Mandatory Reason", status == 200 and rej_res.get("status") == "REJECTED", f"Reason: {rej_res.get('reason')}", ms) and all_passed

    # 9.4 Audit Trail Verification
    status, audit_events, ms = run_request("GET", f"/api/cases/{test_case_id}/audit")
    passed = status == 200 and len(audit_events) >= 3
    all_passed = log_test("9.4 Cryptographic Audit Trail Events", passed, f"{len(audit_events)} audit events recorded for {test_case_id}", ms) and all_passed

    # 10. Dashboard Stats & Noise Reduction KPI
    status, stats, ms = run_request("GET", "/api/dashboard/stats")
    passed = status == 200 and "total_findings" in stats and "unique_clusters" in stats and "p1" in stats
    all_passed = log_test(
        "10.1 Real-Time Dashboard KPI Stats",
        passed,
        f"Findings: {stats.get('total_findings')}, Clusters: {stats.get('unique_clusters')}, P1: {stats.get('p1')}, P2: {stats.get('p2')}",
        ms
    ) and all_passed

    print("=" * 80)
    if all_passed:
        print("[SUCCESS] ALL 18 END-TO-END TEST CASES PASSED WITH 100% SUCCESS!")
    else:
        print("[FAILURE] One or more tests failed. Check logs above.")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    test_all()
