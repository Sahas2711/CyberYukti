# CyberYukti — Data Flow

**Status:** 3 end-to-end paths REAL (case read, approval, AI-analysis-on-fixture); all other "pipeline" displays are FIXTURE-only. No path ingests live scanner data. See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phases 3-4, 16.

## Path 1 — Case listing / detail (REAL, executed)
```
fixtures.py CASES:363-370 → case_routes._cases_store:12
  → GET /api/cases (case_routes.py:22-32)  /  GET /api/cases/{id} (case_routes.py:35-41)
  → realProvider.listCases:15-22 / getCase:24-31
  → CaseTable (dashboard) / case detail page (cases/[id]/page.tsx)
```
- `GET /api/cases` verified: 6 items; `GET /api/cases/{id}` verified: 200/404 (master doc Phase 3).

## Path 2 — Dashboard stats (REAL, executed)
```
CASES:363-370 → dashboard_routes.py:8-33 (sums finding_count, statuses, priorities at request time)
  → realProvider.getDashboardStats:87-94 → KpiStrip / PipelineStrip / PriorityQueue
```
- Verified: P1=2 after override probe changed (master doc Phase 3). Stats are aggregation of fixture constants — no caching (`dashboard_routes.py:10`).

## Path 3 — AI analysis (REAL over fixture input)
```
POST /api/ai/analyze/{id} (ai_routes.py:11-22)
  → ai_routes._cases_store:8 (stale copy — see bug below)
  → engine.analyze_case (engine.py:45) → sanitizer (sanitizer.py:47-63)
  → MockProvider.analyze:16-132 → validator (validator.py:140-171) → AIAnalysis
  → case["ai_analysis"] stored + returned; 200 (`model=mock-v1`)
```
- Verified: `POST /api/ai/analyze/CASE-001` → `model=mock-v1`, `grounded_on_count=6` (master doc Phase 3). NOTE: result stored in the **`ai_routes` copy** — invisible to `case_routes` reads (branches_docs.md §6).

## Path 4 — Approval / override (REAL, executed)
```
approve/reject/override body → approval_routes.py:40,69,100
  → guards (400/404/409) → mutate case_routes._cases_store + approval state
  → _add_audit_event:18-36 (appends to _audit_store) → ApprovalState JSON
  → realProvider.approveCase:42-52 / rejectCase:54-64 / overrideCase:66-76
  → ApprovalControls re-fetches case via getCase()
```
- Verified: override CASE-005 P2→P1, stats P1 2→3, audit event with UUID+prev_hash (master doc Phase 3).

## Path 5 — Audit (REAL backend / MOCK frontend)
- Backend: `audit_routes.py:8-12` reads `_audit_store` (imported from `case_routes.py:3`); 404 if empty (`audit_routes.py:11`).
- Frontend mock: `seedAuditLog()` fabricates clustered→validated→prioritized→analysis events per case (`mockProvider.ts:224-303`); `getAudit` returns `[]` for missing (`:305-308`). Real mode: `realProvider.getAudit:78-85` (404 → mock fallback).

## FIXTURE-only paths (no backend, no execution)
| Path | Component | Evidence | Classification |
|---|---|---|---|
| `FIXTURES` array → mock provider | `mockProvider.ts:9-140` (`_cases:221`) | FE serves cases when `NEXT_PUBLIC_USE_MOCK !== "false"` (`providers.ts:10-12`) | MOCK |
| Prebuilt analyses | `ANALYSES` `mockProvider.ts:142-208` | template strings keyed by case_id; not LLM output | MOCK |
| Lifecycle audit events | `seedAuditLog()` `mockProvider.ts:224-303` | generated from fixture timestamps at startup | MOCK |
| "3 FINDINGS → 1 CLUSTER → 1 TRIAGE CASE" | `DuplicateClusterPanel.tsx:23-48` | renders fixture `findingCount` (`fixtures.py:67`) | FIXTURE display |
| Cluster / Finding objects | `models.py:13-32` | never produced by any code | UNUSED |
| Scanner findings | `sources` names `fixtures.py:66` | strings only — no scanner output exists | NOT IMPLEMENTED |

## Two independent stores bug (affects Paths 3 vs 1/4)
- `case_routes.py:12` vs `ai_routes.py:8`: two copies of the case dict.
- Sequence: approve via Path 4 → `GET /api/ai/analyze` (Path 3) reads an un-approval'd copy; AI result written via Path 3 never appears in Path 1 detail. Silent inconsistency (master doc Phase 26 §4; branches_docs.md §6).

## Not-executed-to-production paths
- Paid LLM providers (OpenAI `openai_provider.py`, Anthropic `anthropic_provider.py`): branch exists, never exercised here (no API keys); silent mock fallback (master doc Phase 26 §2). NOT EXECUTED.
- All scanner→ingestion→normalization→dedup→validation→scoring paths: no code exists. NOT EXECUTED.