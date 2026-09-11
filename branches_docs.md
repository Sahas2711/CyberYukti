# Branch Integration — Definitive Branch Document

**Repository:** https://github.com/Sahas2711/CyberYukti
**Audit date:** 2026-09-11
**Auditor role:** Senior integration / security / QA / release gatekeeper
**Branch reviewed:** `person4` (current and only substantive branch)

---

## 1. Repository State

| Item | Value |
|---|---|
| Repository | https://github.com/Sahas2711/CyberYukti |
| Default branch (GitHub) | `main` (unborn — 0 commits, all files untracked) |
| Local branch | `person4` (HEAD, tracking `origin/person4`) |
| Remote branches | `origin/person4` only; `origin/main` (unborn) |
| Local-only branches | None |
| Stashes | None |
| Commit ancestry | Single linear chain: `826601c → 0874db8 → 62e6d4a → a937c5f → 9bde3c9` |
| Common ancestor with `main` | None (orphan-like: `main` has no commits) |
| Synced to remote? | Yes: `person4` == `origin/person4` |
| Secrets/keys in history | None found (secret scan of all committed files: clean; `.env.example` tracked with empty placeholders only) |

**Recommended integration base:** `person4` IS the content. The correct action is to make `person4` the default/main branch (not merge `main` into `person4` — `main` is empty). GitHub can be updated via Settings → Default Branch.

---

## 2. Branch Ownership / Purpose

### `main` (default, 0 commits)

No commits ever pushed. Contains the entire working tree only as untracked files (before commit to `person4` created the first tracked content). `main` has never been a working branch.

### `person4`

Created during this integration audit. Contains the entire repository implementation (Person 4's slice of the PS16 "Autonomous Vulnerability Triage & Evidence Engine"). 5 commits:

| Commit | Hash | Content |
|---|---|---|
| chore: add repository scaffolding | `826601c` | `.gitignore`, `.env.example`, `prompts.txt` |
| person4: backend | `0874db8` | `backend/` (FastAPI, AI engine, guardrails, mock API, 16 tests) |
| person4: frontend | `62e6d4a` | `frontend/` (Next.js SOC workbench, typed providers, 8 injection tests) |
| docs: existing person4 docs | `a937c5f` | `docs/person4-contracts.md`, `person4-demo-script.md`, `person4-failure-checklist.md`, `frontend-ui-documentation.md` |
| docs: review docs | `9bde3c9` | `docs/PERSON4_INTEGRATION_REVIEW.md`, `REAL_WORLD_DEMO.md`, `MERGE_DECISION.md` |

**There is no Person 1 branch, Person 2 branch, Person 3 branch, or integration branch.** The entire "4-person parallel work" narrative exists only in `prompts.txt` and the documentation. The code implements only Person 4's scope.

---

## 3. Commit History

```
9bde3c9 (HEAD -> person4, origin/person4) docs: add integration review, real-world demo plan, merge decision (DO NOT MERGE)
a937c5f docs: person4 contracts, demo script, failure checklist, ui documentation
62e6d4a person4: frontend — SOC workbench UI, typed mock/real providers, injection-safe rendering, tests
0874db8 person4: backend — AI engine with guardrails, case/approval/audit APIs, fixtures, mock provider tests
826601c chore: add repository scaffolding (gitignore, env example, problem statement)
```

- Linear history; no merge commits; no branches merged; no rebase.
- All commits authored from the same machine; no cross-branch histories.
- No orphan branches; no detached HEAD artifacts.

---

## 4. Branch Comparison (File-Level)

There is only one substantive branch. Comparison against `main` (which has no commits, only untracked files):

**Files in `person4` that do not exist on `main` (as tracked):** All 81 files (since `main` has zero tracked files).

**Files that existed as untracked before the first commit:** The entire working tree (`backend/`, `frontend/`, `docs/`, `prompts.txt`, `.env.example`). All were committed to `person4`. Nothing was left untracked (verified: `git status` clean).

**Key file tree (person4):**

```
backend/
├── app/
│   ├── main.py                     ← FastAPI app, CORS, router registration
│   ├── api/                         ← case_routes, approval_routes, ai_routes, audit_routes, dashboard_routes
│   ├── ai/                          ← engine.py, sanitizer.py, validator.py, provider.py, schemas.py, providers/
│   ├── cases/models.py              ← Pydantic models (Finding, Cluster, TriageCase, etc.)
│   └── mock/fixtures.py             ← 6 hardcoded TriageCase objects
├── pyproject.toml
frontend/
├── app/                             ← page.tsx (dashboard), cases/page.tsx, cases/[id]/page.tsx
├── components/case/                 ← AIAnalysisPanel, ApprovalControls, AuditTimeline, CaseHeader, CasePipeline, DuplicateClusterPanel, EvidencePanel, PriorityBreakdown, RemediationPanel, ThreatIntelPanel, ValidationBadge
├── components/dashboard/            ← CaseTable, KpiStrip, PipelineStrip, PriorityQueue
├── components/shared/               ← Badge, LoadingState, Sidebar, Skeleton, Tooltip, TopHeader
├── lib/api/                         ← client.ts, types.ts, realProvider.ts, mockProvider.ts
├── lib/providers.ts                 ← Provider switching (NEXT_PUBLIC_USE_MOCK)
├── tests/injection-ui.test.tsx      ← 8 injection tests
├── package.json, tsconfig, vitest, next.config, tailwind, postcss
docs/
├── PERSON4_INTEGRATION_REVIEW.md    ← DO NOT MERGE, 17-section review
├── REAL_WORLD_DEMO.md               ← Honest E2E plan (currently impossible)
├── MERGE_DECISION.md                ← Short-form NO with reasons
├── person4-contracts.md             ← Frontend↔backend contract mapping
├── person4-demo-script.md           ← Step-by-step demo walkthrough
├── person4-failure-checklist.md     ← Known failure modes
└── frontend-ui-documentation.md     ← UI component + SOC workbench docs
prompts.txt                          ← PS16 problem statement + scope split
.env.example                         ← OPENAI_API_KEY, ANTHROPIC_API_KEY, USE_MOCK_AI, etc.
.gitignore                           ← node_modules, .next, .env, __pycache__, .pytest_cache, etc.
```

81 tracked files total. No `.venv`, `node_modules`, `.next`, `__pycache__`, `.pytest_cache`, or build artifacts committed.

---

## 5. Merge Compatibility

### `main` ↔ `person4`

| Check | Status |
|---|---|
| Common ancestor | None (`main` is empty) |
| Fast-forward possible? | No — `main` has no commits at all |
| Can be merged? | Yes (trivial: `main` is empty; `person4` contains all content) |
| Conflicts? | None (nothing on `main` to conflict with) |
| Functional risk | None (this is the only merge possible) |
| Recommendation | **UPDATE DEFAULT BRANCH**: set `person4` as the default branch in GitHub, or merge `person4` into `main` (empty target). Either achieves the same result. |
| How to execute | Option A: GitHub Settings → Default branch → change to `person4`. Option B: on `main`, `git merge person4`. |

### Person 1 ↔ Person 2 ↔ Person 3

**Not applicable.** No Person 1, 2, or 3 branches exist. There is no cross-person merge forensics to perform. This is itself a critical finding (see section 7).

---

## 6. Code Quality

### Positive

- Clean TypeScript with strict typing throughout (`frontend/lib/api/types.ts` matches `backend/app/cases/models.py` field-for-field)
- Consistent FastAPI patterns: router-per-domain, model validation via Pydantic, clear error responses
- AI engine has explicit fallback chain: provider → retry → mock → hardcoded minimal
- Sanitizer applies `<UNTRUSTED>` wrapping with explicit field lists (`backend/app/ai/sanitizer.py:6-31`)
- Validator checks grounding: CVE references, numeric values, grounded_on fields (`backend/app/ai/validator.py:63-108`)
- Frontend uses React's `useMemo` for filtered/sorted case list (`CaseTable.tsx:73-87`)
- Approval controls: double-click confirm pattern, reason-required for reject/override (`ApprovalControls.tsx:73-95`)
- No `dangerouslySetInnerHTML` anywhere in the frontend (all React rendering uses default text escaping)

### Negative

- **Two independent in-memory case stores**: `case_routes.py:12` and `ai_routes.py:8` each build `{c["case_id"]: c for c in CASES}` from the same fixture list — but they are separate dicts. A mutation in `case_routes._cases_store` is invisible to `ai_routes._cases_store` and vice versa. This is a silent data consistency bug.
- **Duplicate `AIAnalysis` model**: defined identically in `backend/app/cases/models.py:61-72` and `backend/app/ai/schemas.py:4-15`. The engine imports from `schemas.py`; routes import from `models.py` or `schemas.py`. Works only because all routes return raw dicts via `model_dump()`.
- **`prev_hash` stores previous `event_id`**, not a cryptographic hash (`approval_routes.py:22`). The field name is semantically misleading.
- **Audit route import path**: `audit_routes.py:3` imports `_audit_store` from `case_routes.py`, creating a dependency chain that must be loaded in order. This is fragile.
- **Frontend `realProvider.ts:42-46`** types approve/reject/override responses as `TriageCase` but backend returns `ApprovalState` (a subset). Works at runtime because the frontend ignores the response body and re-fetches via `getCase()`.
- **CASE-005 confidence divergence**: backend fixture `fixtures.py:309` has `confidence=0.82`; frontend mock `mockProvider.ts:106` has `confidence=0.90`. Minor but indicates data was hand-duplicated, not machine-generated.
- **`docs/frontend-ui-documentation.md`** references deleted components (`StatCard`, `PriorityChart`, `AssetPanel`, `DuplicateSourcesPanel`) — documentation is stale.
- **`docs/person4-failure-checklist.md`** references a localStorage toggle that does not exist in the codebase.

---

## 7. Fake / Dummy / Mock Analysis

### What is genuinely implemented

| Component | Status | Evidence |
|---|---|---|
| FastAPI server | REAL | `backend/app/main.py`; starts clean; `GET /health` → 200 |
| Case listing/filtering API | REAL | `case_routes.py`; returns 6 cases from fixtures |
| Approve/reject/override with guards | REAL | `approval_routes.py:39-134`; 400/404/409 behavior verified |
| Audit event append | REAL | `approval_routes.py:18-36`; UUID + timestamp + prev_hash chain |
| AI analysis endpoint | REAL | `ai_routes.py:11-22`; calls engine, persists to `_cases_store` |
| AI engine (mock + provider chain) | REAL | `engine.py:45-104`; mock → retry → fallback logic |
| AI sanitizer | REAL | `sanitizer.py`; strips control chars, wraps in `<UNTRUSTED>` tags |
| AI grounding validator | REAL | `validator.py:63-108`; checks CVEs and numbers in output vs input |
| Frontend SOC workbench | REAL | Pure data rendering from provider objects; no hardcoded UI metrics |
| Frontend injection-safe rendering | REAL | 8 tests + no `dangerouslySetInnerHTML` |

### What is NOT implemented (only fixture/mock)

| Component | Status | Evidence |
|---|---|---|
| Finding ingestion endpoint | **MISSING** | No `POST /api/findings` or any ingestion route exists |
| Finding normalization | **MISSING** | `Finding` model defined (`models.py:13-24`) but never instantiated |
| Deduplication / clustering | **MISSING** | `Cluster` model defined (`models.py:27-32`) but never instantiated; `finding_count=3` in fixtures is a hardcoded attribute, not a clustering result |
| Evidence validation engine | **MISSING** | `ValidationResult` is a fixture attribute (`fixtures.py:69-93`); no probe execution, no sandbox, no subprocess code |
| Risk scoring function | **MISSING** | `PriorityResult.score/level` are hardcoded constants (`fixtures.py:96-108`); no formula computes them |
| EPSS/KEV/OSV enrichment | **MISSING** | `threat_intelligence` dict (`fixtures.py:94`) is a fixture constant; no NVD/EPSS/KEV API calls |
| Persistence | **MISSING** | All stores are in-memory dicts; restart wipes everything (verified) |
| Docker deployment | **MISSING** | No Dockerfile, docker-compose, Makefile, or shell script anywhere |

### Honest classification of every significant data element

| Data | Classification | Location |
|---|---|---|
| `CASE_001`–`CASE_006` | HARDCODED FIXTURE | `backend/app/mock/fixtures.py:61-361` |
| `priority.score` (e.g. 92.5, 45.2) | HARDCODED CONSTANT | `fixtures.py` priority sections |
| `evidence.status` (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE) | HARDCODED CONSTANT | `fixtures.py` evidence sections |
| `finding_count` (e.g. 3) | HARDCODED CONSTANT | `fixtures.py` per-case |
| `ANALYSES` object (frontend) | MOCK (prebuilt template responses) | `frontend/lib/api/mockProvider.ts:142-207` |
| `seedAuditLog()` (frontend) | MOCK (generates lifecycle events from fixtures) | `mockProvider.ts:224-301` |
| `MockProvider.analyze()` | MOCK (string-template builder, not an LLM) | `backend/app/ai/providers/mock_provider.py:16-132` |

---

## 8. Security Issues

| Severity | File:Line | Issue | Exploit Path | Status |
|---|---|---|---|---|
| INFO | `main.py:13-19` | CORS allows `localhost:3000` only; `allow_credentials=True` with `allow_methods=["*"]` | Acceptable for local development; document before wider use | Noted |
| INFO | `approval_routes.py:46,76,106` | No authentication; `analyst_id` accepted verbatim from request body | Any caller can impersonate any analyst | Acceptable for local demo; must be documented |
| LOW | `ai_routes.py:17-22` | Exception handler returns `str(e)` in HTTP 500 detail | Could leak internal error messages in production | Acceptable for local tool; log and return generic message in production |
| NONE | `sanitizer.py:40-44` | Sanitizer strips control chars and truncates to 2000 chars | No injection vector through sanitized fields | Secure |
| NONE | `system_prompt.txt` | System prompt declares `<UNTRUSTED>` tags are data | Combined with sanitizer, prevents prompt injection | Secure (mock and paid providers) |
| NONE | Frontend | No `dangerouslySetInnerHTML`, no `eval`, no `new Function` | XSS surface eliminated by React's default escaping | Secure |

**No CRITICAL or HIGH security issues found.** The system has no subprocess execution, no file access, no outbound network calls in the backend. The absence of the validation/sandbox engine (Person 2) means there is no sandbox-escape surface because there is no sandbox.

---

## 9. Deployment Issues

| Issue | Severity | Detail |
|---|---|---|
| No Dockerfile | BLOCKER | `docker compose build/up` impossible; one-command demo impossible |
| No docker-compose.yml | BLOCKER | No service orchestration; backend and frontend must be started manually |
| Backend must run from repo root | BLOCKER (undocumented) | `backend/app/main.py` imports `backend.app.*`; running `uvicorn` from `backend/` fails with `ModuleNotFoundError: No module named 'backend.app'` |
| No Makefile / shell scripts | MODERATE | No `make dev`, `make test`, or `make demo` targets |
| `.env.example` at root (not in `frontend/`) | MINOR | Frontend `.env.example` was removed; root file covers both but is not obvious to frontend-only developers |
| No health check for frontend | INFO | No `/api/health` on the Next.js side |
| `next-env.d.ts` in `.gitignore` | INFO | `frontend/.gitignore` excludes `next-env.d.ts` (Next.js regenerates it at build time; some teams track it) |

---

## 10. Dependency Conflicts

### Python (`backend/pyproject.toml`)

| Package | Version | Issue |
|---|---|---|
| `fastapi` | `>=0.104.0,<1.0` | OK |
| `starlette` | `==0.37.2` | Pinned to exact version; could conflict if another package needs a different Starlette |
| `uvicorn[standard]` | `>=0.24.0` | OK |
| `pydantic` | `>=2.5.0` | OK |
| `httpx` | `>=0.25.0` | Listed as dependency but never imported in any route; unused |
| `python-dotenv` | `>=1.0.0` | Listed but no `.env` loading in `main.py`; unused (could be loaded by uvicorn runner) |
| `openai` | `>=1.6.0` | Optional SDK; falls back to mock if not installed |
| `anthropic` | `>=0.8.0` | Optional SDK; falls back to mock if not installed |

### Node.js (`frontend/package.json`)

No conflicts. Standard Next.js 14 + React 18 + Tailwind + Vitest stack. All dependencies are stable.

### Cross-language

No Python↔Node dependency conflicts (separate runtimes, separate directories). No shared schemas (types are hand-maintained in both Python Pydantic and TypeScript interfaces).

---

## 11. Schema Conflicts

### Backend ↔ Frontend (verified field-for-field)

| Model | Backend (Pydantic) | Frontend (TypeScript) | Compatible? | Notes |
|---|---|---|---|---|
| `Asset` | 5 fields | 5 fields | ✅ YES | Identical types |
| `EvidenceObservation` | 6 fields | 6 fields | ✅ YES | FE uses stricter union types for `type` and `status` |
| `ValidationResult` | 6 fields | 6 fields | ✅ YES | |
| `PriorityResult` | 6 fields | 6 fields | ✅ YES | |
| `AIAnalysis` | 11 fields | 11 fields | ✅ YES | |
| `ApprovalState` | 5 fields | 5 fields | ✅ YES | FE uses stricter literal unions for `status` and `override_priority` |
| `AuditEvent` | 9 fields | 9 fields | ✅ YES | FE uses stricter `actor` union |
| `TriageCase` | 12 fields | 12 fields | ✅ YES | `vulnerability` and `threat_intelligence` are typed as `dict` on backend, stricter on frontend |
| `DashboardStats` | 9 fields | 9 fields | ✅ YES | |

### Backend response type mismatches (non-blocking)

| Operation | Backend returns | Frontend expects | Impact |
|---|---|---|---|
| `POST /approve` | `ApprovalState` | `TriageCase` | Low — response discarded; re-fetch via `getCase()` |
| `POST /reject` | `ApprovalState` | `TriageCase` | Low — same |
| `POST /override` | `ApprovalState` | `TriageCase` | Low — same |
| `POST /ai/analyze/{id}` | `AIAnalysis` (dumped) | `AIAnalysis` | ✅ matches |
| `GET /audit/{id}` | `list[AuditEvent]` | `AuditEvent[]` | ✅ matches (or 404 vs [] divergence) |

### Audit 404 vs [] divergence

- Backend `GET /api/cases/{id}/audit`: returns 404 if no events exist (`audit_routes.py:11`)
- Frontend mock: returns `[]` for missing audit (`mockProvider.ts:305-307`)
- Frontend real mode: calls `getAudit()` (`realProvider.ts:78-83`); 404 would trigger mock fallback

---

## 12. API Conflicts

### Full API table (all endpoints)

| Method | Path | Backend handler | Input | Output | Auth | Verified |
|---|---|---|---|---|---|---|
| `GET` | `/health` | `main.py:28-30` | — | `{"status":"ok"}` | None | 200 ✅ |
| `GET` | `/api/cases` | `case_routes.py:22-32` | query: `priority`, `status` | `TriageCase[]` | None | 200 ✅ (6 cases) |
| `GET` | `/api/cases/{id}` | `case_routes.py:35-41` | — | `TriageCase` | None | 200 / 404 ✅ |
| `POST` | `/api/cases/{id}/approve` | `approval_routes.py:39-65` | `{analyst_id, reason}` | `ApprovalState` | None | 200 / 400 / 404 / 409 ✅ |
| `POST` | `/api/cases/{id}/reject` | `approval_routes.py:68-96` | `{analyst_id, reason}` | `ApprovalState` | None | 200 / 400 / 404 ✅ |
| `POST` | `/api/cases/{id}/override` | `approval_routes.py:99-134` | `{analyst_id, override_priority, reason}` | `ApprovalState` | None | 200 / 400 / 404 ✅ |
| `GET` | `/api/cases/{id}/audit` | `audit_routes.py:8-12` | — | `AuditEvent[]` | None | 200 / 404 ✅ |
| `POST` | `/api/ai/analyze/{id}` | `ai_routes.py:11-22` | — | `AIAnalysis` | None | 200 / 404 / 500 ✅ |
| `GET` | `/api/dashboard/stats` | `dashboard_routes.py:8-33` | — | `DashboardStats` | None | 200 ✅ |

All endpoints verified with live HTTP probes against a running server. No endpoint exists in docs but not in code (and vice versa for the routes above).

**Missing endpoints (PS16 requires but do not exist):**

- `POST /api/findings` — no ingestion
- `POST /api/validate/{cluster_id}` — no evidence validation
- `POST /api/score/{cluster_id}` — no risk scoring
- `GET /api/clusters` — no cluster listing

---

## 13. Test Confidence

### Backend (`python -m pytest -q`)

| Test file | Tests | What they test | Genuine? |
|---|---|---|---|
| `test_injection.py` | 10 parametrized + 3 direct = 13 | MockProvider output with injection payloads in title field | **Tests mock only**: verifies mock provider returns all required fields regardless of input. Does not test paid providers (OpenAI/Anthropic) under adversarial input. |
| `test_hallucination.py` | 3 | Validator + MockProvider: no KEV claimed when none in input; correct CVSS referenced; no CVE invented | **Tests mock + validator**: most meaningful tests; verify grounding logic against mock output. Would need new cases for real LLM output. |

**What the backend tests do NOT test:**
- No route/API tests (all endpoints tested only via manual live probes, not automated)
- No approval flow tests
- No persistence tests (would require async server or ASGI test client)
- No sanitizer unit tests (sanitizer is only tested indirectly via mock_provider + injection tests)
- No validator unit tests (validator tested only via hallucination tests with mock output)
- No dashboard stats tests

### Frontend (`npm test`)

| Test file | Tests | What they test | Genuine? |
|---|---|---|---|
| `injection-ui.test.tsx` | 8 | `EvidencePanel` renders payloads as plain text (no script/img elements) | **Tests React rendering security**: verifies that XSS/prompt-injection strings appear in `textContent` and no `<script>` or `<img>` elements are created. Genuinely tests UI safety. |

**What the frontend tests do NOT test:**
- No provider tests (mockProvider/realProvider logic untested)
- No component rendering tests beyond EvidencePanel
- No integration tests
- No navigation tests

### Coverage summary

| Category | Coverage | Status |
|---|---|---|
| Unit test coverage | Backend 16 (mock only), frontend 8 (UI rendering) | LOW |
| Integration test coverage | 0 | NONE |
| E2E test coverage | 0 | NONE |
| Security test coverage | 18 injection tests (10 backend + 8 frontend) | MODERATE (mock only) |
| Deployment test coverage | 0 | NONE |

---

## 14. Real-World Readiness

### Can the system run against an actual controlled vulnerable target?

**NO.** Two independent blockers:

1. **No ingestion endpoint exists.** A real scanner finding (JSON, SARIF, or any format) has no path into the system. There is no `POST /api/findings` or equivalent. The engine cannot receive real data.

2. **No evidence validation engine exists.** Even if findings were ingested, no probe would be executed against a target. `ValidationResult` is a fixture attribute, not a computation.

### Can a fresh machine clone and run it?

**YES (with caveats):**
- Clone → `python -m pip install -e backend` → `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` (from repo root) → `cd frontend && npm install && npm run dev`
- Backend must be started from the repo root (not from `backend/`) due to import path `backend.app.*`
- No Docker available → two terminals required
- Backend runs on 8000, frontend on 3000, CORS trusts localhost:3000

### Can a judge independently reproduce a demo?

**ONLY for the current fixture-based UI walkthrough.** The demo shows 6 pre-baked cases with a full SOC workbench, AI analysis, approval workflow, and audit trail. A judge can: start both servers → open browser → click cases → approve → override → see audit. This is a genuine, functional demo of Person 4's scope.

**NOT for PS16 end-to-end** ("scan a real vulnerability → case created → analyst approves"). That workflow does not exist.

---

## 15. PS16 Mapping

| PS16 Requirement | Required? | Implemented? | Status |
|---|---|---|---|
| Finding normalization | YES | NO — `Finding` model unused | NOT SATISFIED |
| Duplicate clustering | YES | NO — `Cluster` model unused | NOT SATISFIED |
| Evidence validation | YES | NO — no probe execution | NOT SATISFIED |
| Safe sandbox | YES | NO — no subprocess/Docker code | NOT SATISFIED |
| Severity reasoning | YES | NO — score/level hardcoded | NOT SATISFIED |
| Exploitability context (EPSS/KEV) | YES | NO — data is fixture constant | NOT SATISFIED |
| Prioritization | YES | NO — no formula exists | NOT SATISFIED |
| Human approval | YES | YES — approve/reject/override with guards | SATISFIED |
| Auditability | YES | PARTIAL — audit events created but lost on restart | PARTIALLY SATISFIED |
| Agentic workflow | YES | NO — no pipeline; cases start pre-built | NOT SATISFIED |
| Real controlled target demo | YES | NO — no ingestion, no sandbox | NOT SATISFIED |

**PS16 completion: 1.5 / 11 requirements fully satisfied.**

---

## 16. Merge Decision

### `main` ↔ `person4`

**Decision: UPDATE DEFAULT BRANCH (or merge `person4` into `main`)**

`main` is empty. `person4` contains all content. There is no code conflict. The correct action is:

- **Option A (recommended):** Change GitHub default branch from `main` to `person4` via repository settings.
- **Option B:** On `main`, run `git merge person4` (fast-forward not possible because `main` has no commit to advance from; but the merge target is empty, so it succeeds cleanly).

### `person4` as "the solution" — should it be marked as a PS16-compliant merge?

**NO.**

Person 4's internal code quality is high and its contracts are clean. But merging `person4` into a "complete PS16 solution" would ship a fixture viewer without the core engine the problem statement requires. The merge decision is NOT about Git conflicts — it is about whether the result satisfies the problem. It does not.

**Conditions for MERGE of `person4` as the integration base:**

1. Person 1 deliverable: a finding-ingestion endpoint with normalization and dedup that produces `Cluster` objects from real scanner output.
2. Person 2 deliverable: a time-boxed evidence-validation engine with honest isolation documentation.
3. Person 3 deliverable: a deterministic priority computation function (`Factors → score → P1-P4`).
4. Persistence: SQLite or file-based storage for approvals, audit events, and analyses.
5. Docker harness: Dockerfile + docker-compose for a reproducible demo environment.
6. E2E test: one automated end-to-end test from ingestion through approval.

None of these exist today. The merge should be held until they do.
