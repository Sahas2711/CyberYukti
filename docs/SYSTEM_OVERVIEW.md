# CyberYukti — System Overview

**Status:** PS16 completion 1.5/11 (13.6%). A SOC analyst workbench operating on pre-built fixtures; the autonomous triage pipeline (ingest → normalize → dedup → validate → score → case) does NOT exist. Verdict: DO NOT MERGE (8 merge blockers). See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phases 21, 25.

## What the system is
- FastAPI (Python) backend + Next.js 14/React 18 frontend implementing **Person 4's slice** of the PS16 "Autonomous Vulnerability Triage & Evidence Engine": AI explanation, approval workflow, audit trail, SOC dashboard (master doc Phases 2, 8).
- Only substantive branch: `person4` (5 commits). `main` is empty — 0 commits (master doc Phase 1; `branches_docs.md` §1). No Person 1/2/3 branches exist.

## What it does today (VERIFIED — live HTTP probes, master doc Phase 3/4)
- Serves 9 endpoints: 6 case/approval/audit/ai/dashboard routes + `/health` (`main.py:21-30`).

  | # | Case | Priority | Sources | finding_count | Evidence |
  |---|---|---|---|---|---|
  | CASE-001 | SQL Injection | P1 92.5 | nuclei, semgrep, burp | 3 | CONFIRMED |
  | CASE-002 | Outdated jQuery | P2 45.2 | npm-audit, snyk | 2 | NOT_CONFIRMED |
  | CASE-003 | XSS | P3 61.8 | nuclei, semgrep, acunetix | 3 | CONFIRMED |
  | CASE-004 | Open Redirect | P4 28.5 | nuclei | 1 | INCONCLUSIVE |
  | CASE-005 | Insecure Deserialization | P2 68.9 | burp, semgrep | 2 | NOT_CONFIRMED |
  | CASE-006 | RCE/Image Resize | P1 97.3 | nuclei, acunetix | 2 | CONFIRMED |

- Approve/reject/override with real guard logic (400/404/409) and audit-event creation (`approval_routes.py:39-134`).
- AI analysis via deterministic `MockProvider` (`mock_provider.py:16-132`) with sanitizer + grounding validator (`sanitizer.py:47-63`, `validator.py:63-108`, `140-171`).
- Injection-safe React rendering (no `dangerouslySetInnerHTML`), 18 tests (10 backend mock + 8 frontend). All pass — master doc Phase 15.
- Dashboard stats aggregated from fixture data at request time (`dashboard_routes.py:8-33`).

## What is MOCK / HARDCODED (master doc Phase 3, 20)
- All 6 cases are hardcoded `TriageCase` constructor calls (`fixtures.py:61-361`).
- `priority.score` (92.5/45.2/61.8/28.5/68.9/97.3), `evidence.status`, and `finding_count` are **HARDCODED CONSTANTS**, not computed (fixtures.py per-case; `finding_count` at `fixtures.py:67,120,173,218,271,324`).
- Frontend `ANALYSES` are MOCK template strings (`mockProvider.ts:142-208`); `seedAuditLog()` fabricates a clustered→validated→prioritized→analysis lifecycle (`mockProvider.ts:224-303`).

## What is missing (Persons 1/2/3 — NOT IMPLEMENTED)
- **Person 1 — Ingestion/Normalization/Dedup:** no `POST /api/findings`; `Finding`, `Cluster` models never instantiated (`models.py:13-32`). No scanner input path (master doc Phase 5).
- **Person 2 — Evidence validation/sandbox:** zero subprocess/Docker/probe code (grep 0 hits); `ValidationResult` is fixture data only (master doc Phase 6).
- **Person 3 — Risk scoring/threat intel:** no scoring formula; `formula_version="1.0.0"` set but no formula exists; no EPSS/KEV enrichment (master doc Phase 7).

## Other gaps
- No persistence (in-memory dicts; audit + decisions lost on restart) — master doc Phase 4.
- No Docker/Dockerfile/docker-compose/Makefile (glob: 0 hits) — master doc Phase 12.
- No auth, no rate limiting, 500 detail leaks `str(e)` (`ai_routes.py:21-22`, LOW) — master doc Phase 13.

## Bottom line
- A fresh machine can run it manually (backend from repo root, two terminals) — but it cannot accept, validate, dedup, or score a real finding. Demo is fixture-only walkthrough (master doc Phases 16-17).