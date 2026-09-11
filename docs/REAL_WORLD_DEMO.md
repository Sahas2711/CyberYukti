# Person 4 Integration Review

**Repository:** github.com/Sahas2711/CyberYukti
**Reviewer role:** Integration engineer / security architect / QA lead / release gatekeeper
**Date:** 2026-09-11
**Scope of verdict:** Whether the Person 4 branch (this repository's entire current implementation) can be merged such that the complete "Autonomous Vulnerability Triage & Evidence Engine" problem statement is satisfied end-to-end.

---

## 1. Executive Decision

# ⛔ DO NOT MERGE

Person 4's own scope is **high quality and internally consistent** (UI, typed provider layer, approval/override/reject, audit trail, AI guardrails, injection-safe rendering — all tested and working against the real backend API). It cannot be merged into a working product, however, because **the other three persons' deliverables — the engine of the problem statement — do not exist anywhere in this repository.** There is no finding-ingestion endpoint, no normalization, no deduplication/clustering logic, no evidence-validation sandbox or probes, and no deterministic priority *computation* (scores are pre-baked fixture constants). The system only runs on hand-crafted demo fixtures. Per the hard merge-gate rules (Sections 38.2–38.8, 38.18; 46–48 of the task), this is a **DO NOT MERGE**.

---

## 2. Repository State

Facts gathered from `git`, not assumptions:

| Item | Actual state |
|---|---|
| Remote (owner/name) | `https://github.com/Sahas2711/CyberYukti` (`origin`) |
| Default branch | `main` |
| Commits on `main` | **0 (zero) — repository has never received a commit** |
| Current branch | `main` |
| All branches | `main` only |
| Person 1 branch | **Does not exist** |
| Person 2 branch | **Does not exist** |
| Person 3 branch | **Does not exist** |
| Person 4 branch | **Does not exist** (created as `person4/integration` during this review — see Git section) |
| Integration branch | Does not exist |
| Open pull requests | None (no remote PRs discovered; remote may not expose PR state) |
| Tracking status | Entire working tree (backend/, frontend/, docs/, prompts.txt, .env.example) is **untracked** |
| Untracked ignored config | None (no root `.gitignore` existed; created during review) |
| Stashes / reflog | None |

**Implication:** the "four parallel persons" narrative exists only in `prompts.txt` and `docs/person4-contracts.md`. In reality there is a single uncommitted tree that implements **only Person 4's vertical slice**, with Person 1/2/3 modelled *only* as Pydantic types (`Finding`, `Cluster`) and pre-baked fixture dictionaries. That is the single most important finding of this review.

---

## 3. Branch Comparison

There are no Person branches to diff. The comparison below is **Person 1/2/3 scope vs what actually exists in the tree** (which is Person 4's implementation).

| Scope (per prompts.txt) | Expected deliverable | Actual implementation | Status |
|---|---|---|---|
| **Person 1** | Scanner ingestion, canonical schema, normalization, dedup, backend foundation | `Finding` & `Cluster` Pydantic models in `backend/app/cases/models.py:13-32` — **defined, never instantiated**. No ingestion endpoint, no normalization, no dedup code. All cases from `backend/app/mock/fixtures.py`. | ❌ ABSENT |
| **Person 2** | Evidence extraction, **Docker sandbox**, validation probes | `ValidationResult` / `EvidenceObservation` models + fixture data only. **No sandbox, no probes, no subprocess, no network validation code** (grep for `subprocess|os.system|create_subprocess|socket.|requests.|httpx.` → 0 hits). | ❌ ABSENT |
| **Person 3** | NVD/EPSS/KEV/OSV enrichment, risk scoring, P1–P4 prioritization formula | `threat_intelligence` (cvss/epss/kev) and `priority` (score/level/factors/formula_version) are **hardcoded fixture constants**. No enrichment calls, no score function (grep for `def .*(score|priority|cvss)` → only a test function). Override writes `priority.level` without recomputing score (`approval_routes.py:128`). | ❌ ABSENT |
| **Person 4** | AI explanation engine, dashboard, case views, approval workflow, audit, guardrails, typed API, frontend | Implemented and verified (see §12). | ✅ PRESENT |

### Overlaps / conflicts / duplicates found

| Item | Finding |
|---|---|
| Duplicate `AIAnalysis` model | Defined twice: `backend/app/cases/models.py:61-72` and `backend/app/ai/schemas.py:4-15` (identical, but *different classes* in different modules). Works only because routes return raw dicts. Maintainability risk. |
| Duplicate case store | `case_routes.py` and `ai_routes.py` each build their own `_cases_store`; the AI route operates on a **stale copy** (mutations in the approval store are invisible to the AI store and vice-versa). |
| Frontend filter bug (fixed) | `EVIDENCE_OPTIONS` contained `"NOT CONFIRMED"` (space) while `evidence.status` is `"NOT_CONFIRMED"` (underscore) → the filter never matched. Fixed in `frontend/components/dashboard/CaseTable.tsx:31`. |
| Audit semantics divergence | Real backend seeds **no** lifecycle audit events (fresh case audit = empty; `GET /audit` then returns 404). Frontend mock seeds `clustered → evidence validated → priority calculated → analysis generated`. Demo parity gap. |
| `prev_hash` naming | The field stores the previous **`event_id`**, not a cryptographic/structural hash of the previous event. Chain integrity is structural only. |
| Approval response type | Backend returns the **approval object**; frontend types responses as `TriageCase` (`realProvider.ts`). Safe at runtime because the UI ignores the body and re-fetches — but the type is technically wrong. |
| Fixture divergence | `CASE-005` evidence confidence = `0.82` (backend fixtures) vs `0.90` (frontend mock + docs). Dashboard `p1` counts derived from fixtures differ slightly across layers. |

---

## 4. Problem Statement Mapping

Official problem statement (repo `prompts.txt`): *"Build an agentic system that **receives raw security findings**, **removes duplicates**, **validates evidence in a safe sandbox**, and **produces prioritized analyst-ready cases**."*

| Requirement | Responsible | Implementation | Input | Output | Test | Real-world demo | Status |
|---|---|---|---|---|---|---|---|
| Finding normalization | P1 | **None** | — | — | — | — | ❌ FAIL |
| Duplicate clustering | P1 | `Cluster` model only; never used | — | — | — | — | ❌ FAIL |
| Evidence validation | P2 | `ValidationResult` model + fixture constants only | — | — | — | — | ❌ FAIL |
| Safe sandbox | P2 | **None** | — | — | — | — | ❌ FAIL |
| Severity / risk scoring | P3 | Fixture-constant scores | — | — | — | — | ❌ FAIL |
| Exploitability context (EPSS/KEV) | P3 | Fixture-constant `threat_intelligence`; UI presentation exists | — | — | — | — | ❌ FAIL (data, not pipeline) |
| AI explanation | P4 | `engine.py` + mock/openai/anthropic providers + sanitizer + validator | `TriageCase` | `AIAnalysis` | ✅ 16 BE tests (mock only) | ✅ via `/api/ai/analyze` (mock-v1) | ✅ PASS (mock AI; paid providers unproven live) |
| Human approval (approve/reject/override) | P4 | `approval_routes.py` + `ApprovalControls.tsx` + in-memory store | analyst_id/reason | `ApprovalState` + audit event | ✅ real-API smoke | ✅ (in-memory only) | ⚠️ PASS at runtime, FAIL on persistence |
| Auditability | P4 | `audit_routes.py`, `AuditTimeline.tsx`, append-only in-memory log | decision | `AuditEvent[]` | ✅ real-API smoke | ✅ (in-memory) | ⚠️ PASS at runtime, FAIL on persistence |
| Safe rendering / injection safety | P4 | text-only rendering, no `dangerouslySetInnerHTML` | untrusted payloads | safe DOM | ✅ 8 FE tests | ✅ | ✅ PASS |
| AI grounding | P4 | sanitizer wraps `<UNTRUSTED>`; validator checks extracted numbers/CVEs against input | case | validated `AIAnalysis` | ✅ 3 hallucination tests (mock only) | ✅ mock-v1 | ⚠️ PASS (mock AI only) |

> Rule applied: a capability is **not complete** because Pydantic models or fixtures exist. Implementation + test + integration + demonstration all failed for Person 1/2/3 capabilities.

---

## 5. Architecture Compatibility

The wiring **Person 4 actually built and verified** works:

```
frontend provider (realProvider)  ──HTTP──>  FastAPI backend (uvicorn, repo root)
   GET  /api/cases                               case_routes
   GET  /api/cases/{id}                          case_routes
   POST /api/cases/{id}/approve|reject|override  approval_routes
   GET  /api/cases/{id}/audit                    audit_routes
   POST /api/ai/analyze/{id}                     ai_routes (engine -> providers)
   GET  /api/dashboard/stats                     dashboard_routes
```

- Endpoint paths/params/bodies match **field-for-field** between `realProvider.ts` and the backend routes (verified by reading both sides).
- CORS: backend trusts exactly `http://localhost:3000`; frontend talks to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) directly, no Next proxy.
- What is missing to make the **problem statement** true is the boundary where Persons 1–3 feed the system: a finding-ingestion endpoint and a pipeline that materializes `Finding → Cluster → ValidationResult → PriorityResult → TriageCase`. None exists, so **no adapter can currently be written** — there is nothing on the left side of the adapter.

---

## 6. Contract Conflicts

`docs/person4-contracts.md` is marked "INITIAL (no Person 1–3 schemas observed)" — correct. Reconciliations:

- **Asset, EvidenceObservation, ValidationResult, PriorityResult, AIAnalysis, ApprovalState, AuditEvent, TriageCase**: backend ↔ frontend fields match exactly (no renames; frontend types are stricter literal unions). ✅
- **`Finding` / `Cluster`**: exist in backend models and the contracts doc, but **not** in `frontend/lib/api/types.ts`. Not a runtime conflict today (no endpoint emits them), but a gap that becomes a conflict the moment ingestion ships. **Resolution required by contract rule:** use an explicit adapter/typed boundary — do **not** rename fields to make it fit.
- **Approve/reject/override responses**: backend returns `ApprovalState`; frontend treats them as `TriageCase`. Low risk (results discarded), but should be typed correctly.
- **Audit**: backend `GET /audit` → 404 when empty; frontend mock → `[]`. Frontend never calls it (uses `caseData.audit`), so latent only.
- **Backend approval guards** (reject-after-approve blocked, override requires reason + valid P1–P4) have **no equivalent in the frontend mock** — mock only checks case existence.

No Person-4-vs-Person-1-3 contract conflict can be assessed because Person 1–3 contracts were never implemented.

---

## 7. End-to-End Workflow (actual, verified)

What **works today** in both mock and real-backend modes:

1. Fetch 6 fixture cases + dashboard stats (real API verified).
2. Open a case; all panels (header, pipeline, evidence, threat intel, priority factors, AI analysis, approval, duplicate cluster, audit) render purely from data objects — no hardcoded fake metrics.
3. Run AI analysis → `mock-v1`, grounded (references only input values; verified `model=mock-v1`, `grounded_on` populated, summary quotes fixture CVSS 8.8 / score 92.5 / CONFIRMED).
4. Approve (double-click confirm) → 200, `ApprovalState APPROVED`, audit event `PENDING → APPROVED`, second approve → 409. Verified against live server.
5. Override CASE-005 P2→P1 → approval `OVERRIDDEN override_priority=P1`, `priority.level` mutated to P1, `p1` stat went 2→3 on the live API. Audit event with metadata `old_priority/new_priority`. Verified.
6. Reject → `REJECTED` with reason. (Route verified; rejection flow shares the same store.)
7. Page refresh: client re-fetches from the same running server → decision retained **while the process lives**.

Where the workflow **cannot go**:

- A raw scanner finding has **no path into the system** (no ingestion endpoint, no normalization, no dedup). `finding_count=3` in fixtures is a static attribute of a hand-written case, not a result of clustering. The UI's "3 FINDINGS → 1 CLUSTER → 1 TRIAGE CASE" visualization is *displayed faithfully* but describes **fixture data, not system behavior**.
- Evidence statuses (`CONFIRMED`, `NOT_CONFIRMED`, `INCONCLUSIVE`) are fixture attributes; no validator ever produces them from live observations. The `NOT_CONFIRMED` contradiction panel renders fixture observations; it is not connected to any scanner-vs-target comparison performed by the system.
- No sandbox, so no "safe validation" claim can be made — the task's Section 27 rule ("if isolation is insufficient, call it what it actually is") applies fully.
- The AI explanation layer never influences priority (priority is static fixture data) — consistent with the "deterministic priority → AI explanation" architecture, but only because the priority is *frozen*, not because it is computed.

---

## 8. Real-World Scenario

**Attempted:** stand up a controlled vulnerable target + open-source scanner + real findings into CyberYukti.

**Result: NOT DEMONSTRABLE — blocked by design, not by tooling.**

- **No ingestion path:** the backend exposes no endpoint that accepts scanner output, so no scanner finding can enter the system regardless of target or scanner. Sections 38.4/38.5/38.6 and §46/§47 therefore fail categorically.
- **Environment:** Docker is not available on this machine (no `docker` on PATH, `docker.exe` not present in Program Files; WSL2 Ubuntu exists but also has no Docker). No scanner binaries installed (`nuclei`, `nikto`, `trivy`, `grype`, `zap` all absent). Python 3.11 + Node 20 present; PyPI and GitHub reachable.
- **Feasibility of the *tooling* side (for future demo; documented in `REAL_WORLD_DEMO.md`):** a local intentionally-vulnerable Flask app and a locally-written Nuclei template are reproducible with freely available software. But because there is nothing to ingest into, running a real scanner would only prove the scanner works — it would prove nothing about CyberYukti. That would violate the task's "do not claim" rules, so it was **not** run as a fake integration proof.

The precise capability that must exist before E2E-001 ("Real Vulnerability → Analyst Case") can pass is a documented Person 1–3 pipeline plus a reproducible target/scanner harness. The recipe (target app, scanner commands, expected artifacts per stage) is in `docs/REAL_WORLD_DEMO.md`.

---

## 9. Security Validation

| Area | Finding | Verdict |
|---|---|---|
| XSS / unsafe HTML | Frontend renders all untrusted data as text; **no** `dangerouslySetInnerHTML`, no `script`/`img` injection (8 UI tests assert querySelector `script`/`img` are null and payloads are present in `textContent`). | ✅ PASS |
| Prompt injection (AI layer) | Sanitizer strips control chars, wraps 30 untrusted fields in `<UNTRUSTED>` tags; system prompt declares tags are data, never instructions; validator checks grounding (numbers/CVEs in output must exist in input). 10 injection payloads + 3 hallucination cases tested — **but against the mock provider only**; no live tests of OpenAI/Anthropic providers. | ⚠️ PASS (mock), unproven (paid providers) |
| Injection → priority | Priority is static fixture data; adversarial text cannot alter it (no path). | ✅ PASS (trivially) |
| Command injection / subprocess | No subprocess/exec/network code exists anywhere in backend. | ✅ PASS (nothing to exploit; also means no validation engine) |
| SSRF / path traversal / file access | No file or outbound-request code in backend. | ✅ PASS (surface absent) |
| Sandbox escape | No sandbox exists to escape. | N/A — flagged as missing capability |
| Secrets / env leakage | No secrets in tree. `.env.example` has empty `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` placeholders. `.env` files are not tracked (`.gitignore` added during review). | ✅ PASS |
| CORS | `allow_origins=["http://localhost:3000"]`, methods/headers `*`, credentials=True. Narrow origin list (good), wildcard methods/headers acceptable for local tool. | ⚠️ OK for local demo; document before wider deployment |
| Auth / authorization | No authentication or per-analyst authorization anywhere; `analyst-1` is hardcoded in frontend POST bodies and accepted verbatim by backend. Acceptable for a local demo, **must** be documented as such, never marketed as production auth. | ⚠️ Manual identity only |

---

## 10. Free / Open-Source Audit

| Dependency | License/Vendor | Free? | Open source? | Required? | Verdict |
|---|---|---|---|---|---|
| Next.js 14 / React 18 / TypeScript / Tailwind / Vitest / Testing Library / eslint | MIT | ✅ | ✅ | production & dev | OK |
| FastAPI / Starlette / Uvicorn / Pydantic / httpx / python-dotenv | BSD/MIT | ✅ | ✅ | backend | OK |
| openai client (`openai`) | MIT | ✅ (library) | ✅ | optional — requires `OPENAI_API_KEY` to do anything | ⚠️ **OPTIONAL**; empty key → automatic mock fallback |
| anthropic client | MIT | ✅ (library) | ✅ | optional — requires `ANTHROPIC_API_KEY` | ⚠️ **OPTIONAL**; empty key → automatic mock fallback |
| OpenAI / Anthropic **services** | proprietary SaaS | ❌ paid | ❌ | optional with free fallback | **OPTIONAL / NOT BLOCKING** (free mock path always exists) |
| pytest / pytest-asyncio / ruff | MIT | ✅ | ✅ | dev | OK |

**Zero mandatory paid dependencies.** A free deterministic mock AI completes analysis offline. No local OSS LLM (e.g., Ollama) integration exists — a nice-to-have, not a blocker.

---

## 11. Deployment Validation

- **No Dockerfile, no compose file, no Makefile, no shell scripts exist anywhere** (glob verified). `docker compose up --build` is impossible as written.
- Verified manual path (runs on this machine):
  - Backend: `python -m pip install -e backend` (deps already installable from PyPI) then from **repo root**: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`. Note: run-from-root is mandatory because `main.py` imports `backend.app.*`.
  - Frontend: `npm install` → `npm run dev` (default `NEXT_PUBLIC_USE_MOCK` unset → mock; `NEXT_PUBLIC_API_URL` default `http://localhost:8000`).
- Backend starts and `GET /health` → `{"status":"ok"}`. All routes exercised (see §12).
- **Reproducibility verdict:** a documented manual path works, but the "zero to demo with one command" gate fails. Needs a Dockerfile + compose and a run-from-root convention or packaging fix.

---

## 12. Test Results

| Check | Command | Result |
|---|---|---|
| Backend unit (AI mock) | `python -m pytest -q` (backend) | ✅ **16 passed** in ~1s (7 functions incl. 10-param injection parametrization; no route/API tests exist) |
| Frontend injection UI | `npm test` (frontend) | ✅ **8 passed** |
| Frontend build | `npm run build` | ✅ compiled, 4 routes, lint+types ok |
| Frontend lint | `npm run lint` | ✅ no warnings/errors |
| Real API smoke (live server) | manual HTTP probes | ✅ list/get/stats/approve(200+400+409)/override(200, P2→P1, stats p1 2→3)/reject route present/analyze(200, mock-v1)/404 on missing case/audit append |
| **Persistence** | restart server → re-GET | ❌ **FAIL: approval reset to PENDING, audit emptied, ai_analysis cleared, override reverted P2.** Backend is entirely in-memory (dicts in `case_routes.py`), no DB/file. |

Test coverage gaps: no tests for routes, approval flow, dashboard, validator, sanitizer, or any pipeline logic (because none exists). All backend tests cover only the **mock AI provider**.

---

## 13. Failure Tests (deliberate)

| Failure injected | Behavior | Verdict |
|---|---|---|
| `analyst_id` missing on approve | 400 `analyst_id is required` | ✅ fails safe |
| Approve an already-approved case | 409 `Case already decided` | ✅ fails safe |
| GET unknown case / audit of empty trail | 404 with `detail` | ✅ fails safe (note: FE mock returns `[]` instead — divergence) |
| Backend down while frontend runs (real mode) | `realProvider` catches and **silently falls back to mock** | ⚠️ acceptable for demo, but it *masks* outages in prod-ish use; documented in code via `console.warn` |
| AI analysis failure | engine retries, then falls back to `MockProvider`, then to a hardcoded minimal analysis | ✅ never crashes the request |
| Server restart | **All decisions, audits, analyses lost** | ❌ FAIL (see persistence) |
| Malformed/scanner input | Not applicable — no input endpoint exists | ❌ (capability missing) |

---

## 14. Known Problems

**Critical (blocking):**
1. No finding **ingestion** endpoint. (P1 missing)
2. No **normalization** / **deduplication** / **clustering** logic; `Finding`/`Cluster` models unused. (P1 missing)
3. No **evidence validation** engine or **sandbox**; `CONFIRMED`/`NOT_CONFIRMED`/`INCONCLUSIVE` are fixture constants. (P2 missing)
4. No **deterministic priority computation**; `score`/`level`/`formula_version` are fixture constants; override mutates `priority.level` without recomputation; the UI statement *"Score is computed deterministically from the validated factors"* is not backed by code. (P3 missing)
5. **No persistence** — approvals, audits, analyses disappear on restart (mock **and** real backend).
6. No **Dockerfile/compose**; run-from-root import requirement un-documented in repo.

**Non-critical but real:**
7. Duplicate `AIAnalysis` model (`cases/models.py` vs `ai/schemas.py`); two independent case stores (`case_routes` vs `ai_routes`).
8. Audit `prev_hash` = previous `event_id`, not a hash; semantic-name mismatch.
9. Audit divergence mock-vs-real (mock seeds lifecycle events; real backend starts empty / 404).
10. Approve/reject/override response typed as `TriageCase` in FE but returns `ApprovalState` on backend.
11. CASE-005 confidence `0.82` (backend) vs `0.90` (frontend mock, docs).
12. Frontend mock lacks the backend's approval-state guards (e.g., no reject-after-approve block).
13. Docs drift: `docs/frontend-ui-documentation.md` references removed components (`StatCard`, `PriorityChart`, `AssetPanel`, `DuplicateSourcesPanel`, demo banner); needs update to the new SOC workbench components.
14. Hardcoded `analyst-1` identity; no auth concept (fine for local demo, must be stated).
15. `docs/person4-failure-checklist.md` references an env-toggle-in-localStorage mechanism that does not exist.
16. Revision-0-suggestion from earlier frontend work: `CaseTable` evidence filter bug (space vs underscore) — **fixed in this review**; re-verified green.

---

## 15. Merge Blockers (genuine)

Mapping to the task's hard conditions (Section 38):

| # | Condition | State |
|---|---|---|
| 38.2 | Real backend integration works | ❌ Only fixtures can be served; ingestion pipeline absent |
| 38.3 | Core workflow only works in mock mode | ❌ True — even the "real" backend is a fixture server |
| 38.4 | No realistic controlled target demonstrated | ❌ True (no ingestion path; tree contains no harness) |
| 38.5 | No real scanner/finding ingestion demonstrated | ❌ True |
| 38.6 | Deduplication fake/hardcoded | ❌ True (`finding_count` is a fixture attribute) |
| 38.7 | Evidence validation fake/hardcoded | ❌ True |
| 38.8 | Priority arbitrary/AI-controlled | ⚠️ Scores are pre-baked constants; not AI-controlled, but not computed either |
| 38.9 | Approval does not persist | ⚠️ Works in-process; does not persist across restart |
| 38.10 | Audit trail inaccurate | ⚠️ Accurate while running; not durable |
| 38.18 | Integrated system does not satisfy problem statement | ❌ True — it cannot receive/validate real findings |

---

## 16. Recommendation

# DO NOT MERGE

With the repository as-is, merging Person 4 means shipping a beautiful, secure, well-typed **fixture viewer with a real approval/audit API and a guarded mock AI layer** — and calling it "an autonomous vulnerability triage & evidence engine." That is not what the problem statement asks for, and the review rules forbid excusing it.

**Conditions under which a future review should pass (MERGE):**
1. A Person-1-style ingestion endpoint (e.g., `POST /api/findings`) that normalizes and clusters raw scanner findings into a `Cluster` with real dedup evidence (`dedup_method`, `dedup_confidence`).
2. A Person-2-style safe validation layer whose observations are produced by **real, time-boxed probes** against a target (document isolation honestly: what it can/cannot touch).
3. A Person-3-style **deterministic priority function** (same factors in → same score/level out) superseding the fixture constants, with `formula_version` bumped/bindable.
4. **Persistence** (SQLite/file) so approvals, overrides, and audit events survive restart (then re-run the restart test — §12 — to green).
5. A reproducible **Docker** target+scanner harness, and re-run E2E-001 (§7 of `REAL_WORLD_DEMO.md`) with real artifacts at every stage.
6. Route-level tests for the above; keep the existing FE injection tests and BE mock-AI tests, and add validator/sanitizer unit tests.

Person 4's own deliverables should be kept as the integration surface; nothing here suggests rewrites of the UI or contracts.

---

## 17. Evidence

- `prompts.txt` — scope split (P1/P2/P3 explicitly out of Person 4's scope and never implemented).
- `docs/person4-contracts.md` — "INITIAL (no Person 1–3 schemas observed)".
- Code: `backend/app/cases/models.py` (unused `Finding`/`Cluster`), `backend/app/mock/fixtures.py` (all case data), `backend/app/api/*.py` (routes; two case stores; in-memory), `backend/app/ai/engine.py` (mock fallback chain), `frontend/lib/api/{types,realProvider,mockProvider}.ts`, `frontend/app/**` and `frontend/components/**` (SOC workbench, pure data rendering).
- Test runs: backend `16 passed`; frontend `8 passed`; `npm run build` clean; `npm run lint` clean.
- Live API probes (this review): approvals 200/400/409, override P2→P1 with `p1` stat 2→3, AI `model=mock-v1` grounded output, 404s; **restart test:** approval reset to `PENDING`, audit cleared, override reverted, analysis dropped.
- This review session fixed one real frontend bug (evidence filter) — re-verified green.
</think>Now the real-world demo doc (honest about what can and cannot be demonstrated today):

<｜DSML｜tool_calls>
<｜DSML｜invoke name="write">
<｜DSML｜parameter name="content" string="true"># Real-World Demo — Reproducible Plan & Current State

**Purpose:** give the judges a fully reproducible demonstration of the ACSC system against a realistic, intentionally vulnerable, legally controlled target.

**Status (honest):** two of three layers exist and are demonstrated (target/scanner tooling feasibility + CyberYukti UI/API on fixtures). The **connector does not exist**: there is no finding-ingestion endpoint or normalization/dedup/validation/priority pipeline in the repository, so scanner output **cannot enter CyberYukti today**. This document therefore contains (A) the not-yet-runnable architecture, (B) the exact commands to build the target + scanner + artifacts so the demo is ready the moment the pipeline lands, and (C) what *is* demonstrable today. Nothing here claims an integration that does not exist.

---

## 1. Architecture (target)

```
LOCAL SCANNERS                          CYBERYUKTI STACK
─────────────────                       ─────────────────
nuclei (HTTP templates)      ─┐
semgrep (SAST rules)         ─┼──(RAW FINDINGS)──▶ [ NOT IMPLEMENTED ]
pip-audit (dependency scan)  ─┘                        │
        │                                    ingestion → normalize → dedup
        ▼                                        → validate (sandbox)
INTENTIONALLY VULNERABLE                         → threat/severity context
LOCAL FLASK APP (target)                          → priority (deterministic)
        │                                        → AI explanation
        ▼                                        → analyst decision
        └──────────────────────────────(HTTPS)──▶ → audit trail
                                                    (FastAPI :8000 ⇄ Next.js :3000)
```

---

## 2. Requirements

| Software | Version/Where | Free? |
|---|---|---|
| Python | 3.11+ (this machine: 3.11) | ✅ |
| Node.js / npm | 20+ / 10+ | ✅ |
| FastAPI/uvicorn stack | `pip install -e backend` | ✅ |
| Flask (for the vulnerable target) | `pip install flask` — reachable from PyPI (verified) | ✅ |
| nuclei | standalone Windows exe from GitHub releases (GitHub reachable, verified) | ✅ |
| semgrep | `pip install semgrep` (PyPI reachable) | ✅ |
| pip-audit | `pip install pip-audit` (PyPI reachable) | ✅ |
| Docker | **desired but NOT available on this machine** — not required if targets/scanners run natively | optional |
| OpenAI/Anthropic keys | optional — system falls back to free `mock-v1` automatically | optional/paid |

No paid SaaS is needed anywhere.

---

## 3. Controlled Vulnerable Target (reproducible, intentional)

Create `demo-target/app.py` — a deliberately vulnerable Flask app (SQL injection in `/search`, reflected XSS in `/echo`, and a pinned old dependency for the dependency scan):

```python
from flask import Flask, request, make_response  # NOQA: E402
import sqlite3

app = Flask(__name__)

def db():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE users (id INTEGER, name TEXT, pwd TEXT)")
    c.executemany("INSERT INTO users VALUES (?,?,?)",
                  [(1,"admin","secret1"),(2,"bob","pw2")])
    return c

@app.route("/search")
def search():
    q = request.args.get("q", "")
    c = db()
    # INTENTIONAL SQLi: raw user input concatenated into query
    rows = c.execute("SELECT name FROM users WHERE name LIKE '%" + q + "%'").fetchall()
    return {"count": len(rows), "names": [r[0] for r in rows]}

@app.route("/echo")
def echo():
    # INTENTIONAL reflected XSS
    return make_response("<div>You said: " + request.args.get("msg", "") + "</div>")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
```

```text
# demo-target/requirements.txt
flask==2.3.3
Werkzeug==2.0.3          # intentionally old → pip-audit finding
```

Start: `python demo-target/app.py` → `http://127.0.0.1:5050`.

---

## 4. Scanners (real, open source) — exact commands

**Scanner A — nuclei (web):** download exe from GitHub releases, then:

```powershell
nuclei.exe -u http://127.0.0.1:5050 -t sqli-template.yaml -o artifacts/nuclei.jsonl
```

with `sqli-template.yaml` (a template for the intentional SQLi):

```yaml
id: local-flask-sqli
info:
  name: Demo Flask search SQL injection
  severity: high
requests:
  - method: GET
    path:
      - "{{BaseURL}}/search?q=%27%20OR%20%271%27%3D%271"
    matchers:
      - type: contains
        words: ["admin"]
```

**Scanner B — semgrep (SAST):**
```powershell
pip install semgrep
semgrep scan --config "p/python" demo-target/app.py --json > artifacts/semgrep.json
```

**Scanner C — pip-audit (dependency):**
```powershell
pip install pip-audit
pip-audit -r demo-target/requirements.txt --format json > artifacts/pip-audit.json
```

Each scanner produces a distinct **raw finding** for the *same underlying issue class*, which is exactly the "3 findings → 1 cluster → 1 case" duplicate scenario the pipeline must prove (not `finding_count=3` stuffed into a fixture).

---

## 5. Run CyberYukti (today's truthful demo mode)

**Backend (from repo root — imports require `backend.app.*`, verified):**

```powershell
python -m pip install -e backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Frontend (mock or real):**

```powershell
cd frontend
npm install
# demo mode (default):
npm run dev                # NEXT_PUBLIC_USE_MOCK unset → mock provider
# or against the real backend:
$env:NEXT_PUBLIC_USE_MOCK="false"; $env:NEXT_PUBLIC_API_URL="http://localhost:8000"; npm run dev
```

Expected: dashboard at `http://localhost:3000` with 6 fixture cases (P1×2, P2×2, P3×1, P4×1), priority queue, pipeline strip, triage table.

---

## 6. What is demonstrable TODAY (verified in this review)

| Capability | How to show it | Verified |
|---|---|---|
| Analyst dashboard & triage (fixtures) | open `/` and `/cases` | ✅ |
| Case workspace (evidence, threat intel, priority factors, duplicate cluster, AI panel) | open `/cases/CASE-001` | ✅ |
| AI explanation, grounded + guarded | POST `/api/ai/analyze/CASE-001` → `model=mock-v1`, `grounded_on` set | ✅ |
| Inject an untrusted string into evidence | 8 frontend tests: no `script`/`img`, payload shown as text | ✅ |
| Human approval | POST approve → `APPROVED` + audit `PENDING→APPROVED`; 2nd approve → 409 | ✅ |
| Override | override CASE-005 P2→P1 → `OVERRIDDEN override_priority=P1`, audit `old_priority/new_priority`, stats `p1` 2→3 | ✅ |
| Audit trail (who/what/when/before/after/why) | GET `/api/cases/CASE-001/audit` after approve | ✅ |
| AI prompt-injection defense | backend: 16 tests (10 payloads) on mock provider; sanitizer wraps `<UNTRUSTED>`, validator checks grounding | ✅ |
| Persistence across restart | NOT demonstrated — **fails** (approval→PENDING, audit empty, override reverted) | ❌ |

---

## 7. Judge Demonstration (ONCE THE PIPELINE + REAL DEMO EXIST)

1. Start target: `python demo-target/app.py` (Section 3).
2. Run Scanner A, B, C (Section 4) → 3 raw findings → `artifacts/*.json`.
3. `POST /api/findings` (to be built by Person 1) with the three findings.
4. Show CyberYukti: one cluster → one triage case, `finding_count=3`, `sources=[nuclei, semgrep, pip-audit]`, dedup evidence (`dedup_method`, `dedup_confidence`).
5. Open the case → risk context (CVSS/EPSS/KEV) → deterministic priority (score + `formula_version`).
6. POST `/api/ai/analyze/{case_id}` → grounded explanation with `grounded_on` provenance.
7. Analyst decision: approve / reject-with-reason / override-with-reason → UI + audit update.
8. Restart the backend → **re-open the case → decision and audit must still be present** (persistence gate).
9. Prompt-injection round: scan once more with a poisoned finding; show it rendered as inert text and priority unchanged.

Capture at every step: `artifacts/nuclei.jsonl`, `semgrep.json`, `pip-audit.json`, normalized findings, cluster, `validation_result`, `priority_result`, case JSON, `AIAnalysis`, approval payload, audit log.

---

## 8. Failure Recovery

| Failure | Action |
|---|---|
| uvicorn won't start | Run from **repo root** (`backend.app.main:app`); verify `pip install -e backend` ran |
| frontend won't build | `npm install` then `npm run dev`; confirm ports 3000/8000 free |
| Deliberate backend outage (demo) | frontend `realProvider` falls back to mock with a `console.warn` — show the console line; restart backend to restore real mode |
| AI key missing | expected — free `mock-v1` fallback auto-selected (`USE_MOCK_AI=true` or no key) |
| Anthropic/OpenAI import error | install `openai`/`anthropic` from PyPI (declared deps); or set `USE_MOCK_AI=true` |
| Scanner/target tools absent | everything above is pip/npm/GitHub-free-download installable; PyPI & GitHub were verified reachable from this machine |

---

## 9. Honest Go/No-Go Statement

The **tooling** described here is 100% free/open-source and reproducible. The blocker is purely inside the repo: **no finding-ingestion endpoint and no normalization/dedup/validation/priority engine exist**, so "Real Vulnerability → Analyst Case" (E2E-001) cannot be executed today. Re-running this document after Person 1–3 deliverables land (plus persistence, §6) is the acceptance path. Until then we present the demo in Section 6 and explicitly do **not** claim real-finding ingestion.