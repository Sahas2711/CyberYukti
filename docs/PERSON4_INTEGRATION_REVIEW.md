# Person 4 Integration Review

**Repository:** github.com/Sahas2711/CyberYukti
**Reviewer role:** Integration engineer / security architect / QA lead / release gatekeeper
**Date:** 2026-09-11
**Scope of verdict:** Whether the Person 4 branch (this repository's entire current implementation) can be merged such that the complete "Autonomous Vulnerability Triage & Evidence Engine" problem statement is satisfied end-to-end.

---

## 1. Executive Decision

# DO NOT MERGE

Person 4's own scope is high quality and internally consistent (UI, typed provider layer, approval/override/reject, audit trail, AI guardrails, injection-safe rendering — all tested and working against the real backend API). It cannot be merged into a working product, however, because the other three persons' deliverables — the engine of the problem statement — do not exist anywhere in this repository. There is no finding-ingestion endpoint, no normalization, no deduplication/clustering logic, no evidence-validation sandbox or probes, and no deterministic priority computation (scores are pre-baked fixture constants). The system only runs on hand-crafted demo fixtures. Per the hard merge-gate rules (task Sections 38.2-38.8, 38.18; 46-48), this is a DO NOT MERGE.

---

## 2. Repository State

Facts gathered from `git`, not assumptions:

| Item | Actual state |
|---|---|
| Remote (owner/name) | `https://github.com/Sahas2711/CyberYukti` (`origin`) |
| Default branch | `main` |
| Commits on `main` | 0 (zero) — repository has never received a commit |
| Current branch | `main` (before this review) |
| All branches | `main` only |
| Person 1 branch | Does not exist |
| Person 2 branch | Does not exist |
| Person 3 branch | Does not exist |
| Person 4 branch | Did not exist (created as `person4/integration` during this review) |
| Integration branch | Did not exist |
| Open pull requests | None discovered |
| Tracking status | Entire working tree (backend/, frontend/, docs/, prompts.txt, .env.example) was untracked |
| Unterminated/ignored config | No root `.gitignore` existed (created during review); `frontend/.gitignore` only covered node_modules/.next |
| Stashes / reflog | None |

**Implication:** the "four parallel persons" narrative exists only in `prompts.txt` and `docs/person4-contracts.md`. In reality there is a single uncommitted tree that implements only Person 4's vertical slice, with Person 1/2/3 modelled only as Pydantic types (`Finding`, `Cluster`) and pre-baked fixture dictionaries. That is the single most important finding of this review.

---

## 3. Branch Comparison

There are no Person branches to diff. The comparison below is Person 1/2/3 scope vs what actually exists in the tree (which is Person 4's implementation).

| Scope (per prompts.txt) | Expected deliverable | Actual implementation | Status |
|---|---|---|---|
| Person 1 | Scanner ingestion, canonical schema, normalization, dedup, backend foundation | `Finding` & `Cluster` Pydantic models in `backend/app/cases/models.py` — defined, never instantiated. No ingestion endpoint, no normalization, no dedup code. All cases from `backend/app/mock/fixtures.py`. | ABSENT |
| Person 2 | Evidence extraction, Docker sandbox, validation probes | `ValidationResult` / `EvidenceObservation` models + fixture data only. No sandbox, no probes, no subprocess, no network-validation code (grep: 0 hits). | ABSENT |
| Person 3 | NVD/EPSS/KEV/OSV enrichment, risk scoring, P1-P4 prioritization formula | `threat_intelligence` (cvss/epss/kev) and `priority` (score/level/factors/formula_version) are hardcoded fixture constants. No enrichment calls, no score function. Override writes `priority.level` without recomputing score. | ABSENT |
| Person 4 | AI explanation engine, dashboard, case views, approval workflow, audit, guardrails, typed API, frontend | Implemented and verified (see Section 12). | PRESENT |

### Overlaps / conflicts / duplicates found

| Item | Finding |
|---|---|
| Duplicate AIAnalysis model | Defined twice: `backend/app/cases/models.py` and `backend/app/ai/schemas.py` (identical structure, different classes). Works only because routes return raw dicts. |
| Duplicate case store | `case_routes.py` and `ai_routes.py` each build their own `_cases_store`; the AI route operates on a stale copy (mutations in one are invisible to the other). |
| Frontend filter bug (fixed in review) | `EVIDENCE_OPTIONS` contained `NOT CONFIRMED` (space) while `evidence.status` is `NOT_CONFIRMED` (underscore) - filter never matched. Fixed in `frontend/components/dashboard/CaseTable.tsx`. Re-verified green. |
| Audit semantics divergence | Real backend seeds no lifecycle audit events (fresh case audit = empty; GET /audit returns 404). Frontend mock seeds clustered/validated/prioritized/analysis events. |
| prev_hash naming | Stores the previous event_id, not a cryptographic/structural hash. Chain integrity is structural only. |
| Approval response type | Backend returns the approval object; frontend types responses as TriageCase (`realProvider.ts`). Safe at runtime (UI ignores body and re-fetches). |
| Fixture divergence | CASE-005 evidence confidence = 0.82 (backend fixtures) vs 0.90 (frontend mock + docs). |

---

## 4. Problem Statement Mapping

Official problem statement (repo `prompts.txt`): build an agentic system that receives raw security findings, removes duplicates, validates evidence in a safe sandbox, and produces prioritized analyst-ready cases.

| Requirement | Responsible | Input | Output | Test | Real-world demo | Status |
|---|---|---|---|---|---|---|
| Finding normalization | P1 | — | — | — | — | FAIL |
| Duplicate clustering | P1 | — | — | — | — | FAIL |
| Evidence validation | P2 | — | — | — | — | FAIL |
| Safe sandbox | P2 | — | — | — | — | FAIL |
| Severity / risk scoring | P3 | — | — | — | — | FAIL |
| Exploitability context (EPSS/KEV) | P3 | — | — | — | — | FAIL (data, not pipeline) |
| AI explanation | P4 | TriageCase | AIAnalysis | 16 BE tests (mock only) | /api/ai/analyze (mock-v1) | PASS (mock AI; paid providers unproven live) |
| Human approval | P4 | analyst_id/reason | ApprovalState + audit | real-API smoke | in-flight runtime | PASS at runtime, FAIL on persistence |
| Auditability | P4 | decision | AuditEvent[] | real-API smoke | in-flight runtime | PASS at runtime, FAIL on persistence |
| Safe rendering / injection safety | P4 | untrusted payloads | safe DOM | 8 FE tests | yes | PASS |
| AI grounding | P4 | case | validated AIAnalysis | 3 hallucination tests (mock only) | mock-v1 | PASS (mock AI only) |

Rule applied: a capability is not complete because models or fixtures exist. Implementation + test + integration + demonstration all failed for Person 1/2/3 capabilities.

---

## 5. Architecture Compatibility

The wiring Person 4 actually built and verified works:

```
frontend provider (realProvider)  --HTTP-->  FastAPI backend (uvicorn, repo root)
   GET  /api/cases                               case_routes
   GET  /api/cases/{id}                          case_routes
   POST /api/cases/{id}/approve|reject|override  approval_routes
   GET  /api/cases/{id}/audit                    audit_routes
   POST /api/ai/analyze/{id}                     ai_routes (engine -> providers)
   GET  /api/dashboard/stats                     dashboard_routes
```

- Endpoint paths/params/bodies match field-for-field between `realProvider.ts` and the backend routes (verified by reading both sides).
- CORS: backend trusts exactly http://localhost:3000; frontend talks to `NEXT_PUBLIC_API_URL` (default http://localhost:8000) directly, no Next proxy.
- Missing to make the problem statement true: the boundary where Persons 1-3 feed the system - a finding-ingestion endpoint and a pipeline that materializes Finding -> Cluster -> ValidationResult -> PriorityResult -> TriageCase. None exist, so no adapter can currently be written (nothing on the left side of the adapter).

---

## 6. Contract Conflicts

`docs/person4-contracts.md` is marked "INITIAL (no Person 1-3 schemas observed)" - correct.

- Asset, EvidenceObservation, ValidationResult, PriorityResult, AIAnalysis, ApprovalState, AuditEvent, TriageCase: backend-frontend fields match exactly (no renames; frontend types are stricter literal unions). OK.
- Finding / Cluster: exist in backend models and the contracts doc, but not in `frontend/lib/api/types.ts`. Not a runtime conflict today. Resolution required by contract rule: use an explicit adapter/typed boundary; do not rename fields to fit.
- Approve/reject/override responses: backend returns ApprovalState; frontend treats them as TriageCase. Low risk (results discarded).
- Audit: backend GET /audit -> 404 when empty; frontend mock -> []. Frontend never calls it (uses caseData.audit).
- Backend approval guards (reject-after-approve blocked, override requires reason + P1-P4) have no equivalent in the frontend mock.

No Person-4-vs-Person-1-3 contract conflict can be assessed because Person 1-3 contracts were never implemented.

---

## 7. End-to-End Workflow (actual, verified)

What works today in both mock and real-backend modes:
1. Fetch 6 fixture cases + dashboard stats (real API verified).
2. Open a case; all panels render purely from data objects - no hardcoded fake metrics.
3. Run AI analysis -> mock-v1, grounded (model=mock-v1, grounded_on populated, summary quotes fixture CVSS 8.8 / score 92.5 / CONFIRMED).
4. Approve (double-click confirm) -> 200, APPROVED, audit event PENDING->APPROVED; second approve -> 409. Verified live.
5. Override CASE-005 P2->P1 -> OVERRIDDEN override_priority=P1, priority.level mutated, p1 stat 2->3 on the live API; audit metadata old/new priority. Verified.
6. Reject -> REJECTED with reason (route shares the store).
7. Page refresh while the same server runs: decision retained (client re-fetches same server).

Where the workflow cannot go:
- A raw scanner finding has no path into the system. finding_count=3 is a static attribute of a hand-written case, not a clustering result. The UI's "3 FINDINGS -> 1 CLUSTER -> 1 TRIAGE CASE" visualization is displayed faithfully but describes fixture data, not system behavior.
- Evidence statuses (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE) are fixture attributes; no validator produces them from live observations.
- No sandbox, so no "safe validation" claim exists. (Task Section 27 rule applied: call it what it actually is.)
- The AI explanation layer never influences priority - consistent with "deterministic priority -> AI explanation", but only because priority is frozen, not because it is computed.

---

## 8. Real-World Scenario

**Attempted:** stand up a controlled vulnerable target + open-source scanner + real findings into CyberYukti.

**Result: NOT DEMONSTRABLE - blocked by design, not by tooling.**

- No ingestion path: the backend exposes no endpoint that accepts scanner output, so no finding can enter the system regardless of target or scanner. Task Sections 38.4/38.5/38.6 and 46/47 fail categorically.
- Environment: Docker unavailable on this machine (no docker on PATH, no docker.exe in Program Files; WSL2 Ubuntu exists but no Docker inside it either). No scanner binaries installed (nuclei/nikto/trivy/grype/zap absent). Python 3.11 + Node 20 present; PyPI and GitHub reachable (verified).
- Feasibility of the tooling side (documented in REAL_WORLD_DEMO.md): a local intentionally-vulnerable Flask app and a locally-written Nuclei template are reproducible with freely available software. But with nothing to ingest into, running a real scanner would only prove the scanner works - it would prove nothing about CyberYukti. Per the task's anti-fake rules it was not run as a fake integration proof.

The precise capability that must exist before E2E-001 ("Real Vulnerability -> Analyst Case") can pass is a documented Person 1-3 pipeline plus a reproducible target/scanner harness (recipe in docs/REAL_WORLD_DEMO.md).

---

## 9. Security Validation

| Area | Finding | Verdict |
|---|---|---|
| XSS / unsafe HTML | All untrusted data rendered as text; no dangerouslySetInnerHTML, no script/img injection (8 UI tests assert script/img null and payloads present in textContent). | PASS |
| Prompt injection (AI layer) | Sanitizer strips control chars, wraps 30 untrusted fields in <UNTRUSTED> tags; system prompt declares tags are data; validator checks grounding (numbers/CVEs in output must exist in input). 10 injection payloads + 3 hallucination cases tested - against the mock provider only. | PASS (mock), unproven (paid providers) |
| Injection -> priority | Priority is static fixture data; adversarial text cannot alter it (no path). | PASS (trivially) |
| Command injection / subprocess | No subprocess/exec/network code anywhere in backend. | PASS (surface absent; also means no validation engine) |
| SSRF / path traversal / file access | No file or outbound-request code in backend. | PASS (surface absent) |
| Sandbox escape | No sandbox exists to escape. | N/A - noted as missing capability |
| Secrets / env leakage | No secrets in tree; .env.example has empty placeholders; .env files ignored (gitignore added during review). | PASS |
| CORS | allow_origins=[http://localhost:3000], methods/headers *, credentials True. Narrow origin list; wildcards acceptable for local tool. | OK for local demo; document before wider use |
| Auth / authorization | None; analyst-1 hardcoded and accepted verbatim. Acceptable for a local demo; must be documented. | Manual identity only |

---

## 10. Free / Open-Source Audit

| Dependency | License/Vendor | Free? | Open source? | Required? | Verdict |
|---|---|---|---|---|---|
| Next.js/React/TS/Tailwind/Vitest/Testing Library/eslint | MIT | yes | yes | prod+dev | OK |
| FastAPI/Starlette/Uvicorn/Pydantic/httpx/python-dotenv | BSD/MIT | yes | yes | backend | OK |
| openai client | MIT | yes | yes | optional (needs key) | OPTIONAL |
| anthropic client | MIT | yes | yes | optional (needs key) | OPTIONAL |
| OpenAI/Anthropic services | proprietary SaaS | paid | no | optional with free fallback | OPTIONAL / NOT BLOCKING |
| pytest/pytest-asyncio/ruff | MIT | yes | yes | dev | OK |

Zero mandatory paid dependencies. A free deterministic mock AI completes analysis offline. No local OSS LLM (e.g., Ollama) integration exists - a nice-to-have, not a blocker.

---

## 11. Deployment Validation

- No Dockerfile, compose file, Makefile, or shell scripts exist anywhere (glob verified). docker compose up --build is impossible as written.
- Verified manual path on this machine:
  - Backend: python -m pip install -e backend, then from repo root: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000. Run-from-root is mandatory because main.py imports backend.app.*.
  - Frontend: npm install -> npm run dev (default NEXT_PUBLIC_USE_MOCK unset = mock; NEXT_PUBLIC_API_URL default http://localhost:8000).
  - GET /health -> {"status":"ok"}; all routes exercised (Section 12).
- Reproducibility verdict: a documented manual path works; the one-command zero-to-demo gate fails. Needs Dockerfile + compose and a run-from-root convention or packaging fix.

---

## 12. Test Results

| Check | Command | Result |
|---|---|---|
| Backend unit (AI mock) | python -m pytest -q (backend) | 16 passed (~1s); 7 functions incl. 10-param injection parametrization; no route/API tests exist |
| Frontend injection UI | npm test (frontend) | 8 passed |
| Frontend build | npm run build | clean, 4 routes, lint+types ok |
| Frontend lint | npm run lint | no warnings/errors |
| Real API smoke (live server) | manual HTTP probes | list/get/stats/approve(200+400+409)/override(200, P2->P1, stats p1 2->3)/reject present/analyze(200, mock-v1)/404s/audit append |
| Persistence | restart server -> re-GET | FAIL: approval reset PENDING, audit emptied, ai_analysis cleared, override reverted P2. Backend entirely in-memory (dicts in case_routes). No DB/file. |

Test coverage gaps: no tests for routes, approval flow, dashboard, validator, sanitizer, or pipeline (none exists). All backend tests cover only the mock AI provider.

---

## 13. Failure Tests (deliberate)

| Failure injected | Behavior | Verdict |
|---|---|---|
| analyst_id missing on approve | 400 "analyst_id is required" | fails safe |
| Approve already-decided case | 409 "Case already decided" | fails safe |
| GET unknown case / audit of empty trail | 404 with detail | fails safe (FE mock returns [] instead - divergence) |
| Backend down while frontend runs (real mode) | realProvider catches and silently falls back to mock (console.warn) | OK for demo; masks outages - documented |
| AI analysis failure | engine retries, falls back to MockProvider, then hardcoded minimal analysis | never crashes the request |
| Server restart | all decisions/audits/analyses lost | FAIL (persistence) |
| Malformed/scanner input | not applicable - no input endpoint exists | capability missing |

---

## 14. Known Problems

Critical (blocking):
1. No finding ingestion endpoint (P1 missing).
2. No normalization / deduplication / clustering logic; Finding/Cluster models unused (P1 missing).
3. No evidence validation engine or sandbox; CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE are fixture constants (P2 missing).
4. No deterministic priority computation; score/level/formula_version are fixture constants; override mutates priority.level without recomputation; the UI statement "Score is computed deterministically from the validated factors" is not backed by code (P3 missing).
5. No persistence - approvals, audits, analyses disappear on restart (mock and real backend).
6. No Dockerfile/compose; run-from-root import requirement undocumented in repo.

Non-critical but real:
7. Duplicate AIAnalysis model (cases/models.py vs ai/schemas.py); two independent case stores (case_routes vs ai_routes).
8. Audit prev_hash = previous event_id, not a hash; semantic-name mismatch.
9. Audit divergence mock-vs-real (mock seeds lifecycle events; real backend starts empty / 404).
10. Approve/reject/override response typed as TriageCase in FE but returns ApprovalState on backend.
11. CASE-005 confidence 0.82 (backend) vs 0.90 (frontend mock, docs).
12. Frontend mock lacks the backend approval-state guards.
13. Docs drift: frontend-ui-documentation.md references removed components (StatCard, PriorityChart, AssetPanel, DuplicateSourcesPanel, demo banner); needs update to the SOC workbench components.
14. Hardcoded analyst-1 identity; no auth concept (fine for local demo, must be stated).
15. person4-failure-checklist.md references an env-toggle-in-localStorage mechanism that does not exist.
16. CaseTable evidence filter bug (space vs underscore) - fixed in this review; re-verified green.

---

## 15. Merge Blockers (genuine)

Mapping to the task's hard conditions (Section 38):
- 38.2 Real backend integration works: FAIL - only fixtures can be served; ingestion pipeline absent.
- 38.3 Core workflow only works in mock mode: FAIL - even the "real" backend is a fixture server.
- 38.4 No realistic controlled target demonstrated: FAIL - no ingestion path; no harness in tree.
- 38.5 No real scanner/finding ingestion demonstrated: FAIL.
- 38.6 Deduplication fake/hardcoded: FAIL - finding_count is a fixture attribute.
- 38.7 Evidence validation fake/hardcoded: FAIL.
- 38.8 Priority arbitrary/AI-controlled: partial - scores pre-baked constants; not AI-controlled, but not computed.
- 38.9 Approval does not persist: partial - works in-process; not durable.
- 38.10 Audit trail inaccurate: partial - accurate while running; not durable.
- 38.18 Integrated system does not satisfy problem statement: FAIL - cannot receive/validate real findings.

---

## 16. Recommendation

# DO NOT MERGE

As-is, merging Person 4 ships a beautiful, secure, well-typed fixture viewer with a real approval/audit API and a guarded mock AI layer - and labels it "an autonomous vulnerability triage & evidence engine". That is not the problem statement, and the review rules forbid excusing it.

Conditions under which a future review should pass (MERGE):
1. Person-1-style ingestion endpoint (e.g., POST /api/findings) that normalizes and clusters raw scanner findings into a Cluster with real dedup evidence (dedup_method, dedup_confidence).
2. Person-2-style safe validation layer whose observations are produced by real, time-boxed probes (document isolation honestly).
3. Person-3-style deterministic priority function (same factors in -> same score/level out) superseding fixture constants, with versioned formula.
4. Persistence (SQLite/file) so approvals, overrides, audit events survive restart; re-run the restart test to green.
5. A reproducible Docker target+scanner harness; re-run E2E-001 with real artifacts at every stage.
6. Route-level tests; keep existing FE injection and BE mock-AI tests; add validator/sanitizer unit tests.

Person 4's own deliverables should be kept as the integration surface; nothing here suggests rewriting the UI or contracts.

---

## 17. Evidence

- prompts.txt - scope split (P1/P2/P3 explicitly out of Person 4's scope and never implemented).
- docs/person4-contracts.md - "INITIAL (no Person 1-3 schemas observed)".
- Code: backend/app/cases/models.py (unused Finding/Cluster), backend/app/mock/fixtures.py (all case data), backend/app/api/*.py (routes; two case stores; in-memory), backend/app/ai/engine.py (mock fallback chain), frontend/lib/api/{types,realProvider,mockProvider}.ts, frontend/app/** and frontend/components/** (SOC workbench, pure data rendering).
- Test runs: backend 16 passed; frontend 8 passed; npm run build clean; npm run lint clean.
- Live API probes (this review): approvals 200/400/409, override P2->P1 with p1 stat 2->3, AI model=mock-v1 grounded output, 404s; restart test: approval reset PENDING, audit cleared, override reverted, analysis dropped.
- This review session fixed one real frontend bug (evidence filter) - re-verified green.