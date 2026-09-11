# CyberYukti — Ordered Integration Merge Plan
Status: VERIFIED — plan from master doc Phase 24, expanded with gate criteria.

**Base branch: `person4` (only substantive branch). Merge order below.**

---

## Stage 1: person4 as Integration Base
- **Action:** Make `person4` the default branch (GitHub Settings → Default Branch).
- **Files touched:** None — GitHub config only.
- **Gate:** `main` becomes `person4`. `GET /health` → 200.

## Stage 2: Person 1 — Ingestion + Normalization + Dedup
- **Action:** Add `POST /api/findings` endpoint; implement normalization (scanner JSON → canonical `Finding`); implement dedup (`Finding` → `Cluster`).
- **Files touched:** New route file (`ingestion_routes.py`), `main.py` (router registration), `models.py` (`Finding`/`Cluster` instantiation logic).
- **Gate:** POST 3 duplicate findings → 1 `Cluster` created; `GET /api/clusters` returns it; finding_count is computed, not constant.

## Stage 3: Canonical Contract Alignment
- **Action:** Verify Person 1's `Finding`/`Cluster` schema matches `models.py:13-32` field-for-field. Align frontend `types.ts` if needed.
- **Files touched:** `models.py`, `types.ts`, `fixtures.py` (update fixture format if schema changed).
- **Gate:** `pytest` passes; `npm run build` clean; all 9 existing endpoints still return 200.

## Stage 4: Person 2 — Evidence Validation + Sandbox
- **Action:** Add evidence validation engine with probe execution. Implement sandbox (Docker or subprocess with honest isolation docs).
- **Files touched:** New route file (`validation_routes.py`), `main.py`, `models.py` (`ValidationResult` instantiation), new sandbox module.
- **Gate:** `POST /api/validate/{cluster_id}` returns `ValidationResult` with computed `status` (not fixture constant); probe runs in sandbox; no sandbox escape path.

## Stage 5: Person 3 — Risk Scoring + Threat Intel
- **Action:** Implement `compute_priority(factors) -> PriorityResult`; add EPSS enrichment (First.org API) and KEV enrichment (CISA database).
- **Files touched:** New module (`risk_engine.py`), `priority_routes.py` (or add to validation_routes), `main.py`.
- **Gate:** `POST /api/score/{cluster_id}` returns computed `score` and `level`; override recomputes; EPSS/KEV values are live, not constants.

## Stage 6: Persistence Layer
- **Action:** Replace in-memory dicts with SQLite or file-based storage for cases, approvals, audit events, and analyses.
- **Files touched:** New persistence module, `case_routes.py`, `approval_routes.py`, `ai_routes.py`, `audit_routes.py`.
- **Gate:** Approve a case → restart server → case retains APPROVED status and audit history.

## Stage 7: Docker Harness
- **Action:** Create `Dockerfile` (backend), `Dockerfile` (frontend), `docker-compose.yml` (backend + frontend + controlled target).
- **Files touched:** New files at repo root. Possibly `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`.
- **Gate:** Clean clone → `docker compose up` → both servers accessible on expected ports.

## Stage 8: E2E Test
- **Action:** One automated test from ingestion through approval. Backend route test + optional frontend E2E.
- **Files touched:** New test files in `backend/tests/` and/or `frontend/tests/`.
- **Gate:** `pytest` passes all route tests; E2E test completes without manual intervention.

## Stage 9: Security Hardening
- **Action:** Add authentication (JWT or API key), rate limiting, input validation on non-sanitized fields, generic error messages.
- **Files touched:** New auth module, `main.py` (middleware), route files (auth dependency), `ai_routes.py` (error handling).
- **Gate:** Unauthenticated requests → 401; rate-limited requests → 429; HTTP 500 no longer leaks `str(e)`.
