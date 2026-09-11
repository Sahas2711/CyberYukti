# CyberYukti — Integration Gap Catalog
Status: VERIFIED — gaps enumerated from master doc Phases 5–7, 12, 15, 21–22.

**10 gaps prevent PS16 compliance. Each is a merge blocker.**

---

## GAP 1: No Ingestion Endpoint
- **What:** No `POST /api/findings` or any route accepts scanner output (JSON/SARIF/JSONL).
- **Where it must plug in:** New route in `backend/app/api/` registered in `main.py`.
- **Currently occupies that space:** Nothing. `fixtures.py` is the sole data source.
- **Evidence:** Phase 5 — "No ingestion endpoint exists." grep for `POST.*finding` returns 0 hits.
- **Verification:** POST valid JSON findings → HTTP 201 → cases created.

## GAP 2: No Normalized Finding Instance
- **What:** `Finding` model defined (`models.py:13-24`) but never instantiated. No code converts heterogeneous scanner output to canonical schema.
- **Where it must plug in:** Normalization function called from ingestion endpoint.
- **Currently occupies that space:** Fixture constants — each case hardcodes `source`, `vulnerability`, etc.
- **Evidence:** Phase 5 — "`Finding` model defined but never instantiated." grep for `Finding(` returns 0 hits.
- **Verification:** Input raw scanner JSON → output `Finding` instance with all 11 fields populated.

## GAP 3: No Cluster Instance
- **What:** `Cluster` model defined (`models.py:27-32`) but never instantiated. `finding_count` in fixtures is a hardcoded integer, NOT a dedup result.
- **Where it must plug in:** Deduplication/clustering function after normalization.
- **Currently occupies that space:** `finding_count=3` in `fixtures.py:67` — hand-written constant.
- **Evidence:** Phase 5 — "`Cluster` model defined but never instantiated." `DuplicateClusterPanel.tsx:26-28` renders the constant.
- **Verification:** Input 3 duplicate findings → output 1 `Cluster` with `finding_ids` list.

## GAP 4: No Probe Execution
- **What:** No evidence validation probe executes against any target. No subprocess, no network call, no Docker container.
- **Where it must plug in:** Evidence validation engine (Person 2 scope).
- **Currently occupies that space:** `evidence.status` and `evidence.confidence` are fixture attributes (`fixtures.py:69-93`).
- **Evidence:** Phase 6 — "grep for `subprocess`, `docker`, `requests.get` returns 0 hits."
- **Verification:** Probe runs against target → `ValidationResult` with computed `status` and `confidence`.

## GAP 5: No Sandbox
- **What:** No Docker or subprocess sandbox for evidence validation probes. No isolation boundary exists.
- **Where it must plug in:** Docker container or subprocess wrapper around probe execution.
- **Currently occupies that space:** Nothing — no sandbox code, no Dockerfile (Phase 12).
- **Evidence:** Phase 12 — "No Dockerfile, docker-compose.yml, Makefile, or shell script exists." glob for `**/Dockerfile*` returns 0 hits.
- **Verification:** `docker compose up` starts backend + sandbox + target.

## GAP 6: No Priority Computation
- **What:** `PriorityResult.score` values (92.5, 45.2, etc.) are fixture constants. No formula computes them. `formula_version="1.0.0"` is set but no code exists.
- **Where it must plug in:** `compute_priority(factors: dict) -> PriorityResult` function (Person 3 scope).
- **Currently occupies that space:** Literal numbers in `fixtures.py:96-108`. Override at `approval_routes.py:128` mutates `level` without recomputing `score`.
- **Evidence:** Phase 7 — "no formula code exists." Cannot answer: "What formula produces 92.5 from these factors?"
- **Verification:** Input factors dict → deterministic output matches `PriorityResult` schema; override recomputes.

## GAP 7: No EPSS/KEV Enrichment
- **What:** `threat_intelligence` dict contains hardcoded `cvss`, `epss`, `kev` values. No live query to First.org EPSS API or CISA KEV database.
- **Where it must plug in:** Threat intel enrichment function before risk scoring.
- **Currently occupies that space:** `fixtures.py:94` — constant dict per case.
- **Evidence:** Phase 7 — "No EPSS/KEV enrichment." grep for `first.org`, `cisa.gov` returns 0 hits.
- **Verification:** Query EPSS for CVE → live score returned; KEV lookup → boolean.

## GAP 8: No Persistence Layer
- **What:** All stores are in-memory Python dicts. Audit events, approvals, analyses vanish on server restart.
- **Where it must plug in:** SQLite/file-based storage layer replacing `_cases_store` and `_audit_store`.
- **Currently occupies that space:** `_cases_store` (`case_routes.py:12`, `ai_routes.py:8`); `_audit_store` (`approval_routes.py:15`).
- **Evidence:** Phase 8 — "PARTIAL (lost on restart)." Phase 26 — "all decisions, audit events, and analyses vanish on server restart."
- **Verification:** Start server → approve case → restart server → case still shows APPROVED.

## GAP 9: No Docker Harness
- **What:** No Dockerfile, no docker-compose.yml. One-command deployment impossible. Two-terminal manual start required.
- **Where it must plug in:** Root `Dockerfile` + `docker-compose.yml` (backend + frontend + target).
- **Currently occupies that space:** Nothing (Phase 12).
- **Evidence:** Phase 12 — "NO DOCKER FILES EXIST." Glob for `**/Dockerfile*`, `**/docker-compose*` returns 0 hits.
- **Verification:** Clean clone → `docker compose up` → both servers accessible.

## GAP 10: No Route/E2E Tests
- **What:** 0 automated route tests, 0 integration tests, 0 E2E tests. All API verification was manual live probes.
- **Where it must plug in:** `pytest` route tests (httpx AsyncClient or similar); frontend E2E (Playwright/Cypress).
- **Currently occupies that space:** 16 backend unit tests (mock-only) + 8 frontend injection tests (Phase 15).
- **Evidence:** Phase 15 — "No route/API tests (all endpoints tested only via manual live probes)." Coverage: integration=0, E2E=0.
- **Verification:** `pytest` passes route tests; E2E test runs ingestion→approval without manual intervention.
