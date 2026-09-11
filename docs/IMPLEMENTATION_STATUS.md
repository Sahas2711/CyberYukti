# CyberYukti — Implementation Status Ledger
Status: VERIFIED — authored from master doc Phases 1–26 and branches_docs.md.

**PS16 completion: 1.5 / 11 (13.6%) | VERDICT: DO NOT MERGE**

---

## API Endpoints (9 implemented)

| Component | Status | File:Line | Evidence |
|---|---|---|---|
| `GET /health` | VERIFIED | `main.py:28-30` | Live probe → 200 `{"status":"ok"}` (Phase 10) |
| `GET /api/cases` | VERIFIED | `case_routes.py:22-32` | Live probe → 6 items (Phase 10) |
| `GET /api/cases/{id}` | VERIFIED | `case_routes.py:35-41` | Live probe → 200/404 (Phase 10) |
| `POST /api/cases/{id}/approve` | VERIFIED | `approval_routes.py:39-65` | Live probe → 200/400/404/409 (Phase 10) |
| `POST /api/cases/{id}/reject` | VERIFIED | `approval_routes.py:68-96` | Live probe → 200/400/404/409 (Phase 10) |
| `POST /api/cases/{id}/override` | VERIFIED | `approval_routes.py:99-134` | Live probe: P2→P1 mutation (Phase 8) |
| `GET /api/cases/{id}/audit` | PARTIAL | `audit_routes.py:8-12` | Works; lost on restart (Phase 8) |
| `POST /api/ai/analyze/{id}` | MOCK | `ai_routes.py:11-22` | Returns `model=mock-v1`; no real LLM (Phase 8) |
| `GET /api/dashboard/stats` | VERIFIED | `dashboard_routes.py:8-33` | Computed from fixture constants (Phase 8) |

## Missing PS16 Endpoints

| Component | Status | Evidence |
|---|---|---|
| `POST /api/findings` | NOT IMPLEMENTED | Phase 5 — no ingestion route exists |
| `POST /api/validate/{id}` | NOT IMPLEMENTED | Phase 6 — no probe execution |
| `POST /api/score/{id}` | NOT IMPLEMENTED | Phase 7 — no formula code |
| `GET /api/clusters` | NOT IMPLEMENTED | Phase 5 — no cluster listing |

## AI Engine + Providers

| Component | Status | File | Evidence |
|---|---|---|---|
| AI engine orchestrator | VERIFIED | `engine.py:45-104` | Sanitize→analyze→validate→fallback chain (Phase 8) |
| Sanitizer | VERIFIED | `sanitizer.py:40-44` | 24 untrusted fields wrapped; 10 payloads pass (Phase 13) |
| Grounding validator | VERIFIED | `validator.py:63-108` | CVE/number checks; 3 hallucination tests (Phase 15) |
| MockProvider | MOCK | `mock_provider.py:16-132` | String builder; `model=mock-v1` (Phase 3) |
| OpenAI provider | NOT EXECUTED | `openai_provider.py` | Falls back to mock; no API key configured (Phase 8) |
| Anthropic provider | NOT EXECUTED | `anthropic_provider.py` | Falls back to mock; no API key configured (Phase 8) |

## Person 1-3 Components (All NOT IMPLEMENTED)

| Component | Status | Evidence |
|---|---|---|
| Ingestion endpoint | NOT IMPLEMENTED | Phase 5 — 0 ingestion routes |
| Finding normalization | NOT IMPLEMENTED | Phase 5 — `Finding` model unused |
| Deduplication / clustering | NOT IMPLEMENTED | Phase 5 — `Cluster` model unused |
| Evidence validation engine | NOT IMPLEMENTED | Phase 6 — 0 subprocess/Docker hits |
| Sandbox / probe execution | NOT IMPLEMENTED | Phase 6 — no sandbox code |
| Risk scoring function | NOT IMPLEMENTED | Phase 7 — scores are fixture constants |
| EPSS/KEV enrichment | NOT IMPLEMENTED | Phase 7 — `threat_intelligence` is constant |

## Approval + Audit Flow

| Component | Status | File:Line | Evidence |
|---|---|---|---|
| Approve guard | VERIFIED | `approval_routes.py:46` | Blocks double-approve → 409 (Phase 8) |
| Reject guard | VERIFIED | `approval_routes.py:76` | Blocks reject-after-approve → 409 (Phase 8) |
| Override mutation | VERIFIED | `approval_routes.py:128` | Mutates `priority.level`; records old/new (Phase 8) |
| Audit event creation | VERIFIED | `approval_routes.py:18-36` | UUID + timestamp + `prev_hash` (Phase 8) |
| Audit persistence | NOT IMPLEMENTED | Phase 8 — in-memory only; lost on restart |

## Dashboard

| Component | Status | File:Line | Evidence |
|---|---|---|---|
| `GET /api/dashboard/stats` | VERIFIED | `dashboard_routes.py:8-33` | Aggregates fixture constants (Phase 8) |
| KPI counts | HARDCODED | `fixtures.py` | `finding_count` is hand-written, not computed (Phase 3) |

## Frontend (3 pages, 25 components)

| Component | Status | Evidence |
|---|---|---|
| Dashboard page (`/`) | VERIFIED | `page.tsx` — renders KpiStrip, PipelineStrip, PriorityQueue, CaseTable (Phase 23) |
| Cases list page (`/cases`) | VERIFIED | `cases/page.tsx` — CaseTable with filter state (Phase 23) |
| Case detail page (`/cases/{id}`) | VERIFIED | `cases/[id]/page.tsx` — full panel set (Phase 23) |
| CaseTable (filter/sort) | VERIFIED | `CaseTable.tsx:73-87` — priority/evidence/approval filters (Phase 8) |
| ApprovalControls | VERIFIED | `ApprovalControls.tsx:73-95` — double-click approve, modal reject/override (Phase 8) |
| DuplicateClusterPanel | MOCK | `DuplicateClusterPanel.tsx:26-28` — renders `finding_count` constant (Phase 5) |
| 16 remaining components | VERIFIED | Shared/layout/panels — render from data objects (Phase 23) |
| `mockProvider.ts` | MOCK | Pre-built `ANALYSES` + `seedAuditLog()` (Phase 3) |
| `realProvider.ts` | VERIFIED | Graceful fallback to mock on error (Phase 23) |

## Test Suites

| Suite | Status | Tests | Evidence |
|---|---|---|---|
| Backend injection (`test_injection.py`) | MOCK-ONLY | 13 | Tests MockProvider only; 10 payloads pass (Phase 15) |
| Backend hallucination (`test_hallucination.py`) | MOCK-ONLY | 3 | Validator + MockProvider; CVE/number grounding (Phase 15) |
| Frontend injection (`injection-ui.test.tsx`) | VERIFIED | 8 | React rendering safety; no XSS (Phase 15) |
| Route tests | NOT IMPLEMENTED | 0 | No automated API tests (Phase 15) |
| E2E tests | NOT IMPLEMENTED | 0 | No end-to-end tests (Phase 15) |
| Deployment tests | NOT IMPLEMENTED | 0 | No Docker/startup tests (Phase 12) |
