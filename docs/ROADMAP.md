# CyberYukti — Prioritized Roadmap
Status: VERIFIED — work items derived from integration gaps (Phases 5–7, 12, 15).

**Maps each gap to a deliverable with acceptance criteria and build order.**

---

## P0 — Must Complete (PS16 Core Pipeline)

### P0-1: Ingestion + Normalization + Dedup
- **Deliverable:** `POST /api/findings` accepts scanner JSON; normalizes to `Finding`; clusters into `Cluster`.
- **Acceptance criteria:** POST 3 duplicate findings → 1 `Cluster` with `finding_ids`; `GET /api/clusters` returns it; `finding_count` is computed.
- **Order:** First (blocks all downstream stages). Referenced in merge plan Stage 2.

### P0-2: Priority Computation Function
- **Deliverable:** `compute_priority(factors: dict) -> PriorityResult` — deterministic formula.
- **Acceptance criteria:** Same input factors → same output; formula documented; `override` recomputes score.
- **Order:** After P0-1. Referenced in merge plan Stage 5.

### P0-3: Persistence Layer
- **Deliverable:** SQLite/file storage for cases, approvals, audit events, analyses.
- **Acceptance criteria:** Approve case → restart → case retains status + audit history.
- **Order:** After P0-2. Referenced in merge plan Stage 6.

### P0-4: Docker Harness
- **Deliverable:** `Dockerfile` + `docker-compose.yml` for backend + frontend + controlled target.
- **Acceptance criteria:** Clean clone → `docker compose up` → both servers accessible.
- **Order:** After P0-3. Referenced in merge plan Stage 7.

### P0-5: E2E Test
- **Deliverable:** One automated test from ingestion through approval.
- **Acceptance criteria:** `pytest` passes; test completes without manual intervention.
- **Order:** After P0-4. Referenced in merge plan Stage 8.

## P1 — Required Before Production

### P1-1: Evidence Sandbox with Honest Isolation
- **Deliverable:** Probe execution sandbox (Docker or subprocess) with documented isolation limits.
- **Acceptance criteria:** Probe runs against target; `ValidationResult` computed; isolation boundaries documented.
- **Order:** After P0-1. Referenced in merge plan Stage 4.

### P1-2: EPSS/KEV Enrichment
- **Deliverable:** Live query to First.org EPSS API and CISA KEV database.
- **Acceptance criteria:** CVE input → live EPSS score; KEV lookup → boolean; values not hardcoded.
- **Order:** After P0-2. Referenced in merge plan Stage 5.

### P1-3: Authentication
- **Deliverable:** JWT or API key auth on all non-health endpoints.
- **Acceptance criteria:** Unauthenticated request → 401; `analyst_id` derived from token, not body.
- **Order:** After P0-3. Referenced in merge plan Stage 9.

### P1-4: Rate Limiting
- **Deliverable:** Per-IP or per-key rate limiting middleware.
- **Acceptance criteria:** Exceed limit → 429 response.
- **Order:** After P1-3. Referenced in merge plan Stage 9.

### P1-5: Route Tests
- **Deliverable:** Automated `pytest` tests for all 9+ endpoints using httpx AsyncClient.
- **Acceptance criteria:** All route tests pass; cover happy path + error cases (400/404/409).
- **Order:** Parallel with P0-4/P0-5. Referenced in merge plan Stage 8.

## P2 — Enhancement

### P2-1: Paid-Provider Adversarial Testing
- **Deliverable:** Injection/hallucination tests against real OpenAI/Anthropic API calls.
- **Acceptance criteria:** Tests pass with real LLM; guardrails prevent CVE hallucination.
- **Order:** After P1-1 (sandbox needed for safe testing).

### P2-2: Local OSS LLM Integration
- **Deliverable:** Local model (e.g., Llama, Mistral) as fallback provider.
- **Acceptance criteria:** Provider loads model; analysis output matches `AIAnalysis` schema.
- **Order:** After P2-1.

### P2-3: Documentation Refresh
- **Deliverable:** Update stale docs (`frontend-ui-documentation.md`, `person4-failure-checklist.md`); remove references to deleted components and nonexistent localStorage toggle.
- **Acceptance criteria:** All doc references match current codebase; no stale claims.
- **Order:** After P0-5 (docs should reflect final state).
