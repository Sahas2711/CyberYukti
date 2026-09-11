# CyberYukti — Sandbox Security

**Status:** NOT APPLICABLE / NOT IMPLEMENTED. There is no sandbox to escape — the "safe sandbox" question is vacuous until Person-2 probe code exists.

## The question is vacuous today
- PS16 Person 2 calls for a safe sandbox for evidence probes (master doc Phase 21).
- No sandbox code of any kind exists: grep for `subprocess`, `docker`, `os.system`, `socket`, `urllib` across `backend/app` → **0 hits** (re-verified).
- No Dockerfile, docker-compose.yml, Makefile, or shell script anywhere in the repo (glob for `**/Dockerfile*`, `**/docker-compose*` → 0 hits; master doc Phase 12).
- No probe runner, no container runner, no subprocess harness. Nothing executes third-party payloads, so there is nothing for an attacker to escape.
- Correct assessment: no sandbox exists, so the guarantee is neither provided nor violated (master doc Phase 13). Any future "sandbox is escape-proof" claim must be re-audited against real code.

## Guarantees a Person-2 sandbox MUST provide (none exist)
1. **Timeouts** — hard wall-clock + per-probe budget so a malicious target cannot hang the pipeline. NOT PRESENT.
2. **CPU limits** — bound compute per probe (cgroup/`resource` limits) against DoS and decompression bombs. NOT PRESENT.
3. **Memory limits** — cap address space; prevent host-worker OOM. NOT PRESENT.
4. **Network isolation** — egress deny-by-default + target-registry allowlist; no SSRF into internal nets. NOT PRESENT (the only outbound SDK paths are optional OpenAI/Anthropic, never exercised — master doc Phase 13).
5. **Privilege dropping** — non-root, minimal UID, stripped capabilities. NOT PRESENT.
6. **Filesystem restrictions** — read-only rootfs, isolated mounts, no host FS except allowlisted artifacts. NOT PRESENT.
7. **Payload containment** — coerce probe output into `observed_value` str, never raw stdout (`models.py:38,40`). NOT PRESENT.
8. **Execution auditability** — record every probe run. NOT PRESENT — only analyst actions write events (`approval_routes.py:18-36`).

## Why the design still matters (forward risk)
- Fixture evidence already carries hostile-looking strings — "IGNORE ALL PREVIOUS INSTRUCTIONS…" and `<script>alert('pwned')</script>` (`fixtures.py:229,237`). Authored as data today; once a real probe targets a hostile service, such strings are *reflectable* back into observed output. The isolation above is what keeps them data.
- Emerging exploit surface once probes land: SSRF via `target`, RCE via subprocess probes on untrusted args, resource exhaustion of the host worker, output smuggling across the boundary.

## Verification recipe (how this status is established / re-confirmed)
1. `grep -rn "subprocess\|docker\|os.system\|socket\|urllib" backend/app` → 0 hits. Re-run on any PR claiming a sandbox.
2. Glob `**/Dockerfile*`, `**/docker-compose*`, `**/*.sh`, `**/Makefile` → 0 hits (master doc Phase 12).
3. Confirm no route named `POST /api/validate/{id}` exists (master doc Phase 10 "Missing endpoints").
4. Confirm no container/runtime tooling added to `pyproject.toml` / `package.json` (master doc Phase 11).

## Acceptance test each guarantee will require (future)
- **Timeout:** probe that never returns → killed at budget; pipeline continues.
- **CPU/mem:** probe that pins CPU or allocates unbounded memory → limited; host worker healthy.
- **Network:** probe requesting `http://169.254.169.254/` or internal hosts → blocked by egress allowlist.
- **Privilege:** probe launched as root or with capabilities → rejected at start.
- **Filesystem:** probe reading outside the allowlisted mount → denied.
- **Containment:** target echoes raw payload/stdout → lands only as a string in `EvidenceObservation.observed_value` (`models.py:38`).
- **Audit:** every probe run → an immutable audit event (extend `audit_routes.py`/`_audit_store`, `case_routes.py:13`).

## Consequence for the security model
- "No sandbox-escape surface" holds today only because there is no sandbox (master doc Phase 13).
- When Person-2 probes land, this file is the acceptance checklist — absence of any single guarantee downgrades the posture from "vacuous" to "unsafe execution".
- Probe targets and allowlists must come from the (absent) evidence engine (`EVIDENCE_ENGINE.md`); probe output feeds the (absent) risk engine (`RISK_ENGINE.md`).