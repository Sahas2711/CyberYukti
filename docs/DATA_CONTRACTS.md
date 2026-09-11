# CyberYukti — Data Contracts

**Status:** 10 backend schemas ↔ 10 TypeScript interfaces match field-for-field. 3 non-blocking type mismatches; 1 duplicate `AIAnalysis`; 1 behavioral divergence (audit 404 vs `[]`). See `branches_docs.md` §11; `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phase 9.

## Contract table (schema → producer → consumer)

| Schema | Producer (backend) | Wire format | Consumer (frontend) | Compatible? |
|---|---|---|---|---|
| `Asset` | fixtures `fixtures.py:13-59` | nested in case JSON | `Asset` `types.ts:1-7` | YES — identical |
| `EvidenceObservation` | fixtures `fixtures.py:74-90`/`:127-142` | nested | `EvidenceObservation` `types.ts:9-16` | YES — FE stricter union for `type` |
| `ValidationResult` | fixtures `fixtures.py:69-93` | nested | `ValidationResult` `types.ts:18-25` | YES |
| `PriorityResult` | fixtures `fixtures.py:96-108` | nested | `PriorityResult` `types.ts:27-40` | YES |
| `AIAnalysis` | engine `engine.py:45-104` / mock `mock_provider.py:16-132` | `POST /api/ai/analyze/{id}` body | `AIAnalysis` `types.ts:42-54`; mock `ANALYSES` `mockProvider.ts:142-208` | YES |
| `ApprovalState` | approval routes `approval_routes.py:56-62/87-93/120-126` | `approve/reject/override` response | `ApprovalState` `types.ts:56-62` | YES — FE stricter unions |
| `AuditEvent` | `_add_audit_event` `approval_routes.py:18-36`; mock `seedAuditLog()` `mockProvider.ts:224-303` | `GET /api/cases/{id}/audit` | `AuditEvent` `types.ts:64-75` | YES — FE stricter `actor` union |
| `TriageCase` | fixtures `fixtures.py:61-361` | `GET /api/cases`, `GET /api/cases/{id}` | `TriageCase` `types.ts:77-91` | YES |
| `DashboardStats` | dashboard route `dashboard_routes.py:23-33` | `GET /api/dashboard/stats` | `DashboardStats` `types.ts:93-103` | YES |
| `Finding` / `Cluster` | **no producer** (never instantiated) | — | — (no FE type) | UNUSED |

## Type mismatches (non-blocking, branches_docs.md §11; master doc Phase 9)
- **`vulnerability`:** backend `dict` (`models.py:103`) vs FE `{ cwe?: string; cve?: string }` (`types.ts:84`) — FE stricter; backend passes through.
- **`threat_intelligence`:** backend `dict` (`models.py:105`) vs FE `{ cvss?: number; epss?: number; kev?: boolean }` (`types.ts:86`) — same pattern.
- **Approval response type:** backend returns `ApprovalState`; `realProvider.ts:42,54,66` types it as `TriageCase`. Works because the body is discarded and the case is re-fetched via `getCase()` (`realProvider.ts:24-31`).
- **`PriorityResult.factors`:** backend `dict` (`models.py:57`) vs FE object with optional known keys (`types.ts:31-38`) — FE is a projection, not a superset.

## Operation-level contract traceability (backend response → FE consumption)
| Operation | Backend returns | FE expects | FE consumes body? | Risk |
|---|---|---|---|---|
| `GET /api/cases` | `TriageCase[]` | `TriageCase[]` | yes (table/filters) | none |
| `GET /api/cases/{id}` | `TriageCase` | `TriageCase` | yes (panels) | none |
| `POST /{id}/approve\|reject\|override` | `ApprovalState` | `TriageCase` (typed) | **no** — re-fetch via getCase | low |
| `POST /ai/analyze/{id}` | `AIAnalysis` (dumped) | `AIAnalysis` | yes + re-fetch | none |
| `GET /{id}/audit` | `list[AuditEvent]` | `AuditEvent[]` | yes | 404-vs-[] divergence |
| `GET /dashboard/stats` | `DashboardStats` | `DashboardStats` | yes (KpiStrip etc.) | none |

## Duplicate `AIAnalysis`
- Defined twice, identically: `models.py:61-72` and `schemas.py:4-15`.
- Engine path imports `schemas.py` (`engine.py:11`, `validator.py:6`); route/`TriageCase` path uses `models.py` (`models.py:107`, `case_routes.py:8`). Safe only because `model_dump()` keys match (master doc Phase 9).

## Behavioral divergences
- **Audit 404-vs-`[]` (branches_docs.md §11):** backend `GET /api/cases/{id}/audit` raises 404 when no audit exists (`audit_routes.py:10-11`); frontend mock returns `[]` (`mockProvider.ts:305-308`). In real mode a 404 triggers the realProvider mock fallback (`realProvider.ts:78-84`), silently masking the divergence.
- **CASE-005 confidence:** backend fixture `confidence=0.82` (`fixtures.py:309`) vs frontend mock `confidence=0.90` (`mockProvider.ts:114`) — hand-duplicated data, not machine-generated (branches_docs.md §6).
- **prev_hash:** stores previous `event_id`, not a cryptographic hash (`approval_routes.py:22`, `mockProvider.ts:248`). Field name misleading (master doc Phase 26 §4).

## Contract tests / verification
- No automated contract tests exist. Alignment is verified by inspection + manual HTTP probes only (branches_docs.md §13: "No route/API tests"). 400/404/409 behaviors verified via live probes (master doc Phase 10).
- `next-env.d.ts` is gitignored and schemas are hand-maintained in two languages — no shared schema source exists (branches_docs.md §10); drift risk is why the mismatches above cluster in untyped dict fields.