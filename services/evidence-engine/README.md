# Evidence Validation Engine (Person 2)

A deterministic, zero-LLM security vulnerability evidence validation engine built for the ACSC Hackathon agentic vulnerability triage pipeline.

---

## 1. What It Does

The Evidence Validation Engine determines whether raw vulnerability scanner claims are **actually supported by controlled evidence** on the target asset.

Instead of passing unverified scanner claims directly to analysts, this service:
1. Receives canonical finding claims from Person 1.
2. Resolves target assets strictly against a hardcoded lab allowlist (`LAB_TARGETS`) to eliminate SSRF and unvetted network access.
3. Deterministically selects predefined, safe, non-destructive probes without an LLM in the validation loop.
4. Executes checks in bounded containment (Docker / safe sandbox).
5. Deterministically evaluates observed evidence against claimed evidence to output audit-ready results:
   - **`CONFIRMED`**: Observed evidence directly proves the claim (e.g. vulnerable package version matched).
   - **`NOT_CONFIRMED`**: Probe succeeded and observed evidence *contradicts* the claim (e.g. patched version observed).
   - **`INCONCLUSIVE`**: Target offline, probe timeout, unmapped location type, or unresolved asset. **Execution failures are never converted to NOT_CONFIRMED.**

---

## 2. Architecture & Pipeline

```text
Canonical Finding (Person 1)
           │
           ▼
[API Layer: POST /validate]
  ├── Payload size check (< 64KB, 413)
  ├── Malformed input / schema validation (400)
  └── Adversarial/command injection check (400)
           │
           ▼
[Target Resolution: target_registry.py]
  ├── asset.id in LAB_TARGETS allowlist?
  └── NO  ──► HTTP 200 with status: INCONCLUSIVE
           │ YES
           ▼
[Deterministic Probe Lookup: registry.py]
  ├── location.type lookup (package, endpoint, port, file)
  └── Unmapped ──► HTTP 200 with status: INCONCLUSIVE
           │ Mapped
           ▼
[Input Sanitization & Guardrails: probes/]
  ├── PACKAGE_VERSION: regex ^[A-Za-z0-9][A-Za-z0-9_.\-]{0,127}$, no shell=True
  ├── HTTP_ENDPOINT: resolved host only, follow_redirects=False, GET only
  ├── PORT_CHECK: port checked against target allowed_ports whitelist
  └── FILE_EXISTS: canonicalized realpath must stay within lab root
           │
           ▼
[Bounded Sandbox Execution: docker_runner.py]
  ├── Timeouts, CPU/memory limits, stdout truncation
           │
           ▼
[Deterministic Evaluator: evaluator.py]
  ├── Pure code logic (Zero LLM)
  ├── Match ──► CONFIRMED (0.96 confidence)
  ├── Contradiction ──► NOT_CONFIRMED (0.96 confidence)
  └── Error/Timeout/Unknown ──► INCONCLUSIVE (0.10 - 0.30 confidence)
           │
           ▼
ValidationResult JSON ──► (Person 3: Risk Engine & Person 4: AI Dashboard)
```

---

## 3. Available Probes & Guardrails

| Probe | `location.type` | Guardrails & Boundaries | Output Evidence |
|---|---|---|---|
| **`PACKAGE_VERSION`** | `package` | Package name regex `^[A-Za-z0-9][A-Za-z0-9_.\-]{0,127}$`. Never uses `shell=True`. | `{"package": "...", "version": "...", "target": "..."}` |
| **`HTTP_ENDPOINT`** | `endpoint` | Host strictly from target registry (SSRF boundary). `follow_redirects=False`. Safe GET only. | `{"url": "...", "reachable": true, "status_code": 200}` |
| **`PORT_CHECK`** | `port` | Target host and port must be in target's `allowed_ports` whitelist. Non-destructive TCP connect. | `{"host": "...", "port": 8080, "state": "OPEN"}` |
| **`FILE_EXISTS`** | `file` | Canonicalized path bounds-check against lab root. Rejects directory traversal (`../`). Read-only. | `{"path": "...", "exists": true, "size_bytes": 1024}` |

---

## 4. API Specification & Error Contract

### Endpoints
* `GET /health` &rarr; `{"status": "ok"}`
* `GET /probes` &rarr; `{"probes": ["PACKAGE_VERSION", "HTTP_ENDPOINT", "PORT_CHECK", "FILE_EXISTS"]}`
* `POST /validate` &rarr; Accepts canonical finding, returns `ValidationResult`.

### Error Contract (Section 25)

| Situation | HTTP Status | Response Body |
|---|---|---|
| Malformed JSON / missing required fields | **400** | `{"error": "malformed_input", "detail": "..."}` |
| Unknown/unregistered probe requested, or `"command"` field present | **400** | `{"error": "invalid_probe_request", "detail": "..."}` |
| Well-formed finding, but no probe maps to `location.type`, or `asset.id` not in registry | **200** | Normal `ValidationResult` with `status: "INCONCLUSIVE"` |
| Oversized finding payload (> 64 KB) | **413** | `{"error": "payload_too_large"}` |
| Unexpected internal error | **500** | `{"error": "internal_error"}` *(never leaks stack traces)* |

---

## 5. Input and Output Contracts

### Input Schema (`POST /validate`)
```json
{
  "finding_id": "F-001",
  "cluster_id": "CL-001",
  "asset": { "id": "shop-api-01" },
  "vulnerability": {
    "title": "Outdated dependency",
    "cve": "CVE-2023-1111",
    "cwe": null
  },
  "location": {
    "type": "package",
    "package": "example-package"
  },
  "evidence": {
    "claimed_version": "1.2.3"
  }
}
```

### Output Schema (`ValidationResult`)
```json
{
  "finding_id": "F-001",
  "status": "CONFIRMED",
  "confidence": 0.96,
  "observed": {
    "package": "example-package",
    "version": "1.2.3",
    "target": "shop-api-01",
    "inspection_method": "controlled_manifest"
  },
  "probe": {
    "type": "PACKAGE_VERSION",
    "version": "1.0",
    "status": "PASS"
  },
  "execution": {
    "sandbox": "docker",
    "duration_ms": 4
  },
  "reason": [
    "Observed version (1.2.3) strictly matches claimed version (1.2.3)",
    "Claimed vulnerability evidence verified by controlled probe"
  ],
  "validation_id": "V-9a28c31f"
}
```

---

## 6. Sandboxing and Target Allowlisting

1. **Explicit Asset Registry (`validator/target_registry.py`)**:
   Only explicitly listed lab targets (`shop-api-01`, `shop-api-01-patched`, `db-cluster-01`) can be targeted. Arbitrary hostnames or IP addresses from findings are never contacted.
2. **Container Security Flags**:
   - Non-root execution (`--user=10001:10001`)
   - Network containment (`--network=lab-net` or `--network=none`)
   - Read-only root filesystem (`--read-only`)
   - Dropped capabilities (`--cap-drop=ALL`)
   - No new privileges (`--security-opt=no-new-privileges`)
   - Never privileged (`--privileged` is strictly prohibited)
   - Bounded resources (`--cpus=0.5`, `--memory=256m`, 10KB output buffer limit)
   - Hard execution timeout (`5.0s`)

---

## 7. How to Run & Test

### Run Unit & Adversarial Tests
```bash
python -m pytest tests -v
```

### Run Benchmark Evaluation
```bash
python evaluate_engine.py
```

### Start Service Locally
```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

### Run with Docker Compose
```bash
docker compose up --build
```

---

## 8. Integration with Other Team Members

- **Person 1 (Finding Intelligence)** &rarr; Sends `POST http://<evidence-engine>:8000/validate` with canonical findings.
- **Person 3 (Threat Intel + Risk)** &rarr; Consumes `ValidationResult`. If `status == "CONFIRMED"`, score remains high. If `status == "NOT_CONFIRMED"`, finding priority is downgraded. If `status == "INCONCLUSIVE"`, flags finding for analyst triage.
- **Person 4 (AI + Analyst Dashboard)** &rarr; Displays audit reasons, observed evidence, duration, and confidence score on the dashboard for human verification.

---

## 9. Known Limitations & Simplifications

1. **Exact Version vs Range Matching**:
   Real-world vulnerability scanners often report version intervals (`affected if < 1.2.4`). While our implementation includes Python `packaging.specifiers.SpecifierSet` range matching as an enhancement, the baseline hackathon lab scenario defaults to exact equality comparison.
2. **Lab Targets Scope**:
   Probing is strictly limited to pre-configured lab targets (`shop-api-01`, `shop-api-01-patched`, `db-cluster-01`). Scanning arbitrary production or external networks is purposefully prevented by design.
3. **HTTP Probe Methods**:
   The HTTP probe strictly executes read-only GET/HEAD requests to avoid state-changing or destructive side-effects during automated validation.
