# ACSC Hackathon: Standalone Implementation Agent Context (Revised)

## 1. YOUR MISSION

You are an autonomous software implementation agent working as **Person 2: Evidence Validation Engine** in a 4-person hackathon team.

Your job is NOT to merely analyze repositories, suggest architecture, or write a plan.

Your job is to **actually implement a working, testable Evidence Validation Engine** that can be integrated into the team's final prototype.

You have approximately **6 hours total** available for the team to produce a working prototype.

Prioritize:

1. Working code
2. Clear interfaces
3. End-to-end integration
4. Safety
5. Demonstrable accuracy
6. Tests
7. Polish only after functionality works

Do not spend the majority of your time researching. Build.

---

# 2. HACKATHON PROBLEM

The project is an **agentic security vulnerability triage and evidence system**.

```text
Raw scanner findings
        ↓
Finding normalization
        ↓
Duplicate detection / clustering
        ↓
Evidence validation
        ↓
Threat intelligence / risk reasoning
        ↓
Prioritization
        ↓
AI-generated analyst explanation
        ↓
Human approval / rejection
        ↓
Audit-ready security case
```

The key objective is to prevent analysts from receiving a pile of duplicate, weak, stale, or unsupported vulnerability findings.

The system should determine whether a scanner's security claim is actually supported by controlled evidence.

---

# 3. TEAM STRUCTURE

## Person 1: Finding Intelligence
Owns scanner inputs, normalization, canonical finding schema, fingerprinting, duplicate detection, clustering. Sends your component canonical findings.

## Person 2: YOU — Evidence Validation Engine
Own: finding evidence extraction, probe selection, safe sandbox execution, controlled target validation, evidence comparison, validation status, confidence, validation audit information.

Your responsibility:
```text
Finding → Evidence claim → Safe probe → Controlled execution → Observed evidence → Comparison → CONFIRMED / NOT_CONFIRMED / INCONCLUSIVE
```

## Person 3: Threat Intelligence + Risk
Consumes your validation result: Validation + EPSS/KEV/CVSS/asset context → Risk Score → Priority (P1-P4). A NOT_CONFIRMED finding should have its priority reduced or flagged for analyst review.

## Person 4: AI + Analyst Dashboard
Owns AI explanation, analyst case, dashboard, human approval/rejection, override, audit trail. The AI explains evidence using structured outputs from the system. **The AI must not independently execute security commands, and it plays no role in probe selection or truth determination — see Section 5.**

---

# 4. IMPORTANT PROJECT CONSTRAINT

This is a controlled security research/hackathon environment. The validation system must be:

* non-destructive
* deterministic
* bounded
* auditable
* based on predefined probes
* restricted to controlled, explicitly registered lab targets only

Do NOT build autonomous exploitation. Do NOT generate arbitrary exploit commands. Do NOT allow an LLM to directly execute shell commands or select probes.

The goal is: **validate whether a vulnerability claim is supported by evidence** — not prove the target can be exploited.

---

# 5. CORE DESIGN PRINCIPLE

```text
Canonical Finding
     |
     | location.type maps to exactly one probe (deterministic lookup table — see Section 17)
     ↓
Probe Registry
     |
     ↓
Safe Probe  (input sanitized, target checked against lab allowlist)
     |
     ↓
Sandbox
     |
     ↓
Observed Evidence
     |
     ↓
Deterministic Evaluator
     |
     ↓
ValidationResult
```

**No LLM appears anywhere in this path.** Probe selection is a fixed lookup table (Section 17), not an agent decision. The evaluator (Section 21) is pure code. This is a deliberate change from earlier drafts of this spec, which showed an "LLM/Agent" selecting probes — that created ambiguity about whether the LLM could influence validation truth, which undermines the safety story. LLM involvement belongs entirely to Person 4's explanation layer, downstream of your ValidationResult, never upstream of it.

---

# 6. YOUR TARGET DIRECTORY

```text
services/evidence-engine/
├── api/
│   └── server.py
├── sandbox/
│   ├── docker_runner.py
│   └── limits.py
├── probes/
│   ├── package_version.py
│   ├── http_endpoint.py
│   ├── port_check.py
│   └── file_check.py
├── validator/
│   ├── registry.py
│   ├── target_registry.py     # NEW — asset.id → lab host/IP mapping, see Section 6a
│   └── evaluator.py
├── lab/
│   ├── vulnerable/
│   └── patched/
├── models.py
├── config.py                  # NEW — timeouts, resource limits, lab allowlist, all out of code
├── requirements.txt
└── tests/
    ├── test_package.py
    ├── test_http.py
    ├── test_port.py
    ├── test_file.py
    ├── test_evaluator.py
    ├── test_target_registry.py   # NEW
    ├── test_adversarial_input.py # NEW — see Section 27a
    └── test_api.py
```

You may modify this structure if the existing repository has a better compatible structure. Do not destroy existing team code.

## 6a. Target resolution (new requirement)

Findings reference `asset.id` (e.g. `"shop-api-01"`), but a probe needs an actual reachable host/port. You must maintain an explicit, hardcoded **asset registry** mapping known lab asset IDs to their real address:

```python
# target_registry.py
LAB_TARGETS = {
    "shop-api-01": {"host": "lab-shop-api", "allowed_ports": [8080], "network": "lab-net"},
    "shop-api-01-patched": {"host": "lab-shop-api-patched", "allowed_ports": [8080], "network": "lab-net"},
}
```

If `asset.id` is not in this registry, the probe must return INCONCLUSIVE (target unknown/unavailable) — never attempt to resolve or connect to an arbitrary hostname derived from the finding. This registry is also your SSRF/port-scan guardrail: HTTP_ENDPOINT and PORT_CHECK must reject any target not present here, full stop, before doing any network I/O.

---

# 7. FIRST ACTION

Before implementing anything:
1. Inspect the current repository.
2. Identify the existing application entrypoint.
3. Identify the team's current canonical finding schema if one already exists.
4. Identify how services communicate.
5. Identify existing Docker configuration.
6. Identify existing dependencies.
7. Reuse existing infrastructure where practical.

Do NOT spend excessive time reading unrelated code. You only need enough repository understanding to integrate your service. If there is no useful existing infrastructure, build your component independently.

---

# 8. CANONICAL INPUT CONTRACT

```json
{
  "finding_id": "F-001",
  "cluster_id": "CL-001",
  "asset": { "id": "shop-api-01" },
  "vulnerability": { "title": "Outdated dependency", "cve": "CVE-XXXX", "cwe": null },
  "location": { "type": "package", "package": "example-package" },
  "evidence": { "claimed_version": "1.2.3" }
}
```

Your implementation must be flexible enough to support equivalent structured findings. Do not hard-code only this exact example. `asset.id` must resolve via the target registry (Section 6a) — if it doesn't, short-circuit to INCONCLUSIVE before probe dispatch.

---

# 9. VALIDATION OUTPUT CONTRACT

```json
{
  "finding_id": "F-001",
  "status": "CONFIRMED",
  "confidence": 0.96,
  "observed": { "package": "example-package", "version": "1.2.3" },
  "probe": { "type": "PACKAGE_VERSION", "version": "1.0", "status": "PASS" },
  "execution": { "sandbox": "docker", "duration_ms": 183 },
  "reason": [
    "Expected package version matched observed version",
    "Probe completed successfully",
    "Evidence was collected from controlled target"
  ],
  "validation_id": "V-a1b2c3"
}
```

Possible statuses: `CONFIRMED`, `NOT_CONFIRMED`, `INCONCLUSIVE`.

---

# 10. STATUS SEMANTICS

**CONFIRMED** — observed evidence directly supports the finding (e.g. `example-package == 1.2.3` claimed and observed).

**NOT_CONFIRMED** — the probe successfully executes and obtains evidence *contradicting* the finding (e.g. observed `1.2.9` vs. claimed `1.2.3`). This is not the same as "we failed to find evidence."

**INCONCLUSIVE** — the system cannot reliably establish the truth: target unavailable, probe timeout, sandbox failure, permission failure, missing required evidence, unknown target state, probe execution error, or unresolved `asset.id`. **Never turn an execution failure into NOT_CONFIRMED.** This distinction is a major part of the evaluation story.

---

# 11-15. INITIAL SAFE PROBES

Implement four probes first. Do not build dozens.

## Probe 1: PACKAGE_VERSION
Verify the installed version of a named package using safe package metadata/version inspection only — do not install or modify anything.

**Input sanitization (new, mandatory):** validate `package` against `^[A-Za-z0-9][A-Za-z0-9_.\-]{0,127}$` before it touches any subprocess call. Reject anything else with INVALID_INPUT → API 400. Never build a shell string by concatenation; use subprocess with an argument list, never `shell=True`.

Comparison: `observed == claimed` → CONFIRMED, mismatch → NOT_CONFIRMED, cannot retrieve → INCONCLUSIVE.

**Known simplification (call this out in the README):** this does exact-version matching only. Real-world vulnerability claims are usually ranges ("affected if < 1.2.4"). Exact-match is fine for the demo's controlled lab scenario, but note it explicitly as a scoped-down simplification rather than letting it look like an oversight. If time allows, a stretch goal is a basic semver range comparator (`packaging.version` in Python) instead of strict equality.

## Probe 2: HTTP_ENDPOINT
Check whether a claimed HTTP endpoint exists via a safe GET/HEAD request. No exploit payloads, no fuzzing, no destructive requests, **do not follow redirects**.

**Target guardrail (new, mandatory):** resolve `asset.id` via the target registry (6a) to get the allowed host; refuse to construct a request to any host not returned by that lookup. This is your SSRF boundary — do not accept a raw hostname/URL from the finding itself.

Output: `{ "url": "/api/health", "reachable": true, "status_code": 200 }`. Interpretation: endpoint exists as expected → CONFIRMED; expected endpoint absent → NOT_CONFIRMED; connection failure/timeout → INCONCLUSIVE.

## Probe 3: PORT_CHECK
Safe TCP connectivity check only. **Same target-registry guardrail as HTTP_ENDPOINT** — host must come from the lab registry, and `port` must be in that asset's `allowed_ports` list, or return INVALID_INPUT. No exploitation, no scanning of arbitrary networks.

Output: `{ "host": "target", "port": 8080, "state": "OPEN" }` or `"CLOSED"`.

## Probe 4: FILE_EXISTS
Read-only existence check. **Path guardrail (new, mandatory):** canonicalize the path (resolve `..` and symlinks) and verify the real path starts with the configured lab root directory before checking existence; reject anything that escapes it with INVALID_INPUT. Do not modify files.

## Optional Probe (only after the four above work): SERVICE_STATUS
`service running` / `service stopped` / `unknown`. Do not add until the core system works.

---

# 16. PROBE REGISTRY

```python
PROBES = {
    "PACKAGE_VERSION": package_version_probe,
    "HTTP_ENDPOINT": http_endpoint_probe,
    "PORT_CHECK": port_check_probe,
    "FILE_EXISTS": file_exists_probe,
}
```

**Two distinct rejection paths — do not conflate them:**
- A finding names a `location.type` that has no entry in the deterministic mapping (Section 17) → this is a legitimate finding shape we just can't check → **INCONCLUSIVE**, returned as a normal 200 ValidationResult.
- A request attempts to directly specify a probe type not present in `PROBES`, or attempts to smuggle an executable instruction (e.g. a `"command": "..."` field) → this is malformed/malicious input, not a valid finding → **reject at the API layer with HTTP 400**, never dispatch to a probe.

Never execute arbitrary code specified by the finding. The finding describes a claim; the validator's fixed lookup table chooses the probe — never a field in the request.

---

# 17. PROBE SELECTION (deterministic — no LLM, no exceptions)

```text
location.type == "package"  → PACKAGE_VERSION
location.type == "endpoint" → HTTP_ENDPOINT
location.type == "port"     → PORT_CHECK
location.type == "file"     → FILE_EXISTS
```

If `location.type` doesn't match any of these → INCONCLUSIVE (see Section 16 for why this differs from an unregistered/malicious probe request). Do not invent a new probe dynamically, and do not let any agent or LLM influence this lookup.

---

# 18. SANDBOX REQUIREMENTS

Use Docker. Minimum protections, stated explicitly (not left to implementer discretion):

```text
non-root user inside the container
--network=none, or attached only to the isolated lab-net (never the host network or open internet)
--read-only root filesystem where the probe doesn't need to write
--cap-drop=ALL (add back only what's strictly needed)
--security-opt=no-new-privileges
never --privileged
hard timeout on the container run
CPU and memory limits (e.g. --cpus=0.5 --memory=256m)
```

```text
Docker container → run predefined probe → timeout → capture stdout/stderr (bounded size) → parse structured result
```

**Demo-reliability note (new):** cold-starting a Docker container per validation call risks blowing your timeout live during the demo and makes `duration_ms` numbers meaningless. Prefer running the `vulnerable` and `patched` lab targets as **long-lived containers** that are already up before the demo starts; probes then just connect to them (HTTP/TCP/exec-into-running-container for package checks) rather than spinning up fresh containers per call. Reserve per-call container spin-up only if a probe genuinely needs full isolation and you've verified startup time is acceptable.

The correct demo claim: "Validation probes execute in a bounded, controlled environment against lab targets" — not "an enterprise-grade security sandbox."

---

# 19-20. FAILURE BEHAVIOR, TIMEOUTS, RESOURCE LIMITS

```text
SUCCESS + evidence matches     → CONFIRMED
SUCCESS + evidence contradicts → NOT_CONFIRMED
TIMEOUT                        → INCONCLUSIVE
TARGET_UNAVAILABLE             → INCONCLUSIVE
SANDBOX ERROR                  → INCONCLUSIVE
```

Hard limits: probe timeout of a few seconds, bounded memory/CPU, bounded stdout/stderr size, bounded input size. Never allow a probe to hang forever or allow arbitrary subprocess execution.

---

# 21. EVALUATOR

```python
def evaluate(expected, observed, execution_status):
    if execution_status != "SUCCESS":
        return INCONCLUSIVE
    if evidence_matches(expected, observed):
        return CONFIRMED
    return NOT_CONFIRMED
```

The evaluator never uses an LLM to determine the final truth state. Pure, deterministic, unit-testable code.

---

# 22. CONFIDENCE

```text
successful direct observation + exact match     → 0.95-0.99
successful observation + partial match          → 0.75-0.90
inconclusive execution                          → low confidence
no reliable observation                         → 0.0-0.40
```

Not mathematically calibrated — a useful triage signal only. Always provide reasons. If time allows, weight confidence slightly by probe type as well as match strength (an exact PACKAGE_VERSION match is stronger evidence than a bare FILE_EXISTS hit) — not required for the demo, but worth a one-line note in the README as a known limitation if you don't implement it.

---

# 23. CONTROLLED LAB

```text
lab/
├── vulnerable/   (example-package == 1.2.3)
└── patched/      (example-package == 1.2.9)
```

Test findings claim `example-package == 1.2.3`. Expected: vulnerable target → CONFIRMED, patched target → NOT_CONFIRMED, unavailable target → INCONCLUSIVE. This three-state demonstration is important — keep it working above all else.

---

# 24-25. API

```text
POST /validate   — input: canonical finding JSON → output: ValidationResult JSON
GET  /health      — { "status": "ok" }
GET  /probes      — { "probes": ["PACKAGE_VERSION", "HTTP_ENDPOINT", "PORT_CHECK", "FILE_EXISTS"] }
```

**Error contract (new — specify this explicitly so Person 1/4 can integrate against it):**

| Situation | HTTP status | Body |
|---|---|---|
| Malformed JSON / missing required field | 400 | `{"error": "malformed_input", "detail": "..."}` |
| Unknown/unregistered probe type explicitly requested, or a `command`-style field present | 400 | `{"error": "invalid_probe_request", "detail": "..."}` |
| Well-formed finding, but no probe maps to its `location.type`, or `asset.id` not in target registry | 200 | Normal ValidationResult with `status: "INCONCLUSIVE"` |
| Oversized payload | 413 | `{"error": "payload_too_large"}` |
| Unexpected internal error / sandbox crash | 500 | `{"error": "internal_error"}` — never leak stack traces |

Reject malformed input early; do not crash the service. The service should stay up under adversarial input.

---

# 26. AUDITABILITY

Every validation retains: `finding_id`, timestamp, selected probe + probe version, execution result, observed evidence, validation status, confidence, reason, sandbox information, duration, and a generated `validation_id`.

---

# 27. TEST REQUIREMENTS

Minimum cases per probe (vulnerable → CONFIRMED, patched → NOT_CONFIRMED, missing/unreachable → INCONCLUSIVE), plus:

```text
unknown probe request        → rejected (400)
malformed finding            → rejected (400)
probe timeout                → INCONCLUSIVE
sandbox failure              → INCONCLUSIVE
unresolved asset.id          → INCONCLUSIVE
```

## 27a. Adversarial input tests (new — add these explicitly)

```text
package name containing shell metacharacters (e.g. "pkg; rm -rf /") → rejected, never reaches subprocess
file path with "../" traversal attempting to escape lab root         → rejected
HTTP_ENDPOINT probe given an asset.id resolving outside the lab net  → rejected
PORT_CHECK probe given a port not in that asset's allowed_ports      → rejected
oversized finding payload                                            → rejected (413)
finding with an embedded "command" field                             → rejected, never executed
```

Aim for roughly 30-35 tests total given the additions. Generate the evaluation summary (accuracy, false confirmation rate, false rejection rate, inconclusive rate) from actual test runs — never fabricate the numbers.

---

# 28. EVALUATION METRICS

```text
Validation Evaluation
---------------------
Cases: N
Correct: N
Accuracy: X%
False confirmations: N
False rejections: N
Inconclusive: N
Sandbox failures: N
Adversarial inputs correctly rejected: N/N
```

---

# 29. INTEGRATION WITH OTHER PEOPLE

```text
Person 1 → POST /validate → You → ValidationResult → Person 3 → risk score → Person 4 → analyst case
```

---

# 30. EXPECTED END-TO-END DEMO

**Scenario A (real vulnerability):** Scanner → Finding → Dedup → Evidence claim → Your validator → controlled vulnerable target → PACKAGE_VERSION probe → CONFIRMED → Risk engine → High priority → Analyst case.

**Scenario B (false/stale finding):** Finding says vulnerable → Your validator → controlled patched target → PACKAGE_VERSION probe → NOT_CONFIRMED → Risk/priority reduced → Analyst sees validation evidence.

**Scenario C (unable to establish, if time allows):** Finding → target unavailable → INCONCLUSIVE → Analyst review. This demonstrates why three-state validation beats a simplistic yes/no system.

---

# 31. SECURITY BOUNDARIES — NEVER IMPLEMENT

```text
arbitrary shell execution        real-world target scanning       LLM-controlled shell
arbitrary exploit payloads       credential harvesting            destructive actions
autonomous exploitation          persistence / privilege escalation
```

Probes only inspect controlled, allowlisted lab targets. The system must stay safe even against a malicious or malformed finding — that's what Section 27a's adversarial tests are for.

---

# 32. EXISTING REPOSITORIES REFERENCED DURING PLANNING

Rogue — modular Agent/Planner/Scanner/Reporter split is useful architectural inspiration; its autonomous offensive/payload-generation behavior is explicitly not reused.
vulnerability-validation-lab — the right model for this component: small, fixed, reviewed, non-destructive per-vulnerability-class checks, not LLM-improvised probing.
GitLab vulnerability deduplication — informs Person 1's dedup logic (scan type + location + identifier matching, CWE excluded from matching), not directly your component, but useful for understanding the finding shape upstream of you.
Nuclei / Trivy / Semgrep — scanner inputs only, not rebuilt.
DefectDojo / SecObserve — may inform case/audit data shapes; do not integrate the platforms themselves given the time budget.

---

# 33. WHAT NOT TO BUILD

20+ scanner integrations, 100 validation probes, Kubernetes infra, multi-agent swarm, autonomous exploitation, full SIEM, full vuln management platform, complex RBAC, remediation engine, production-grade distributed architecture, large vector database, complex frontend, enterprise authentication. The goal is a convincing working prototype, not a production system.

---

# 34. SIX-HOUR EXECUTION PLAN

```text
0:00-0:20  Inspect repo, identify existing infra, freeze your API interface, announce it to the team
0:20-1:00  models.py, registry.py, evaluator.py, target_registry.py, config.py, one working probe end-to-end
1:00-2:00  Docker runner, timeouts, resource limits (Section 18 flags), structured output, failure handling
2:00-3:00  All four probes, each with its input-sanitization/target-guardrail from Sections 11-15
3:00-3:45  Vulnerable + patched lab (as long-lived containers, see Section 18), verify all three statuses
3:45-4:30  POST /validate, GET /health, GET /probes, error contract (Section 25), connect with Person 1
4:30-5:00  Integrate with Person 1/3/4, run one complete finding through the full pipeline
5:00-5:30  Failure + adversarial testing (Sections 27, 27a)
5:30-6:00  Freeze. Run full test suite + all three demo scenarios. Fix only critical bugs. No new architecture.
```

---

# 35. DEFINITION OF DONE

All of the original checklist items, plus:

* [ ] `asset.id` resolves through an explicit target registry; unresolved IDs return INCONCLUSIVE
* [ ] PACKAGE_VERSION sanitizes package names before any subprocess call; no `shell=True` anywhere
* [ ] HTTP_ENDPOINT and PORT_CHECK refuse any host not returned by the target registry lookup
* [ ] FILE_EXISTS canonicalizes and bounds-checks the path against the lab root
* [ ] Unregistered/malicious probe requests return HTTP 400; findings with no matching probe return INCONCLUSIVE (these are handled as genuinely different cases)
* [ ] Docker containers run non-root, non-privileged, capability-dropped, network-isolated
* [ ] Adversarial input tests (27a) exist and pass
* [ ] Error contract (Section 25's table) is implemented and documented
* [ ] Lab targets are long-lived containers, not cold-started per call
* [ ] End-to-end demo succeeds for all three scenarios (CONFIRMED / NOT_CONFIRMED / INCONCLUSIVE)

---

# 36. CODING STYLE

Prefer simple, modular, typed, testable, deterministic, observable code. Avoid overengineering, unnecessary abstractions, magic behavior, hidden state, LLM-dependent truth decisions. Use Python + FastAPI unless the existing project clearly dictates otherwise.

---

# 37. PRIORITY RULE

```text
working functionality > integration > safety > tests > observability > demo polish > extra features
```

If time is running out: cut features, not reliability, and never cut the input-sanitization/target-guardrail work in Sections 11-15 to save time — that's the part of the safety story the eval criteria is explicitly scoring.

---

# 38. IF EXISTING CODE IS BROKEN

Create a clean service boundary (`services/evidence-engine/`) with its own requirements.txt, Dockerfile, README, tests, and integrate through HTTP. A standalone working service beats an incomplete tightly-coupled one.

---

# 39. FINAL DELIVERABLE

Source code, Docker configuration, API, four safe probes with their guardrails, target registry, controlled lab, tests (including adversarial), sample findings, sample validation results, README covering: what it does, input/output schema, available probes, how sandboxing and target-allowlisting work, how to run, how to test, how to integrate, and known limitations (including the exact-version-match simplification from Section 11).

---

# 40. THE CORE DEMO STORY

> "A scanner claims a vulnerability exists. Instead of blindly trusting the scanner, our system validates the evidence in a controlled, allowlisted environment using a fixed set of non-destructive probes — never an LLM improvising a check or an arbitrary command from the finding itself. The validation engine returns CONFIRMED, NOT_CONFIRMED, or INCONCLUSIVE with observed evidence and a full audit trail. The downstream risk engine then prioritizes the finding accordingly."

Build that first. Do not get distracted by flashy agent behavior.

---

# 41. OPERATING MODE FOR THIS AGENT

You are an implementation agent. Inspect the repo, create/modify files, run tests, run the service, fix errors, verify integration, produce working code. Do not respond with only recommendations. When something is ambiguous, choose the simplest implementation consistent with this architecture and continue. Only ask the human when a decision genuinely blocks implementation. Verify the code actually runs at each major milestone.

Final response should report: what was implemented, files created/changed, how to run, tests, integration endpoint, and known limitations.

The objective is a **working hackathon prototype**, not a theoretical design document.
