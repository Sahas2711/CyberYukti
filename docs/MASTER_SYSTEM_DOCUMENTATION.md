# Master System Documentation — CyberYukti Forensic Audit

**Repository:** https://github.com/Sahas2711/CyberYukti
**Branch audited:** `person4` (only substantive branch)
**Audit date:** 2026-09-11
**Auditor roles:** Senior Software Architect, Security Architect, QA Lead, DevSecOps Engineer, Integration Engineer, Adversarial Code Reviewer, PS16 Evaluator

---

## Phase 1 — Git Repository State

**Remote:** `origin` → `https://github.com/Sahas2711/CyberYukti` (HTTPS)
**Default branch (GitHub):** `main` — 0 commits, all files untracked
**Active branch:** `person4` — 5 linear commits, clean, synced to `origin/person4`
**No Person 1, 2, 3, or integration branches exist.** No stashes, no reflog entries, no ignored config.
**Tracked files:** 81. **Untracked files (post-audit):** `branches_docs.md`, `docs/MASTER_SYSTEM_DOCUMENTATION.md` + 40 topic docs (being created in this session).
**Secret scan:** Clean. Only `.env.example` committed (empty placeholders). No `sk-`, `ghp_`, `AKIA`, or private keys in tree.

---

## Phase 2 — Branch-by-Branch Archaeology

### `main` (0 commits)
**Purpose:** Default branch. Never received any commit.
**Actual state:** Empty.

### `person4` (5 commits, HEAD)
**Purpose:** Implements Person 4's slice of the PS16 "Autonomous Vulnerability Triage & Evidence Engine": AI explanation engine, typed provider layer, approval/override/reject workflow, audit trail, SOC workbench dashboard and case detail views, and AI injection/grounding guardrails.

**Actual implementation:**
- FastAPI backend with 9 API endpoints, in-memory stores, Pydantic models, mock+real AI provider chain, sanitizer, validator
- Next.js frontend with 3 pages, 25 components, typed mock/real providers, filterable case table, injection-safe rendering
- 16 backend tests (mock AI only), 8 frontend tests (UI injection rendering)
- 6 hardcoded TriageCase fixtures with pre-baked scores, evidence statuses, and finding counts

**Missing implementation:** Everything Person 1/2/3 — ingestion, normalization, dedup, evidence validation, sandbox, risk scoring, persistence.

**Runtime path (current):**
```
Fixture List (fixtures.py) → In-Memory Dict (case_routes._cases_store)
    → FastAPI routes → JSON response
    → Frontend (realProvider.ts or mockProvider.ts) → React components → SOC Workbench UI

AI Analysis: TriageCase dict → sanitize_case_for_llm() → provider.analyze() → validate_analysis() → AIAnalysis dict
Approve/Reject/Override: JSON body → guards → mutate _cases_store → append _audit_store → return ApprovalState
Dashboard Stats: Aggregation over CASES list → DashboardStats
```

**Dependencies:**
- Python ≥3.11 (verified 3.11.9 on this machine), FastAPI, Starlette, Pydantic, Uvicorn, httpx (unused), openai (optional), anthropic (optional)
- Node ≥18 (verified 20.x), Next.js 14, React 18, Tailwind, Vitest, @testing-library/react, jsdom

---

## Phase 3 — Code Authenticity / Fakeness Audit

### VERIFIED REAL
| Component | File | Evidence |
|---|---|---|
| FastAPI server starts and serves routes | `backend/app/main.py` | Live probe: `GET /health` → 200 `{"status":"ok"}` |
| Case listing returns 6 cases | `backend/app/api/case_routes.py:22-32` | Live probe: `GET /api/cases` → 6 items |
| Approval guards work (400/404/409) | `backend/app/api/approval_routes.py:39-134` | Live probe: missing analyst_id→400; double-approve→409 |
| Override mutates priority level | `approval_routes.py:128` | Live probe: CASE-005 P2→P1; stats p1 2→3 |
| Audit events created with UUID + prev_hash | `approval_routes.py:18-36` | Live probe: `GET /api/cases/CASE-001/audit` → 1 event |
| AI analysis via mock-v1 with grounded output | `ai_routes.py:11-22`, `mock_provider.py` | Live probe: `POST /api/ai/analyze/CASE-001` → `model=mock-v1`, `grounded_on_count=6` |
| AI sanitizer strips control chars, wraps in `<UNTRUSTED>` | `sanitizer.py:40-44` | 10 injection payloads pass mock provider tests |
| AI grounding validator checks CVE/number consistency | `validator.py:63-108` | 3 hallucination tests pass |
| Frontend renders from data objects | `frontend/app/page.tsx`, `app/cases/[id]/page.tsx` | Build clean; 8 injection tests pass; no hardcoded UI metrics |
| Injection-safe React rendering | `frontend/tests/injection-ui.test.tsx` | 8 payloads verified: no `<script>` elements, payloads appear in textContent |

### HARDCODED / MOCK / NOT IMPLEMENTED
| Component | Classification | File:Line | Evidence |
|---|---|---|---|
| CASE_001–CASE_006 | HARDCODED FIXTURE | `fixtures.py:61-361` | All case data is a TriageCase constructor call with constant arguments |
| `priority.score` (92.5, 45.2, 61.8, 28.5, 68.9, 97.3) | HARDCODED CONSTANT | `fixtures.py` priority sections | No function computes these; they are literal numbers |
| `evidence.status` (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE) | HARDCODED CONSTANT | `fixtures.py` evidence sections | Status is set at case creation time; no probe produces it |
| `finding_count` (3, 2, 3, 1, 2, 2) | HARDCODED CONSTANT | `fixtures.py` per-case | This is NOT a clustering result; it is a hand-written attribute |
| `ANALYSES` object (frontend) | MOCK (template strings) | `mockProvider.ts:142-207` | Pre-built analysis strings with interpolated case data; not LLM output |
| `seedAuditLog()` (frontend) | MOCK (generated events) | `mockProvider.ts:224-301` | Generates clustered→validated→prioritized→analysis lifecycle events at startup from fixture timestamps |
| `MockProvider.analyze()` | MOCK (string builder) | `mock_provider.py:16-132` | Constructs a JSON string from case fields using f-strings and `_clean()` regex; no LLM call |
| `Finding` model | UNUSED | `models.py:13-24` | Defined but never instantiated anywhere in the codebase |
| `Cluster` model | UNUSED | `models.py:27-32` | Defined but never instantiated |
| Evidence validation engine | NOT IMPLEMENTED | N/A | No probe execution, no Docker, no subprocess code; grep for `subprocess` returns 0 hits |
| Risk scoring function | NOT IMPLEMENTED | N/A | `priority.score` is a constant; no formula computes it |
| Finding ingestion endpoint | NOT IMPLEMENTED | N/A | No `POST /api/findings` or any ingestion route |

---

## Phase 4 — "Does It Actually Work?" Audit

| Feature | Claimed | Code Exists | Executable | Tested | E2E Tested | Real Input | Real Output | Status |
|---|---|---|---|---|---|---|---|---|
| FastAPI server | Yes | Yes | Yes (started) | No (no start test) | No | N/A | 200 /health | VERIFIED |
| Case listing | Yes | Yes | Yes (live) | No | No | Fixtures | 6 cases | VERIFIED |
| Case detail | Yes | Yes | Yes (live) | No | No | case_id | TriageCase | VERIFIED |
| Approve | Yes | Yes | Yes (live) | No | No | analyst_id + reason | APPROVED + audit event | VERIFIED |
| Reject | Yes | Yes | Yes (live) | No | No | analyst_id + reason | REJECTED + audit event | VERIFIED |
| Override | Yes | Yes | Yes (live) | No | No | new_priority + reason | OVERRIDDEN + priority mutation | VERIFIED |
| Audit trail | Yes | Yes | Yes (live) | No | No | case_id | AuditEvent[] | PARTIAL (lost on restart) |
| AI analysis | Yes | Yes | Yes (live) | Yes (mock only) | No | TriageCase | AIAnalysis (mock-v1) | VERIFIED (mock only) |
| Dashboard stats | Yes | Yes | Yes (live) | No | No | N/A | DashboardStats | VERIFIED |
| Finding ingestion | Yes (PS16) | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| Normalization | Yes (PS16) | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| Deduplication | Yes (PS16) | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| Evidence validation | Yes (PS16) | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| Risk scoring | Yes (PS16) | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| Persistence | Implicit | No | No (restart proof) | No | No | N/A | N/A | BROKEN (in-memory only) |
| Docker deployment | Expected | No | No | No | No | N/A | N/A | NOT IMPLEMENTED |

---

## Phase 5 — Person 1 / Ingestion Audit

**Result: NOT IMPLEMENTED**

No ingestion endpoint exists. No route accepts scanner findings in any format (JSON, SARIF, JSONL, or otherwise).

**Models defined but unused:**
- `Finding` (`models.py:13-24`) — 11 fields including `scanner`, `scanner_rule_id`, `cve`, `cwe`, `asset`, `raw_evidence`, `observed_at`
- `Cluster` (`models.py:27-32`) — 5 fields: `cluster_id`, `finding_ids`, `primary_finding_id`, `dedup_confidence`, `dedup_method`

**Critical distinction:** `finding_count=3` in `CASE_001` (`fixtures.py:67`) is a hardcoded integer, NOT the result of a dedup/clustering algorithm. It does not count real findings. The `DuplicateClusterPanel` (`DuplicateClusterPanel.tsx:26-28`) renders this number as-is from the fixture data — it is a display of a constant, not evidence of clustering.

**What must exist but does not:**
1. `POST /api/findings` — accepts raw scanner output
2. Normalization logic — converts heterogeneous scanner formats to canonical `Finding` schema
3. Deduplication logic — groups `Finding` objects into `Cluster` objects
4. Correlation logic — cross-references SAST ↔ DAST findings from different scanners

---

## Phase 6 — Person 2 / Evidence Validation Audit

**Result: NOT IMPLEMENTED**

No evidence validation engine exists. No probe execution code. No Docker/sandbox code. No subprocess calls anywhere in backend.

**Models defined but unused as computations:**
- `ValidationResult` (`models.py:44-50`) — status, confidence, observations, validator_version
- `EvidenceObservation` (`models.py:35-41`) — observation_id, type, target, observed_value, expected_value, method

**What exists:** These models are used as type definitions for the fixture data in `fixtures.py`. The `status` field (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE) is set at case creation time, not computed by any validation logic.

**Critical finding:** There is zero subprocess, Docker, or network-validation code in the entire backend. Grep for `subprocess`, `docker`, `requests.get`, `httpx.get` returns 0 hits in backend code (excluding tests and provider imports). This means no probe has ever been executed against any target.

---

## Phase 7 — Person 3 / Risk Engine Audit

**Result: NOT IMPLEMENTED**

No risk scoring function exists. Priority scores are fixture constants.

**Models defined but used as constants:**
- `PriorityResult` (`models.py:53-58`) — cluster_id, score, level, factors, formula_version

**Evidence from `fixtures.py`:**

| Case | Score | Level | Factors (all constants) |
|---|---|---|---|
| CASE-001 | 92.5 | P1 | cvss=8.8, epss=0.72, kev=True, asset_criticality=critical, internet_exposed=True, evidence_confidence=0.95 |
| CASE-002 | 45.2 | P2 | cvss=5.4, epss=0.15, kev=False, asset_criticality=high, internet_exposed=False, evidence_confidence=0.88 |
| CASE-003 | 61.8 | P3 | cvss=6.1, epss=0.42, kev=False, asset_criticality=critical, internet_exposed=True, evidence_confidence=0.91 |
| CASE-004 | 28.5 | P4 | cvss=4.2, epss=0.08, kev=False, asset_criticality=low, internet_exposed=False, evidence_confidence=0.35 |
| CASE-005 | 68.9 | P2 | cvss=7.5, epss=0.35, kev=False, asset_criticality=high, internet_exposed=True, evidence_confidence=0.82 |
| CASE-006 | 97.3 | P1 | cvss=9.8, epss=0.85, kev=True, asset_criticality=medium, internet_exposed=False, evidence_confidence=0.96 |

`formula_version="1.0.0"` is set in every case — but no formula code exists. `override` in `approval_routes.py:128` mutates `priority.level` without recomputing `score`. The system has no way to answer: "What formula produces 92.5 from these factors?"

**What must exist but does not:**
1. `compute_priority(factors: dict) -> PriorityResult` — deterministic score function
2. EPSS enrichment — live query to `https://api.first.org/data/v1/epss`
3. KEV enrichment — CISA KEV database lookup
4. Formula versioning with documented thresholds

---

## Phase 8 — Person 4 / Response & Human Approval Audit

**Result: PRESENT (this is the only implemented slice)**

### Case Management
- `GET /api/cases` — list all cases with optional priority/status filters (`case_routes.py:22-32`)
- `GET /api/cases/{id}` — single case detail with audit trail (`case_routes.py:35-41`)
- Frontend: CaseTable with search, priority/evidence/approval filters, sorted by P1→P4 (`CaseTable.tsx:73-87`)

### Approval Workflow
- `POST /api/cases/{id}/approve` — requires `analyst_id`; blocks re-approve (409) (`approval_routes.py:39-65`)
- `POST /api/cases/{id}/reject` — requires `analyst_id` + `reason`; blocks reject-after-approve (409) (`approval_routes.py:68-96`)
- `POST /api/cases/{id}/override` — requires `analyst_id` + `reason` + valid `override_priority` (P1-P4); mutates `priority.level` and records `old_priority`/`new_priority` in audit metadata (`approval_routes.py:99-134`)

### AI Explanation
- `POST /api/ai/analyze/{id}` — triggers AI engine; result stored in `case["ai_analysis"]`; response is `AIAnalysis` (`ai_routes.py:11-22`)
- Engine: sanitize → provider.analyze() → validate → retry → fallback to mock → hardcoded minimal fallback (`engine.py:45-104`)
- Providers: OpenAI (`openai_provider.py`), Anthropic (`anthropic_provider.py`), Mock (`mock_provider.py`)
- Guardrails: sanitizer strips control chars + wraps 24 untrusted fields in `<UNTRUSTED>` tags; validator checks CVE/number grounding; system prompt instructs LLM to treat tags as data

### Audit Trail
- `GET /api/cases/{id}/audit` — returns `AuditEvent[]` or 404 (`audit_routes.py:8-12`)
- Events: UUID, timestamp, actor, actor_id, action, previous_state, new_state, metadata, prev_hash (stores previous event_id, not a cryptographic hash) (`approval_routes.py:18-36`)

### Dashboard
- `GET /api/dashboard/stats` — aggregated counts: total_findings, unique_clusters, confirmed/not_confirmed/inconclusive, p1/p2/p3/p4 (`dashboard_routes.py:8-33`)
- Frontend: KpiStrip, PipelineStrip, PriorityQueue, CaseTable all render from provider data

### UI Components (25 components)
- Dashboard: KpiStrip, PipelineStrip, PriorityQueue, CaseTable
- Case detail: CaseHeader, CasePipeline, EvidencePanel, PriorityBreakdown, AIAnalysisPanel, RemediationPanel, ThreatIntelPanel, DuplicateClusterPanel, ApprovalControls, AuditTimeline, ValidationBadge
- Shared: Badge, LoadingState, Sidebar, Skeleton, Tooltip, TopHeader
- Layout: TopHeader (with Sidebar)

### What is NOT Person 4's responsibility (confirmed absent)
- No finding ingestion, normalization, or deduplication
- No evidence validation engine
- No risk scoring function
- No Docker deployment
- No persistence layer

---

## Phase 9 — Schema Contract Audit

**Cross-reference:** See `docs/person4-contracts.md` and `branches_docs.md` section 11.

All 9 Pydantic models (`Asset`, `EvidenceObservation`, `ValidationResult`, `PriorityResult`, `AIAnalysis`, `ApprovalState`, `AuditEvent`, `TriageCase`, plus duplicate `AIAnalysis` in `schemas.py`) have field-for-field-compatible TypeScript counterparts in `frontend/lib/api/types.ts`.

**Type mismatches (non-blocking):**
- Backend `vulnerability: dict` vs Frontend `vulnerability: { cwe?: string; cve?: string }` — FE is stricter; backend passes through.
- Backend `threat_intelligence: dict` vs Frontend `threat_intelligence: { cvss?: number; epss?: number; kev?: boolean }` — same pattern.
- Backend approval responses (`ApprovalState`) vs Frontend expects (`TriageCase`) — response body discarded.

**Duplicate definition:**
- `AIAnalysis` is defined identically in `backend/app/cases/models.py:61-72` AND `backend/app/ai/schemas.py:4-15`. The engine imports from `schemas.py`. The routes import from `models.py`. Both are used. Works because `model_dump()` produces identical dicts.

---

## Phase 10 — API Contract Audit

**See `branches_docs.md` section 12 for full table.**

9 endpoints, all verified with live HTTP probes:
- `GET /health` → 200
- `GET /api/cases` → 200 (6 items)
- `GET /api/cases/{id}` → 200 / 404
- `POST /api/cases/{id}/approve` → 200 / 400 / 404 / 409
- `POST /api/cases/{id}/reject` → 200 / 400 / 404 / 409
- `POST /api/cases/{id}/override` → 200 / 400 / 404 (validates P1-P4, requires reason)
- `GET /api/cases/{id}/audit` → 200 / 404
- `POST /api/ai/analyze/{id}` → 200 / 404 / 500
- `GET /api/dashboard/stats` → 200

**Error handling:** 400 (missing analyst_id, invalid override_priority), 404 (case not found, audit not found), 409 (already decided), 500 (AI analysis failure). No timeout handling. No rate limiting.

---

## Phase 11 — Dependency & Deployability Forensics

**Python backend (`pyproject.toml`):**
- `fastapi>=0.104.0,<1.0` ✅
- `starlette==0.37.2` — pinned exact version (potential conflict with other packages needing different Starlette)
- `uvicorn[standard]>=0.24.0` ✅
- `pydantic>=2.5.0` ✅
- `httpx>=0.25.0` — listed but **never imported in any backend route** (unused dependency)
- `python-dotenv>=1.0.0` — listed but `.env` not loaded in `main.py` (unused or loaded by runner)
- `openai>=1.6.0` — optional; auto-mock if no API key
- `anthropic>=0.8.0` — optional; auto-mock if no API key

**Node frontend (`package.json`):**
- `next ^14.2.35`, `react ^18.3.1`, `react-dom ^18.3.1` — stable; no conflicts
- Dev: `vitest ^1.6.0`, `@testing-library/react ^14.3.1`, `jsdom ^29.1.1`, `tailwindcss ^3.4.15`, `typescript ^5.6.3`

**Clean machine deployment:**
```bash
git clone https://github.com/Sahas2711/CyberYukti
cd CyberYukti
python -m pip install -e backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000  # MUST run from repo root
cd frontend && npm install && npm run dev
```
**Blocker:** Must run uvicorn from repo root (not `backend/`); no Docker one-liner available.

---

## Phase 12 — Docker Forensics

**Result: NO DOCKER FILES EXIST**

No Dockerfile, docker-compose.yml, Makefile, or shell script exists anywhere in the repository (verified by glob for `**/Dockerfile*`, `**/docker-compose*`, `**/*.sh`, `**/Makefile`). `docker compose build` and `docker compose up` are impossible.

**Static verification only.** Docker execution NOT POSSIBLE.

---

## Phase 13 — Security Forensics

| Severity | File:Line | Finding | Exploit Path | Impact | Fix |
|---|---|---|---|---|---|
| INFO | `main.py:13-19` | CORS `allow_origins=["http://localhost:3000"]` with `allow_credentials=True` and `allow_methods=["*"]` | N/A (localhost only) | Acceptable for local tool | Document; restrict `allow_methods` in production |
| INFO | `approval_routes.py:46,76,106` | No authentication; `analyst_id` from request body trusted verbatim | Any HTTP caller can impersonate any analyst | Analyst identity is unverified | Add API key or JWT auth for non-demo use |
| LOW | `ai_routes.py:17-22` | Exception handler returns `str(e)` in HTTP 500 detail | Could leak internal error messages | Information disclosure | Return generic message; log full error server-side |
| NONE | `sanitizer.py:40-44` | Control character stripping + 2000-char truncation + `<UNTRUSTED>` wrapping | No injection vector through sanitized fields | N/A | Already secure |
| NONE | `system_prompt.txt` | System prompt declares `<UNTRUSTED>` tags are data | Combined with sanitizer, prevents prompt injection | N/A | Already secure |
| NONE | Frontend | No `dangerouslySetInnerHTML`, no `eval`, no `new Function` anywhere | XSS surface eliminated | N/A | Already secure |

**No CRITICAL or HIGH security vulnerabilities found.** The system has no subprocess execution, no file access, no outbound network calls in the backend (excluding optional OpenAI/Anthropic SDK calls). The absence of the validation/sandbox engine means there is no sandbox-escape surface because there is no sandbox.

---

## Phase 14 — Adversarial Input Testing

### Backend injection tests (10 payloads in `test_injection.py`)
All test the **mock provider** — `MockProvider.analyze(tampered_case)` — and verify the output is a valid `AIAnalysis` JSON with all required fields. These tests confirm:
1. The mock provider's `_clean()` regex strips `<UNTRUSTED>` tags from inputs
2. The mock provider produces all required fields regardless of title content
3. No payload causes the mock provider to follow injection instructions

### Frontend injection tests (8 payloads in `injection-ui.test.tsx`)
All test `EvidencePanel` rendering and verify:
1. No `<script>` elements in rendered output
2. All payloads appear in `textContent` (plain text, not executable)
3. `<img src=x onerror=alert(1)>` does not create an img element
4. Benign control values render without false positives

### What is NOT tested (gaps)
- Paid providers (OpenAI/Anthropic) under adversarial input — untested
- Backend routes under adversarial input (e.g., malicious `analyst_id`, `reason` fields)
- The sanitizer under adversarial input (only tested indirectly via mock provider)
- Path traversal, SSRF, command injection against the API (surface absent but untested)

---

## Phase 15 — Test Suite Forensics

**Backend tests (16 total, all pass):**
- `test_injection.py`: 10 parametrized payloads + 3 direct tests → all verify mock provider returns valid AIAnalysis JSON with injection in title field
- `test_hallucination.py`: 3 tests → verify mock provider + validator: no KEV when none in input, correct CVSS referenced, no CVE invented

**What each test would catch:**
- `test_mock_provider_ignores_injection`: Would catch if mock provider followed title injection → all 10 payloads pass (mock is inherently injection-safe because it builds strings from case data, not from LLM calls)
- `test_mock_provider_output_matches_schema`: Would catch if mock output didn't match Pydantic schema → passes (mock output is hand-crafted)
- `test_mock_provider_produces_valid_json`: Would catch if mock output wasn't valid JSON → passes
- `test_no_kev_claimed_when_none_in_input`: Would catch if mock or validator referenced KEV when input lacked it → passes
- `test_correct_cvss_referenced`: Would catch if mock referenced wrong CVSS → passes
- `test_no_cve_invented`: Would catch if mock or validator allowed invented CVEs → passes

**Critical observation:** All backend tests test the mock provider only. If the mock provider were replaced with a real LLM provider, the hallucination tests would likely fail (real LLMs hallucinate CVEs). The tests validate the guardrails against a deterministic system, not against real AI behavior.

**Frontend tests (8 total, all pass):**
- All test `EvidencePanel` rendering with injection payloads → catch XSS in React rendering

---

## Phase 16 — Real-World Demonstration Validation

**The end-to-end pipeline:**
```
Controlled Vulnerable Application → Real Scanner → Raw Findings → CyberYukti Ingestion
→ Normalization → Deduplication → Evidence Validation → Risk Scoring → AI Analysis
→ Priority Case → Human Approval → Audit Trail
```

**Current status:** Only the last 5 steps (AI analysis → priority case → human approval → audit trail) are demonstrable. The first 7 steps (vulnerable app → scanner → ingestion → normalization → dedup → evidence validation → risk scoring) do not exist.

**What CAN be demonstrated today:**
1. Start backend + frontend
2. Open dashboard: 6 pre-built vulnerability cases with evidence status, priority, sources
3. Click a case: evidence panel, priority breakdown, threat intel panel, duplicate cluster panel, AI analysis panel, remediation panel
4. Approve/reject/override with audit trail
5. View dashboard stats

**What CANNOT be demonstrated:**
- Scanner finding → ingestion → case creation
- Deduplication of same finding across scanners
- Evidence probe execution against a target
- Priority computation from factors

**Honest assessment:** The demo shows a fully functional SOC analyst workbench operating on pre-built data. It does NOT show the autonomous vulnerability triage pipeline that PS16 requires.

---

## Phase 17 — Five Required Demo Scenarios

| Scenario | Description | Status | Evidence |
|---|---|---|---|
| 1. Confirmed vulnerability | Scanner reports vuln → evidence confirms → risk elevated → P1/P2 → analyst case | **MOCK** | CASE-001 has CONFIRMED evidence and P1 priority, but both are fixture constants, not computed |
| 2. False positive | Scanner reports vuln → evidence contradicts → risk reduced | **MOCK** | CASE-002 has NOT_CONFIRMED evidence and P2 priority; both fixture constants |
| 3. Duplicate findings | Three scanners report same issue → normalized → deduped → one incident | **MOCK** | CASE-001 has `sources=["nuclei","semgrep","burp"]` and `finding_count=3`, but these are fixture constants, not dedup results |
| 4. Malicious scanner output | Untrusted input → sanitized → no command execution | **PARTIAL** | Backend sanitizer + grounding validator work against mock provider; frontend injection tests pass; but the real scenario (scanner → ingestion) doesn't exist |
| 5. Human priority override | System assigns priority → analyst overrides → reason recorded → audit event created | **WORKING** | Live probe: override CASE-005 P2→P1 → 200, audit event with old_priority/new_priority/reason |

**Summary:** 1 scenario fully working (override), 1 partially working (injection defense, but ingestion path missing), 3 scenarios are mock data displays.

---

## Phase 18 — Branch Merge Forensics

**There is only 1 branch + 1 empty branch.** Cross-person merge analysis is not applicable (no Person 1/2/3 branches exist).

| Pair | Fast-Forward? | Normal Merge? | Conflicts | Functional Risk | Recommendation |
|---|---|---|---|---|---|
| `main` ↔ `person4` | No (main has 0 commits) | Yes (trivial: main is empty) | None | None | UPDATE DEFAULT BRANCH to `person4` |

---

## Phase 19 — Repository Hygiene

| Issue | Status |
|---|---|
| `.venv` committed | No |
| `node_modules` committed | No |
| `__pycache__` committed | No |
| `.pytest_cache` committed | No |
| `.next` build output committed | No |
| `package-lock.json` committed | Yes (standard practice for apps; acceptable) |
| `.env` committed | No (`.env.example` committed with empty values) |
| IDE metadata committed | No |
| Dead/unused code | `Finding` and `Cluster` models (`models.py:13-32`) — defined but never instantiated |
| Unused dependency | `httpx` in `pyproject.toml` — never imported in any backend route |
| Stale documentation | `frontend-ui-documentation.md` references deleted components; `person4-failure-checklist.md` references nonexistent localStorage toggle |

---

## Phase 20 — Documentation vs. Code Consistency

| Documentation Claim | Evidence in Code | Correct? | Problem |
|---|---|---|---|
| "13 findings reduced to 6 actionable cases" (dashboard) | `CASES` list has 6 items with `finding_count` summing to 13 | Display is correct, but `finding_count` is a fixture constant, not a clustering result | **MISLEADING** — implies dedup happened |
| "3 FINDINGS → 1 CLUSTER → 1 TRIAGE CASE" (DuplicateClusterPanel) | Renders `finding_count` from fixture | **MISLEADING** — implies dedup pipeline exists |
| "Score is computed deterministically from the validated factors" (ApprovalControls) | `priority.score` is a fixture constant; no formula exists | **FALSE** — no computation occurs |
| "Evidence validation status" displayed with confidence % | `evidence.status` and `evidence.confidence` are fixture constants | **MISLEADING** — implies validation was performed |
| "Findings normalized and deduplicated" (DuplicateClusterPanel subtitle) | No normalization or dedup code exists | **FALSE** — the panel displays fixture data, not pipeline output |
| `docs/person4-contracts.md`: "INITIAL (no Person 1-3 schemas observed)" | Correct — Person 1/2/3 code doesn't exist | ✅ Accurate |
| `docs/PERSON4_INTEGRATION_REVIEW.md`: "DO NOT MERGE" | Correct assessment based on evidence | ✅ Accurate |
| `docs/REAL_WORLD_DEMO.md`: "currently impossible" | Correct — no ingestion pipeline exists | ✅ Accurate |

---

## Phase 21 — PS16 Requirements Traceability

| PS16 Requirement | Required | Implementation | Evidence | Status | Gap |
|---|---|---|---|---|---|
| Finding normalization | YES | `Finding` model defined, never used | `models.py:13-24` | NOT IMPLEMENTED | No ingestion endpoint, no normalization logic |
| Duplicate clustering | YES | `Cluster` model defined, never used; `finding_count` is fixture constant | `models.py:27-32`, `fixtures.py:67` | NOT IMPLEMENTED | No dedup/clustering algorithm |
| Evidence validation | YES | `ValidationResult` model used as fixture type | `models.py:44-50`, `fixtures.py:69-93` | NOT IMPLEMENTED | No probe execution, no validation engine |
| Safe sandbox | YES | No Docker/subprocess code | grep: 0 hits | NOT IMPLEMENTED | No sandbox exists |
| Severity reasoning | YES | `PriorityResult` with constant `score`/`level` | `fixtures.py:96-108` | NOT IMPLEMENTED | No formula computes priority |
| Exploitability context | YES | `threat_intelligence` dict with constant cvss/epss/kev | `fixtures.py:94` | NOT IMPLEMENTED | No EPSS/KEV enrichment |
| Prioritization | YES | Same as severity reasoning | Same | NOT IMPLEMENTED | Same as severity reasoning |
| Human approval | YES | Approve/reject/override with guards + audit | `approval_routes.py:39-134` | SATISFIED | |
| Auditability | YES | Audit events created but lost on restart | `approval_routes.py:18-36` | PARTIAL | No persistence |
| Agentic workflow | YES | No pipeline; cases start pre-built | All fixtures | NOT IMPLEMENTED | No end-to-end pipeline |
| Real controlled target | YES | No ingestion, no sandbox | All of the above | NOT IMPLEMENTED | No target, no scanner integration |

**PS16 Completion Score: 1.5 / 11 requirements fully satisfied (13.6%).** Only "Human approval" is fully satisfied. "Auditability" is partially satisfied. All others are not implemented.

---

## Phase 22 — Expected vs. Current Architecture

### Expected (PS16)
```
Scanners → Ingestion → Canonical Finding → Dedup/Correlation → Evidence Sandbox
→ Threat Intel (EPSS/KEV) → Risk Scoring → Priority → AI Explanation
→ Analyst Case → Human Approval/Override → Immutable Audit Trail
```

### Current
```
Hardcoded Fixtures (fixtures.py) → In-Memory Dicts → FastAPI Routes → JSON
    → Frontend (realProvider or mockProvider) → React SOC Workbench UI

AI Engine: TriageCase dict → Sanitizer → Provider.analyze() → Validator → AIAnalysis dict
Approval: JSON body → Guards → Mutate dict → Append audit event (in-memory)
```

### Missing components (mapping current → expected)
1. **Scanners → Ingestion** : No ingestion endpoint or parser
2. **Canonical Finding → Dedup** : No Finding/Cluster instantiation
3. **Evidence Sandbox** : No probe execution or Docker sandbox
4. **Threat Intel** : No EPSS/KEV enrichment
5. **Risk Scoring** : No priority computation function
6. **Persistence** : No SQLite/file storage
7. **Docker** : No containerization

---

## Phase 23 — Complete Code Documentation

### `backend/app/main.py` (30 lines)
- **Purpose:** FastAPI application entry point
- **Responsibilities:** Create app, configure CORS (localhost:3000), register 5 routers
- **Inputs:** None (module-level execution)
- **Outputs:** `app` ASGI application
- **Dependencies:** FastAPI, Starlette CORSMiddleware, all 5 route modules
- **Security:** CORS restricted to localhost:3000; credentials allowed

### `backend/app/mock/fixtures.py` (370 lines)
- **Purpose:** Define all system data as Python objects
- **Responsibilities:** Create 6 Assets, 6 TriageCases with full evidence/priority/approval data; export as `CASES: list[dict]`
- **Inputs:** None (all data hardcoded)
- **Outputs:** `CASES` list consumed by all route modules
- **Key detail:** `Finding` and `Cluster` models imported but never used; `CASES` list is the single source of truth for all case data

### `backend/app/cases/models.py` (109 lines)
- **Purpose:** Pydantic model definitions for the entire system
- **9 models:** Asset, Finding, Cluster, EvidenceObservation, ValidationResult, PriorityResult, AIAnalysis, ApprovalState, AuditEvent, TriageCase
- **Key:** `Finding` and `Cluster` are defined but never instantiated. `AIAnalysis` is duplicated in `ai/schemas.py`.

### `backend/app/api/case_routes.py` (41 lines)
- **Purpose:** Case listing and detail endpoints
- **State:** `_cases_store` (in-memory dict from fixtures), `_audit_store` (in-memory dict)
- **Key:** `_ensure_audit()` creates empty audit list for a case; `get_case()` attaches audit to response

### `backend/app/api/approval_routes.py` (134 lines)
- **Purpose:** Approve, reject, override endpoints with guard logic
- **Guards:** 400 (missing analyst_id), 404 (case not found), 409 (already decided: approve blocks after APPROVED/REJECTED/OVERRIDDEN; reject blocks after APPROVED/REJECTED; override blocks after APPROVED/REJECTED)
- **Override:** Mutates `priority.level` directly; records `old_priority`/`new_priority`/`reason` in audit metadata

### `backend/app/api/ai_routes.py` (22 lines)
- **Purpose:** AI analysis trigger endpoint
- **Key:** Calls `analyze_case(case)`, stores result in `case["ai_analysis"]`, returns `analysis.model_dump()`
- **Bug:** `_cases_store` is separate from `case_routes._cases_store`; mutations here don't propagate (and vice versa)

### `backend/app/api/audit_routes.py` (12 lines)
- **Purpose:** Audit trail retrieval endpoint
- **Key:** Returns 404 if case has no audit events (different from frontend mock which returns `[]`)

### `backend/app/api/dashboard_routes.py` (33 lines)
- **Purpose:** Aggregated dashboard statistics
- **Key:** Computes totals from `CASES` list at request time; no caching

### `backend/app/ai/engine.py` (104 lines)
- **Purpose:** AI analysis orchestration with fallback chain
- **Flow:** `_get_provider()` → `sanitize_case_for_llm()` → `provider.analyze()` → `validate_analysis()` → retry with stricter prompt → fallback to MockProvider → hardcoded minimal fallback
- **Provider selection:** `USE_MOCK_AI` env var (default: true); `AI_PROVIDER` env var (openai/anthropic)

### `backend/app/ai/sanitizer.py` (83 lines)
- **Purpose:** Prepare case data for LLM consumption by wrapping untrusted fields
- **24 fields** listed in `UNTRUSTED_FIELDS` (sanitizer.py:6-30: title, description, raw_evidence, cve, cwe, scanner, scanner_rule_id, hostname, environment, criticality, observed_at, summary, why_it_matters, evidence_summary, priority_explanation, investigation_questions, recommended_remediation, confidence_notes, limitations, level, status, actor, action, reason) + 3 nested `ASSET_FIELDS` (hostname, environment, criticality, sanitizer.py:33-37)
- **Method:** Control char strip → truncate to 2000 chars → wrap in `<UNTRUSTED field="name">...</UNTRUSTED>`

### `backend/app/ai/validator.py` (171 lines)
- **Purpose:** Validate AI analysis output against case input data
- **Checks:** Required fields, list types, CVE grounding (CVEs in output must exist in input), number grounding (numbers in output must exist in input), grounded_on non-empty
- **Returns:** `(AIAnalysis | None, list[str])` — parsed analysis + list of issues

### `backend/app/ai/providers/mock_provider.py` (132 lines)
- **Purpose:** Deterministic AI analysis builder for development/testing
- **Method:** String-template builder using case fields (title, CVE, CVSS, EPSS, KEV, hostname, etc.)
- **Output:** `model: "mock-v1"` — deterministic, repeatable, injection-safe
- **Key:** `_clean()` strips `<UNTRUSTED>` tags from input fields before using them

### `backend/app/ai/providers/openai_provider.py` (60 lines)
- **Purpose:** OpenAI API integration with fallback
- **Flow:** Check API key → import openai → create client → chat.completions.create() → parse response → fallback to mock on error
- **Model:** `OPENAI_MODEL` env var (default: `gpt-4o`)

### `backend/app/ai/providers/anthropic_provider.py` (63 lines)
- **Purpose:** Anthropic API integration with fallback
- **Flow:** Check API key → import anthropic → create client → messages.create() → parse response → fallback to mock on error
- **Model:** `ANTHROPIC_MODEL` env var (default: `claude-sonnet-4-20250514`)

### `frontend/lib/api/types.ts` (103 lines)
- **Purpose:** TypeScript type definitions matching backend Pydantic models
- **10 interfaces:** Asset, EvidenceObservation, ValidationResult, PriorityResult, AIAnalysis, ApprovalState, AuditEvent, TriageCase, DashboardStats

### `frontend/lib/providers.ts` (15 lines)
- **Purpose:** Provider switching based on `NEXT_PUBLIC_USE_MOCK` env var
- **Default:** Mock provider (useMock = true when env var is not "false")

### `frontend/lib/api/client.ts` (36 lines)
- **Purpose:** HTTP client with error handling
- **Base URL:** `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`)
- **Error:** Throws `ApiError` with status code and detail on non-2xx responses

### `frontend/lib/api/mockProvider.ts` (415 lines)
- **Purpose:** Complete frontend mock data layer with seeded fixtures, lifecycle audit events, and approval workflow
- **Key:** `FIXTURES` array (duplicated from backend); `ANALYSES` prebuilt analysis templates; `seedAuditLog()` generates clustered→validated→prioritized→analysis events at startup

### `frontend/lib/api/realProvider.ts` (96 lines)
- **Purpose:** Real API provider with graceful fallback to mock on any error
- **All 8 Provider methods** implemented: listCases, getCase, analyzeCase, approveCase, rejectCase, overrideCase, getAudit, getDashboardStats
- **Key:** Every method catches errors and falls back to mock with `console.warn`

### `frontend/app/page.tsx` (128 lines)
- **Purpose:** Dashboard page (home route `/`)
- **Renders:** KpiStrip, PipelineStrip, PriorityQueue, CaseTable
- **Data:** Fetches `getDashboardStats()` + `listCases()` in parallel

### `frontend/app/cases/page.tsx` (106 lines)
- **Purpose:** Cases list page (`/cases`)
- **Renders:** CaseTable with filter state from URL search params

### `frontend/app/cases/[id]/page.tsx` (177 lines)
- **Purpose:** Case detail page (`/cases/{id}`)
- **Renders:** CaseHeader, CasePipeline, EvidencePanel, PriorityBreakdown, AIAnalysisPanel, RemediationPanel, ThreatIntelPanel, DuplicateClusterPanel, ApprovalControls, AuditTimeline
- **Actions:** "Analyze" button triggers `analyzeCase()` then re-fetches case

### `frontend/components/dashboard/CaseTable.tsx` (288 lines)
- **Purpose:** Filterable, sortable case table with search
- **Filters:** Priority (P1-P4), Evidence status (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE/STALE), Approval status (PENDING/APPROVED/REJECTED/OVERRIDDEN), text search
- **Sorting:** By priority level (P1 first) then by score (descending)
- **Key:** Evidence filter uses `NOT_CONFIRMED` (underscore) — fixed during this audit from `NOT CONFIRMED` (space)

### `frontend/components/case/ApprovalControls.tsx` (310 lines)
- **Purpose:** Analyst decision UI with approve (double-click confirm), reject (modal with required reason), override (modal with priority selector + required reason)
- **Key:** Disables all buttons after decision; shows transition diagram for overrides

---

## Phase 24 — Merge Plan

**Recommended integration sequence (once Person 1/2/3 code exists):**

```
1. person4 (current — already exists as integration base)
   ↓
2. Person 1 branch: ingestion + normalization + dedup
   (adds POST /api/findings; instantiates Finding + Cluster models; adds normalization + dedup logic)
   ↓
3. Canonical contract alignment
   (ensure Person 1's Finding/Cluster schema matches Person 4's models.py exactly)
   ↓
4. Person 2 branch: evidence validation + sandbox
   (adds POST /api/validate/{cluster_id}; instantiates ValidationResult + EvidenceObservation; adds probe execution)
   ↓
5. Person 3 branch: risk scoring + threat intel
   (adds POST /api/score/{cluster_id}; implements priority formula; adds EPSS/KEV enrichment)
   ↓
6. Persistence layer
   (SQLite/file storage for approvals, audit, analyses; must survive restart)
   ↓
7. Docker harness
   (Dockerfile + docker-compose for backend, frontend, and a controlled vulnerable target)
   ↓
8. E2E test
   (automated test from ingestion through approval)
   ↓
9. Security hardening
   (auth, rate limiting, input validation on non-sanitized fields)
```

---

## Phase 25 — Hard Merge Gates

| Gate | Condition | Status | Verdict |
|---|---|---|---|
| Backend starts | `uvicorn backend.app.main:app` serves routes | ✅ PASS | |
| Frontend builds | `npm run build` completes clean | ✅ PASS | |
| Tests pass | Backend 16/16, frontend 8/8 | ✅ PASS | |
| API contracts match | Backend ↔ frontend field-for-field | ✅ PASS | |
| Ingestion exists | POST /api/findings or equivalent | ❌ FAIL | **MERGE BLOCKER** |
| Normalization exists | Finding → canonical schema | ❌ FAIL | **MERGE BLOCKER** |
| Dedup exists | Finding → Cluster | ❌ FAIL | **MERGE BLOCKER** |
| Evidence validation exists | Probe execution in sandbox | ❌ FAIL | **MERGE BLOCKER** |
| Risk scoring exists | Factors → score → P1-P4 | ❌ FAIL | **MERGE BLOCKER** |
| Persistence works | Restart test: data survives | ❌ FAIL | **MERGE BLOCKER** |
| Docker works | `docker compose up` from clean clone | ❌ FAIL | **MERGE BLOCKER** |
| E2E test exists | Automated end-to-end test | ❌ FAIL | **MERGE BLOCKER** |
| No secrets committed | Secret scan clean | ✅ PASS | |
| No .venv/node_modules committed | Clean tree | ✅ PASS | |

**8 MERGE BLOCKERS identified.**

---

## Phase 26 — Final Truth Report

### 1. What actually works today?
- FastAPI server serves 9 endpoints with real guard logic (400/404/409)
- Approve/reject/override workflow with audit trail creation
- AI analysis via mock-v1 with grounding validation
- Dashboard stats computed from fixture data
- Frontend SOC workbench: dashboard, case list, case detail with all panels
- Injection-safe rendering (18 tests total: 10 backend + 8 frontend)
- Real provider fallback (graceful degradation to mock on any error)

### 2. What partially works?
- Audit trail: events created correctly but lost on restart (no persistence)
- AI analysis: works with mock provider; paid providers (OpenAI/Anthropic) fall back to mock silently on this machine (no API keys configured)
- Frontend ↔ backend contract alignment: field-for-field match but approval response type mismatch (non-blocking)

### 3. What is fake/mock/simulated?
- All 6 TriageCase objects (hardcoded fixtures, not pipeline output)
- All priority scores (constant values, not computed)
- All evidence statuses (fixture attributes, not validation results)
- All finding counts (fixture constants, not dedup results)
- Frontend mock audit lifecycle events (generated from fixtures at startup)
- Frontend prebuilt analyses (template strings, not LLM output)
- `DuplicateClusterPanel` "3 FINDINGS → 1 CLUSTER → 1 TRIAGE CASE" (displays fixture data, not pipeline output)

### 4. What is broken?
- Persistence: all decisions, audit events, and analyses vanish on server restart
- Two independent case stores (case_routes vs ai_routes): mutations in one are invisible to the other
- `prev_hash` field name is misleading (stores previous event_id, not a hash)
- Documentation drift (stale component references, nonexistent localStorage toggle)

### 5. What is dangerous?
- No authentication (analyst identity unverified)
- Exception messages in HTTP 500 responses (information disclosure)
- No rate limiting
- No input validation on non-sanitized fields

### 6. What is undeployable?
- No Dockerfile → one-command deployment impossible
- No docker-compose.yml → no service orchestration
- Backend must run from repo root (undocumented import path requirement)
- No Makefile or shell scripts

### 7. What is duplicated?
- `AIAnalysis` model: defined in both `models.py` and `schemas.py`
- Case stores: `_cases_store` in both `case_routes.py` and `ai_routes.py`
- Fixture data: duplicated between backend `fixtures.py` and frontend `mockProvider.ts`

### 8. What branches can merge?
- `person4` can become the default branch (merge into empty `main`)

### 9. What branches cannot merge?
- No other branches exist to merge

### 10. What must be rewritten?
- Nothing — Person 4's code is well-structured and correctly implements its scope. The missing components (Person 1/2/3) need to be **added**, not rewritten.

### 11. What must be deleted?
- Unused `Finding` and `Cluster` models should be moved to Person 1's scope (or removed if Person 1 implements their own)
- Unused `httpx` dependency in `pyproject.toml`
- Stale documentation references

### 12. What is missing from PS16?
- 9.5 of 11 requirements are missing or partially implemented (see Phase 21)

### 13. Can the system currently demonstrate a real controlled vulnerability?
- **NO.** No scanner integration, no ingestion, no validation, no sandbox.

### 14. Can a fresh machine deploy it?
- **YES (manual, two terminals, from repo root)**. No Docker one-liner.

### 15. Can a judge independently reproduce the demo?
- **YES for the fixture-based SOC workbench walkthrough.** No for the PS16 end-to-end pipeline.

### 16. Does the current system genuinely solve PS16?
- **NO.** It implements 1.5 of 11 requirements. The core engine (ingestion → normalization → dedup → validation → scoring → case → approval → audit) does not exist. What exists is a well-built analyst workbench operating on pre-built data.

---

## CYBERYUKTI FINAL ENGINEERING VERDICT

```
============================================================
CYBERYUKTI FINAL ENGINEERING VERDICT
============================================================

Repository Health:        HEALTHY (clean git, no secrets, 81 tracked files)
Branch Health:            CLEAN (1 branch, linear history, synced to remote)
Code Quality:             GOOD (typed, tested, consistent patterns within Person 4 scope)
Security:                 ADEQUATE FOR LOCAL DEMO (no auth, but no dangerous surfaces)
Deployability:            PARTIAL (manual path works; no Docker one-liner)
Integration:              INCOMPLETE (Person 4 only; Persons 1/2/3 absent)
Test Confidence:          LOW-MODERATE (18 injection tests; no route/integration/E2E tests)
Real-World Readiness:     NOT READY (no scanner integration, no sandbox, no persistence)
PS16 Compliance:          NOT SATISFIED (1.5/11 requirements = 13.6%)

Person 1 (Ingestion):     NOT PRESENT IN REPOSITORY
Person 2 (Evidence):      NOT PRESENT IN REPOSITORY
Person 3 (Risk Engine):   NOT PRESENT IN REPOSITORY
Person 4 (Response/UI):   IMPLEMENTED AND VERIFIED

Fake/Mock Functionality:  All case data, priority scores, evidence statuses,
                          finding counts are fixture constants (not pipeline outputs)

Critical Security Issues: 0 CRITICAL, 0 HIGH, 1 LOW (exception message leakage)

Critical Merge Blockers:  8 (no ingestion, no normalization, no dedup, no
                          evidence validation, no risk scoring, no persistence,
                          no Docker, no E2E test)

Critical Deployment Blockers: 2 (no Dockerfile, backend must run from repo root)

Recommended Integration Branch: person4 (make it the default branch)
Recommended Merge Order: person4 → Person 1 → contract alignment → Person 2
                       → Person 3 → persistence → Docker → E2E test → hardening

FINAL PS16 STATUS:   NO (PARTIALLY at 13.6%)

MERGE STATUS:        NOT SAFE (8 blockers; DO NOT MERGE as PS16-complete solution)
============================================================
```
