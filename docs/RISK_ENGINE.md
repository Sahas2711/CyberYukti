# CyberYukti — Risk Engine

**Status:** NOT IMPLEMENTED. All 6 priority scores are fixture constants; no formula, no computation function, no versioned implementation exists despite `formula_version="1.0.0"` being set.

## The model
- `PriorityResult` (`backend/app/cases/models.py:53-58`): cluster_id, score, level, factors, formula_version.
- `TriageCase.priority` embeds it (`models.py:106`).

## The data — HARDCODED CONSTANTS (`fixtures.py`)
| Case | score | level | File:Line |
|---|---|---|---|
| CASE-001 | 92.5 | P1 | `fixtures.py:96-98` |
| CASE-002 | 45.2 | P2 | `fixtures.py:148-150` |
| CASE-003 | 61.8 | P3 | `fixtures.py:193-195` |
| CASE-004 | 28.5 | P4 | `fixtures.py:246-248` |
| CASE-005 | 68.9 | P2 | `fixtures.py:299-301` |
| CASE-006 | 97.3 | P1 | `fixtures.py:344-346` |
- Each `factors` dict is a literal (`fixtures.py:99-106`, per case) — no function consumes it, no formula derives the score above it.
- `formula_version="1.0.0"` is a literal string in every case (e.g. `fixtures.py:107,160,205,258,311,356`). No formula code, version gate, or threshold doc exists (master doc Phase 7).
- Override mutates `level` only: `approval_routes.py:128` sets `case["priority"]["level"] = new_priority`; `score` is NOT recomputed. Live probe: CASE-005 P2→P1 kept score 68.9 (master doc Phase 3).
- Frontend contract rule (Person-4 spec): "Do NOT recompute the score in the frontend" (`prompts.txt:776`).

## 14 Phase-7 audit questions — all NO / NONE
1. Does any function compute `score` from `factors`? **NO** — score is a literal; grep for a scoring function → 0 hits.
2. Does `compute_priority(factors) -> PriorityResult` exist? **NO** — no such function in codebase.
3. Does override recompute the score? **NO** — mutates `level` only (`approval_routes.py:128`).
4. Can "what formula produces 92.5?" be answered? **NO** — unreproducible (master doc Phase 7).
5. Are P1–P4 threshold boundaries defined anywhere? **NONE** — only literal `level="P1"` etc. (`fixtures.py:98`).
6. Are factor weights / contributions defined? **NONE** — `factors` dict has no weights (`fixtures.py:99-106`).
7. Is `formula_version` bound to code? **NO** — free-floating literal `"1.0.0"` (`fixtures.py:107`).
8. Is there re-scoring when evidence changes? **NO** — evidence is fixture data with no change path.
9. Is there a risk-engine unit test? **NONE** — suite covers mock AI + UI only (master doc Phase 15).
10. Does any endpoint trigger scoring? **NO** — no `POST /api/score/{cluster_id}` (master doc Phase 10).
11. Is scoring part of an ingestion pipeline? **NO** — no ingestion exists (master doc Phase 5).
12. Does a scoring action write an audit event? **NO** — only approve/reject/override write events (`approval_routes.py:64,95,130-133`).
13. Does AI compute or justify a fresh priority? **NO** — mock provider re-reads fixture `score`/`level` verbatim (`mock_provider.py:32-34`).
14. Is `score` clamped/validated anywhere? **NO** — passes through unvalidated; no bounds check.

## What must exist (Person 3 scope — all absent)
1. `compute_priority(factors: dict) -> PriorityResult` — deterministic score function (master doc Phase 7).
2. EPSS enrichment — live `https://api.first.org/data/v1/epss` query.
3. CISA KEV lookup.
4. Documented thresholds + versioned formula; override must recompute `score`, not just re-label `level`.

## Consistency (system-wide)
- PS16 completion 1.5/11 = 13.6%; "severity reasoning" and "prioritization" are NOT IMPLEMENTED (master doc Phase 21). DO NOT MERGE with 8 blockers. One branch exists: `person4`.