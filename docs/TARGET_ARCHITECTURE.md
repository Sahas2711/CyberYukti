# CyberYukti — Target Architecture

**Status:** PS16 target. NOT IMPLEMENTED beyond stage 8 (AI explanation) and stage 9-10 (approval + partial audit). Completion 1.5/11 (13.6%), 8 merge blockers, DO NOT MERGE. See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phase 22.

## PS16 target pipeline (expected, master doc Phase 22)

```
 Scanners (nuclei / semgrep / burp / npm-audit / snyk ...)   [Person 1 scope]
       │  raw JSON / SARIF / JSONL
       ▼
 Ingestion  POST /api/findings                                [Person 1]  ← missing
       ▼
 Normalization → canonical Finding schema                     [Person 1]  ← missing
       ▼
 Dedup / Correlation → Cluster objects                        [Person 1]  ← missing
       │                                    
       ▼
 Evidence Sandbox (time-boxed probe, isolation)               [Person 2]  ← missing
       ▼
 Threat Intel (EPSS, KEV, CVSS enrichment)                    [Person 3]  ← missing
       ▼
 Risk Scoring → factors → score → P1-P4                       [Person 3]  ← missing
       ▼
 AI Explanation (sanitize → LLM → grounding validate)         [Person 4]  PRESENT (mock)
       ▼
 Analyst Case (TriageCase)                                    [Person 4]  PRESENT (fixtures)
       ▼
 Human Approval / Override                                    [Person 4]  PRESENT
       ▼
 Immutable Audit Trail                                        [Person 4]  PARTIAL (in-memory, lost on restart)
       ▼
 (…Persistence + Docker + E2E harness…)
```

## Current vs Target comparison

| Stage | PS16 required | Current implementation | File evidence | Status |
|---|---|---|---|---|
| Scanner integration | Yes | None — sources are name strings in fixtures | `fixtures.py:66` (CASE-001) | NOT IMPLEMENTED |
| Ingestion endpoint | Yes | None — no `POST /api/findings` | no route (grep) | NOT IMPLEMENTED |
| Normalization | Yes | None — `Finding` defined, never used | `models.py:13-24` | NOT IMPLEMENTED |
| Dedup / clustering | Yes | None — `Cluster` unused; `finding_count` constant | `models.py:27-32`, `fixtures.py:67` | NOT IMPLEMENTED |
| Evidence sandbox | Yes | None — no subprocess; `ValidationResult` is fixture data | `models.py:44-50`, `fixtures.py:69-93` | NOT IMPLEMENTED |
| Threat intel enrichment | Yes | None — static `threat_intelligence` dict | `fixtures.py:94` | NOT IMPLEMENTED |
| Risk scoring | Yes | None — `score`/`level` constants | `fixtures.py:96-108` | NOT IMPLEMENTED |
| AI explanation | Yes | Engine + sanitizer + validator, mock provider | `engine.py:45-104`, `sanitizer.py`, `validator.py` | VERIFIED (mock only) |
| Analyst case | Yes | 6 hardcoded `TriageCase` fixtures | `fixtures.py:61-361` | HARDCODED |
| Human approval | Yes | Approve/reject/override + guards | `approval_routes.py:39-134` | VERIFIED |
| Audit trail | Yes | Events created; lost on restart | `approval_routes.py:18-36` | PARTIAL |
| Persistence | Implicit | In-memory dicts only | `case_routes.py:12-13` | NOT IMPLEMENTED |
| Docker | Expected | No Dockerfile/compose/Makefile | glob: 0 hits | NOT IMPLEMENTED |

## Gap → owner mapping (integration sequence, master doc Phase 24)
1. **Person 1** first: `POST /api/findings` + normalization + dedup → instantiates `Finding`/`Cluster`.
2. Contract alignment: Person 1's schemas must match `models.py:13-32` exactly.
3. **Person 2**: `POST /api/validate/{cluster_id}` + sandbox + probe execution.
4. **Person 3**: `POST /api/score/{cluster_id}` + `compute_priority()` + EPSS/KEV enrichment + `PriorityResult` with evolving formula.
5. Persistence (SQLite/file), then Docker harness, then E2E test, then security hardening.

## Observations
- Only "Human approval" fully satisfies a PS16 requirement; "Auditability" is partial (master doc Phase 21).
- Person 4 code is well-structured and should be **added onto**, not rewritten — the 8 blockers are missing components, not defects (master doc Phase 26 §10).
- Merge verdict: DO NOT MERGE as a PS16-complete solution; recommend making `person4` the default branch as the integration base (`branches_docs.md` §16).