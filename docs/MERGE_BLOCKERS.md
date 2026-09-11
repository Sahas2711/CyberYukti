# CyberYukti — Hard Merge Blockers
Status: VERIFIED — 8 blockers from master doc Phase 25.

**All 8 must be resolved before `person4` can be merged as a PS16-complete solution.**

---

## BLOCKER 1: No Ingestion
- **Condition violated:** PS16 requires finding ingestion from scanners.
- **Evidence:** Phase 5 — no `POST /api/findings` route; grep returns 0 hits for any ingestion endpoint.
- **What unblocks it:** Implement `POST /api/findings` that accepts scanner JSON and creates `TriageCase` instances.

## BLOCKER 2: No Normalization
- **Condition violated:** PS16 requires heterogeneous scanner output normalized to canonical `Finding` schema.
- **Evidence:** Phase 5 — `Finding` model (`models.py:13-24`) defined but never instantiated; grep for `Finding(` returns 0 hits.
- **What unblocks it:** Implement normalization logic converting raw scanner fields to canonical `Finding` attributes.

## BLOCKER 3: No Deduplication
- **Condition violated:** PS16 requires duplicate findings clustered into incidents.
- **Evidence:** Phase 5 — `Cluster` model (`models.py:27-32`) unused; `finding_count` in `fixtures.py:67` is a hardcoded integer, not a dedup result.
- **What unblocks it:** Implement dedup algorithm that groups `Finding` instances into `Cluster` objects.

## BLOCKER 4: No Evidence Validation
- **Condition violated:** PS16 requires evidence validation with probe execution against a target.
- **Evidence:** Phase 6 — zero subprocess, Docker, or network-validation code; grep for `subprocess`, `docker`, `httpx.get` returns 0 backend hits.
- **What unblocks it:** Implement evidence validation engine with probe execution in a sandbox.

## BLOCKER 5: No Risk Scoring
- **Condition violated:** PS16 requires deterministic priority computation from validated factors.
- **Evidence:** Phase 7 — `priority.score` values are fixture constants (`fixtures.py:96-108`); `formula_version="1.0.0"` set but no formula code exists.
- **What unblocks it:** Implement `compute_priority(factors: dict) -> PriorityResult` with documented thresholds.

## BLOCKER 6: No Persistence
- **Condition violated:** PS16 requires audit trail to survive restart.
- **Evidence:** Phase 8 — all stores are in-memory dicts (`case_routes.py:12`, `ai_routes.py:8`, `approval_routes.py:15`); restart wipes data.
- **What unblocks it:** Add SQLite or file-based storage for cases, approvals, and audit events.

## BLOCKER 7: No Docker Harness
- **Condition violated:** PS16 requires reproducible deployment; no one-command demo possible.
- **Evidence:** Phase 12 — no Dockerfile, docker-compose.yml, Makefile, or shell script exists; glob returns 0 hits.
- **What unblocks it:** Create `Dockerfile` + `docker-compose.yml` for backend, frontend, and controlled target.

## BLOCKER 8: No E2E Test
- **Condition violated:** PS16 requires automated end-to-end test from ingestion through approval.
- **Evidence:** Phase 15 — 0 route tests, 0 integration tests, 0 E2E tests; all verification was manual live probes.
- **What unblocks it:** Write automated test covering ingestion → normalization → dedup → validation → scoring → approval.

---

**MERGE STATUS: NOT SAFE**
