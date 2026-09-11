# CyberYukti — Demo Readiness Assessment
Status: VERIFIED — based on master doc Phases 16–17, 26.

**Verdict: Fixture-based SOC workbench demo is reproducible. PS16 pipeline demo is not.**

---

## What CAN Be Demonstrated Today

### Fixture Walkthrough Steps (all VERIFIED)

1. **Start backend from repo root**
   `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` — MUST run from root, not `backend/`. `GET /health` → 200. VERIFIED.

2. **Start frontend**
   `cd frontend && npm install && npm run dev` — serves on `localhost:3000`. CORS trusts this origin. VERIFIED.

3. **Dashboard KPI**
   Open `http://localhost:3000` — KpiStrip shows total_findings, unique_clusters, confirmed/not_confirmed/inconclusive counts. All computed from fixture constants. VERIFIED.

4. **Case detail panels**
   Click any case → CaseHeader, CasePipeline, EvidencePanel, PriorityBreakdown, ThreatIntelPanel, DuplicateClusterPanel, AIAnalysisPanel, RemediationPanel. All render from data objects. VERIFIED.

5. **Analyze button → mock-v1**
   Click "Analyze" → `POST /api/ai/analyze/{id}` → `model=mock-v1`, grounded analysis returned. VERIFIED (mock only).

6. **Approve/reject/override with audit**
   Approve with analyst_id → 200 + audit event. Override CASE-005 P2→P1 → priority mutation + audit with old_priority/new_priority/reason. VERIFIED.

7. **Dashboard stats after override**
   `GET /api/dashboard/stats` → p1 count incremented. VERIFIED.

### Critical Caveat
- All 6 cases are hardcoded fixtures. No real scanner data enters the system.
- Restart wipes all overrides, approvals, and audit events.

---

## What CANNOT Be Demonstrated

| Capability | Status | Blocker |
|---|---|---|
| Scanner → ingestion → case | NOT IMPLEMENTED | No `POST /api/findings` (Phase 5) |
| Deduplication of duplicates | NOT IMPLEMENTED | `finding_count` is constant (Phase 5) |
| Evidence probe execution | NOT IMPLEMENTED | No sandbox/probe code (Phase 6) |
| Priority computation | NOT IMPLEMENTED | Scores are constants (Phase 7) |
| Docker one-command demo | NOT IMPLEMENTED | No Dockerfile (Phase 12) |

---

## Five Required Demo Scenarios (Phase 17)

| # | Scenario | Status | Evidence |
|---|---|---|---|
| 1 | Confirmed vulnerability → evidence confirms → P1/P2 | **MOCK** | CASE-001 has CONFIRMED + P1, but both are fixture constants |
| 2 | False positive → evidence contradicts → risk reduced | **MOCK** | CASE-002 has NOT_CONFIRMED + P2; fixture constants |
| 3 | Duplicate findings → normalized → deduped → one incident | **MOCK** | `sources=["nuclei","semgrep","burp"]` + `finding_count=3`; fixture constants |
| 4 | Malicious scanner output → sanitized → no execution | **PARTIAL** | Sanitizer + validator work; but ingestion path doesn't exist |
| 5 | Priority override → reason recorded → audit event | **WORKING** | Live probe: CASE-005 P2→P1 → audit with old/new priority |

**Summary:** 1 WORKING, 1 PARTIAL, 3 MOCK.

---

## Judge Reproducibility
- **Can independently reproduce:** Yes — fixture-based SOC workbench walkthrough (steps 1–7).
- **Cannot independently reproduce:** PS16 end-to-end pipeline (scanner → case → approval).
