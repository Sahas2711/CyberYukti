# CyberYukti — Mock / Fake / Dummy Audit

Status: HONEST INVENTORY — the git-committed consumer UI is real; every data element feeding it is pre-built; the pipeline does not exist.

The one-line truth (exact statement, authoritative)
> **fixtures != scanner integration; a UI that renders fixture data is a demo, not the pipeline.**

Classification vocabulary: REAL = live executable producing real output; PARTIAL = works but ephemeral/incomplete; MOCK = generated replacement output; HARDCODED = literal constant; SIMULATED = fabricated lifecycle; PLACEHOLDER = schema without behavior; BROKEN = fails requirement; UNUSED = dead code; NOT IMPLEMENTED = absent.

Data element inventory

| Data | Class | File:Line | Reality |
|---|---|---|---|
| CASE_001–CASE_006 | HARDCODED | `fixtures.py:61-361` | 6 `TriageCase(...)` constructor calls with constant args; single source of ALL case data |
| `priority.score` (92.5, 45.2, 61.8, 28.5, 68.9, 97.3) | HARDCODED | fixtures.py priority sections | Literal numbers; no function computes them; `formula_version="1.0.0"` on every case but no formula code exists |
| `evidence.status` (CONFIRMED / NOT_CONFIRMED / INCONCLUSIVE) | HARDCODED | fixtures.py evidence sections | Set at case-creation; no probe ever produced it |
| `evidence.confidence` (incl. CASE-005: backend `0.82` vs frontend `0.90`) | HARDCODED | `fixtures.py:309` vs `mockProvider.ts:106` | Hand-duplicated constant; proof of two copied datasets |
| `finding_count` (3, 2, 3, 1, 2, 2) | HARDCODED | `fixtures.py:67,120,173,218,271,324` | NOT a clustering result — a hand-written attribute; `DuplicateClusterPanel.tsx:26-28` renders it as-is |
| `sources` (["nuclei","semgrep","burp"], etc.) | HARDCODED | fixtures.py per-case | Static strings implying scans that never ran |
| `threat_intelligence` (cvss/epss/kev) | HARDCODED | `fixtures.py:94` | No EPSS/KEV/NVD enrichment; constant dict |
| `ANALYSES` object | MOCK | `mockProvider.ts:142-207` | Pre-built analysis template strings with interpolated case data; model `cyberyukti-ai-v1.0`, hardcoded `generated_at`; NOT LLM output |
| `seedAuditLog()` | MOCK | `mockProvider.ts:224-301` | Fabricates `clustered→evidence validated→priority calculated→analysis generated` lifecycle events at startup from fixture timestamps; states DETECTED/CLUSTERED/VALIDATED/PRIORITIZED are fictional |
| `MockProvider.analyze()` | MOCK | `mock_provider.py:16-132` | String-template builder from case fields via f-strings + `_clean()` regex (`:10-13`); no LLM call; `model="mock-v1"`; deterministic |
| Backend `GET /api/cases`, approve/reject/override/audit/stats | REAL | `case_routes.py`, `approval_routes.py`, etc. | Live-probe verified guard logic (400/404/409) — but operates on HARDCODED input |
| AI `engine.py` fallback chain + sanitizer + validator | REAL | `engine.py:45-104`, `sanitizer.py:40-44`, `validator.py:63-108` | Real orchestration — currently exercised against MockProvider only |
| React SOC workbench UI | REAL | `frontend/app/page.tsx`, `cases/[id]/page.tsx` | Pure data rendering; no hardcoded UI metrics |
| `Finding` model | UNUSED | `models.py:13-24` | Defined, never instantiated anywhere |
| `Cluster` model | UNUSED | `models.py:27-32` | Defined, never instantiated |
| Ingestion endpoint (`POST /api/findings`) | NOT IMPLEMENTED | N/A | No route accepts scanner output in any format |
| Normalization / dedup | NOT IMPLEMENTED | N/A | No code converts scanner output → Finding → Cluster |
| Evidence sandbox / probe execution / subprocess | NOT IMPLEMENTED | N/A | grep `subprocess`/`docker` = 0 hits |
| Risk scoring function | NOT IMPLEMENTED | N/A | No factor→score computation; override mutates level without recomputing score (`approval_routes.py:128`) |
| Persistence | BROKEN | N/A | All stores in-memory; restart wipes everything (Phase 26.4) |
| Audit trail (within session) | PARTIAL | `approval_routes.py:18-36` | Real events, UUID + prev_hash chain — lost on restart |

Consequences
- Backend tests (16) test MockProvider only; hallucination tests validate the validator against a deterministic string-builder, not a real LLM (Phase 15).
- Frontend tests (8) prove injection-safe rendering — of mock data.
- The demo's five PS16 scenarios rate: 1 WORKING (override), 1 PARTIAL (injection defense — ingestion path missing), 3 MOCK (fixture displays) (Phase 17).
- Nothing shown on screen is downstream of a scanner or a computation. Every score, status, count, and analysis pre-dates server start.