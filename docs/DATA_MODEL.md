# CyberYukti — Data Model

**Status:** 10 Pydantic models across 2 files; 2 models UNUSED (`Finding`, `Cluster`). One duplicate model (`AIAnalysis` in `models.py` and `ai/schemas.py`). See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phase 9.

## `backend/app/cases/models.py` (109 lines)

| Model (line) | Purpose | Fields (mandatory; `?` = Optional) | Producer | Consumer | Classification |
|---|---|---|---|---|---|
| `Asset` :5-10 | Asset being assessed | `asset_id, hostname, environment, internet_exposed, criticality` | HARDCODED fixtures (`fixtures.py:13-59`) | nested in `TriageCase`, `Finding` | HARDCODED |
| `Finding` :13-24 | Raw scanner finding (canonical) | `finding_id, cluster_id, scanner, scanner_rule_id?, cve?, cwe?, title, description?, asset, raw_evidence?, observed_at` | **None — never instantiated** | None | UNUSED |
| `Cluster` :27-32 | Dedup group of findings | `cluster_id, finding_ids: list[str], primary_finding_id, dedup_confidence: float, dedup_method` | **None — never instantiated** | None | UNUSED |
| `EvidenceObservation` :35-41 | Single validation probe result | `observation_id, type, target, observed_value, expected_value?, method` | HARDCODED fixtures (`fixtures.py:74-90`, `:127-142`) | nested in `ValidationResult` | HARDCODED |
| `ValidationResult` :44-50 | Evidence-validation outcome | `cluster_id, status, confidence: float, observations: list[EvidenceObservation], validated_at, validator_version` | HARDCODED fixtures (`fixtures.py:69-93`) — status/confidence are constants | `TriageCase.evidence`, `types.ts:18-25` | HARDCODED |
| `PriorityResult` :53-58 | Priority score + rationale | `cluster_id, score: float, level, factors: dict, formula_version` | HARDCODED fixtures (`fixtures.py:96-108`) — no formula computes `score` | `TriageCase.priority`, `types.ts:27-40` | HARDCODED |
| `AIAnalysis` :61-72 | LLM explanation output | `summary, why_it_matters, evidence_summary, priority_explanation, investigation_questions: list[str], recommended_remediation: list[str], confidence_notes: list[str], limitations: list[str], model, generated_at, grounded_on: list[str]` | AI engine (`engine.py:45-104`); mock (`mock_provider.py:16-132`) | `TriageCase.ai_analysis`, `types.ts:42-54` | REAL (mock provider) |
| `ApprovalState` :75-80 | Human decision state | `status`("PENDING" default), `decided_by?, decided_at?, override_priority?, reason?` | Approval routes (`approval_routes.py:56-62,87-93,120-126`) | `TriageCase.approval`, `types.ts:56-62` | REAL |
| `AuditEvent` :83-93 | Immutable audit record | `event_id, case_id, timestamp, actor, actor_id?, action, previous_state?, new_state?, metadata?, prev_hash?` | `_add_audit_event` (`approval_routes.py:18-36`); mock `seedAuditLog()` (`mockProvider.ts:224-303`) | `audit_routes.py:8-12` → `types.ts:64-75` | PARTIAL (in-memory) |
| `TriageCase` :96-109 | Aggregate case shown to analyst | `case_id, cluster_id, title, asset, sources: list[str], finding_count: int, vulnerability: dict, evidence: ValidationResult, threat_intelligence: dict, priority: PriorityResult, ai_analysis?: AIAnalysis, approval: ApprovalState() default, audit: list[AuditEvent]` | HARDCODED fixtures (`fixtures.py:61-361`) | all API routes + `types.ts:77-91` | HARDCODED |

## Duplicate `AIAnalysis` — `backend/app/ai/schemas.py:4-15`
- Identical 11 fields, byte-for-byte equivalent to `models.py:61-72`.
- Producer/consumer split: `engine.py:11` and `validator.py:6` import from `.schemas`; `TriageCase` and routes use `models.py` (`models.py:107`, `case_routes.py:8`). Safe only because both sides serialize via `model_dump()` (master doc Phase 9; branches_docs.md §6).
- Maintenance risk: a field added to one copy silently diverges from the other; no shared schema generation or import of one from the other.

## Field-level conventions
- **Untyped dicts (backend):** `factors` (`models.py:57`), `vulnerability` (`:103`), `threat_intelligence` (`:105`), `previous_state`/`new_state`/`metadata` (`:90-92`). All pass-through; frontend constrains them (`types.ts:31-38,84-86`). Non-blocking.
- **Defaults:** `ApprovalState.status="PENDING"` is a mutable `BaseModel` default good practice (fresh instance per case, `fixtures.py:110`); `TriageCase.approval=ApprovalState()` and `audit=[]` at `models.py:108-109`.
- **`prev_hash`** is `Optional[str]` and stores the *previous event_id*, not a hash (`approval_routes.py:22`) — naming misleading (master doc Phase 26 §4).
- `Finding`/`Cluster` Optional-typing (`?`) anticipates scanner gaps (no CVE, no rule id) — schema is ingestion-ready (master doc Phase 5).

## Type-schema conventions
- All case data flows as JSON dicts: fixtures export via `model_dump()` (`fixtures.py:363-370`); routes re-serialize dicts. Pydantic classes are construct-time only; no `response_model=` declared on routes (branches_docs.md §12).
- Mutations bypass Pydantic entirely: `approval_routes.py` assigns raw dicts to `case["approval"]` (`:56-62`) and `case["priority"]["level"]` (`:128`); `ai_routes.py:19` assigns the `model_dump()` dict. Field-level drift is therefore unchecked at runtime.

## Model lifecycle summary (construction timeline)
```
Assets (fixtures.py:13-59)              # construct-time only
  └→ TriageCase (fixtures.py:61-361)    # references Asset, ValidationResult, PriorityResult
      └→ CASES: list[dict] (fixtures.py:363-370)   # model_dump() → JSON forever after
```
- After `model_dump()`, no Pydantic object ever wraps case data again except AI output: `analyze_case()` returns `AIAnalysis` (`engine.py:45`) and `validate_analysis()` parses into `AIAnalysis` (`validator.py:162-166`).
- `ApprovalState`/`AuditEvent` are constructed **only as plain dicts** on the wire (`approval_routes.py:23-35`, `:56-62`) — their Pydantic classes (`models.py:75-93`) are never instantiated at runtime; they exist for type documentation + frontend parity.

## UNUSED models (dead code, master doc Phases 5, 19)
- `Finding` (`models.py:13-24`) — imported at `fixtures.py:4`, no constructor call anywhere.
- `Cluster` (`models.py:27-32`) — imported at `fixtures.py:5`, never instantiated.
- Migration path: these belong to Person 1's scope (master doc Phase 26 §11); do not delete before Person 1 ingests — or let Person 1 own them.