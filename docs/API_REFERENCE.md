# CyberYukti — API Reference

**Status:** 9 endpoints exist and are VERIFIED by live HTTP probes (master doc Phase 10; branches_docs.md §12). 4 PS16-required endpoints NOT IMPLEMENTED. No route-level automated tests exist (branches_docs.md §13).

## Implemented endpoints (all VERIFIED)

| # | Method | Path | Handler (file:line) | Input | Output | Error codes |
|---|---|---|---|---|---|---|
| 1 | GET | `/health` | `main.py:28-30` | — | `{"status":"ok"}` | — |
| 2 | GET | `/api/cases` | `case_routes.py:22-32` | query `priority`, `status` (optional) | `TriageCase[]` (6) | — |
| 3 | GET | `/api/cases/{case_id}` | `case_routes.py:35-41` | path `case_id` | `TriageCase` | 404 |
| 4 | POST | `/api/cases/{case_id}/approve` | `approval_routes.py:39-65` | `{analyst_id, reason?}` | `ApprovalState` | 400 / 404 / 409 |
| 5 | POST | `/api/cases/{case_id}/reject` | `approval_routes.py:68-96` | `{analyst_id, reason}` | `ApprovalState` | 400 / 404 / 409 |
| 6 | POST | `/api/cases/{case_id}/override` | `approval_routes.py:99-134` | `{analyst_id, override_priority, reason}` | `ApprovalState` | 400 / 404 |
| 7 | GET | `/api/cases/{case_id}/audit` | `audit_routes.py:8-12` | path `case_id` | `AuditEvent[]` | 404 |
| 8 | POST | `/api/ai/analyze/{case_id}` | `ai_routes.py:11-22` | path `case_id` | `AIAnalysis` (dumped) | 404 / 500 |
| 9 | GET | `/api/dashboard/stats` | `dashboard_routes.py:8-33` | — | `DashboardStats` | — |

### Guard semantics (VERIFIED, master doc Phases 3, 8)
- **400:** missing `analyst_id` (`approval_routes.py:49-50`), missing `reason` for reject (`:80-81`), `override_priority` not in P1-P4 (`:112-113`), missing reason for override (`:114-115`).
- **404:** case not found (`approval_routes.py:42-43,71-72,102-103`; `case_routes.py:38-39`; `ai_routes.py:14-15`); audit trail not found (`audit_routes.py:10-11`).
- **409:** already decided — approve blocks unless PENDING/REJECTED/OVERRIDDEN (`approval_routes.py:53`); reject blocks unless PENDING/OVERRIDDEN (`:84`); override blocks unless PENDING (`:117` reads prev but not guard-explicit — see note).
- **500:** AI analysis failure — returns `str(e)` in detail (`ai_routes.py:21-22`), information-disclosure LOW (master doc Phase 13).

### Behavioral notes
- Override mutates `case["priority"]["level"]` in place without recomputing `score` (`approval_routes.py:128`) — score/level can desync (master doc Phase 7).
- Verify note (branches_docs.md §12): reject row lists `200 / 400 / 404` — the 409 guard exists at `approval_routes.py:84-85` but was not probed in the recorded reject run; approve/override 409s were live-verified. Recording as observed with this caveat.
- All endpoints are **unauth'd**; `analyst_id` accepted verbatim (`approval_routes.py:46,76,106`) — analyst impersonation possible (branches_docs.md §8).

## Missing endpoints — PS16 required, NOT IMPLEMENTED

| Method | Path | PS16 need | Missing piece |
|---|---|---|---|
| POST | `/api/findings` | ingestion | no route, no parser |
| POST | `/api/validate/{cluster_id}` | evidence validation | no sandbox/probe engine |
| POST | `/api/score/{cluster_id}` | risk scoring | no formula |
| GET | `/api/clusters` | cluster listing | no dedup |

- Full tally (branches_docs.md §12): "No endpoint exists in docs but not in code (and vice versa for the routes above)" for the 9 implemented; the 4 above are missing from both.

## Not covered
- No timeout handling, no rate limiting (master doc Phase 10).
- CORS restricted to `http://localhost:3000` with `allow_methods=["*"]`, `allow_credentials=True` (`main.py:13-19`).
- Nothing but the 9 endpoints is served; `frontend/app` pages are reached through Next.js, not this API. NOT EXECUTED for HTTP automation: all 9 rows above were verified via manual live probes, not an automated suite (branches_docs.md §13).