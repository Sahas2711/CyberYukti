# CyberYukti — Current Architecture

**Status:** Fixture-driven workbench. PS16 completion 13.6%; the target architecture's first 6 stages (ingest→normalize→dedup→validate→score) are absent. See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phase 22.

## ASCII diagram (as-built, verified in source)

```
                    ┌───────────────────────────────────────────┐
                    │ backend/app/mock/fixtures.py:61-361        │
                    │ 6 HARDCODED TriageCase objects (CASE_001–6)│
                    │ 6 Asset constants; CASES list exported     │
                    │ fixtures.py:363-370                        │
                    └───────────────────┬───────────────────────┘
                                        │ CASES (dicts)
     ┌──────────────────────────────────┴─────────────────────────────┐
     ▼                                                                ▼
 ┌───────────────┐  ┌─────────────────────┐  ┌──────────────────┐
 │ case_routes   │  │ ai_routes           │  │ approval_routes  │
 │ _cases_store  │  │ _cases_store        │  │ (imports         │
 │ case_routes.  │  │ ai_routes.py:8      │  │  case_routes     │
 │ py:12         │  │ (INDEPENDENT COPY)  │  │  store)          │
 │ +_audit_store │  └──────────┬──────────┘  │  approval_routes │
 └──────┬────────┘             │             │  .py:7           │
        │                      │             └────────┬─────────┘
        └──────────────────────┼──────────────────────┘
                               ▼
                  ┌─────────────────────────────┐
                  │ FastAPI routes → JSON       │
                  │ main.py:21-30 (5 routers)   │
                  │ /health, /api/cases, ...    │
                  └──────────────┬──────────────┘
                                 │ JSON over HTTP :8000
                                 ▼
              ┌──────────────────────────────────────────────┐
              │ frontend  │  NEXT_PUBLIC_USE_MOCK != "false" │
              │           │  → mockProvider (default)        │
              │ providers.ts:10-12                           │
              │           │  else → realProvider (HTTP)      │
              │ realProvider.ts:11 (falls back to mock)      │
              └──────────────────────┬───────────────────────┘
                                     ▼
                  React SOC Workbench UI (dashboard, case list,
                  case detail: EvidencePanel, PriorityBreakdown,
                  DuplicateClusterPanel, AIAnalysisPanel, ...)
```

## Data path (executed end-to-end)
1. `fixtures.py:363-370` exports `CASES` (6 `TriageCase.model_dump()` dicts).
2. `case_routes.py:12` builds `_cases_store` (dict keyed by case_id); `_audit_store` at `case_routes.py:13` starts empty.
3. Routes serve dicts as JSON (list `case_routes.py:22-32`, detail `35-41`; approval `approval_routes.py:39-134`; audit `audit_routes.py:8-12`; stats `dashboard_routes.py:8-33`).
4. Frontend: `realProvider.ts` calls those endpoints; `getCase` re-fetch after approval (`realProvider.ts:24-31`).
5. Components render provider objects (`page.tsx`, `cases/[id]/page.tsx` — master doc Phase 23).

## AI engine flow (REAL, mock-only)
```
POST /api/ai/analyze/{id} (ai_routes.py:11-22)
  → analyze_case() (engine.py:45-104)
      → sanitize_case_for_llm() (sanitizer.py:47-63)   # control chars + <UNTRUSTED> wraps
      → provider.analyze()                             # MockProvider by default (engine.py:17-28)
      → validate_analysis() (validator.py:140-171)     # schema + CVE/number grounding
      → retry with stricter prompt (engine.py:63-77)   # if validation failed
      → fallback MockProvider (engine.py:84-86)        # if retry failed
      → hardcoded minimal AIAnalysis (engine.py:88-102)
  → result stored in ai_routes._cases_store + returned
```
Paid providers (`openai_provider.py`, `anthropic_provider.py`) exist but were never exercised (no API keys on this machine; silently fall back to mock) — master doc Phase 26 §2. Live probe: `model=mock-v1`, `grounded_on_count=6` (master doc Phase 3).

## Known bug — two independent in-memory case stores (branches_docs.md §6)
- `case_routes.py:12` and `ai_routes.py:8` each build a **separate** `{case_id: case}` dict from the same `CASES` fixture list.
- Approvals mutate the `case_routes`/`approval_routes` copy (`approval_routes.py:7`); `POST /api/ai/analyze` reads and mutates the `ai_routes` copy.
- Result: an AI analysis or decision applied through one route is **invisible** to the other — silent data-consistency bug (master doc Phase 26 §4).
- Compounding: `ai_routes.py:17-22` catches exceptions and returns a 500 with `str(e)`, so engine fallbacks are never surfaced to the client.

## Not shown in the diagram (because they do not exist)
- Scanner → ingestion, sandbox/probe execution, dedup/clustering, risk formula, persistence, Docker. All NOT IMPLEMENTED (master doc Phases 5-7, 12).