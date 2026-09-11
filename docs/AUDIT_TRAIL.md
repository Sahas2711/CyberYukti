# CyberYukti — Audit Trail

**Status:** PARTIAL. Audit events are created correctly per decision (uuid, timestamp, actor, chain link) but live only in memory — verified lost on restart — and the backend returns 404 where the frontend mock returns `[]`.

## Schema
- `AuditEvent` (`backend/app/cases/models.py:83-93`): event_id, case_id, timestamp, actor, actor_id, action, previous_state, new_state, metadata, `prev_hash`.
- `prev_hash` is **misleadingly named**: it stores the previous **`event_id`**, not a cryptographic hash (`approval_routes.py:22` → `audit[-1]["event_id"]`). Chain integrity is link-by-ID only; in-memory events can be rewritten without detection (master doc Phase 26 §4).

## Event creation — REAL (three writers)
- approve → `_add_audit_event(case_id, "analyst", analyst_id, "approve", prev, new)` (`approval_routes.py:64`).
- reject → `"reject"` (`approval_routes.py:95`).
- override → `"override"` with metadata `old_priority`/`new_priority`/`reason` (`approval_routes.py:130-133`).
- `_add_audit_event` (`approval_routes.py:18-36`): `uuid.uuid4()` event_id (`:24`), UTC ISO timestamp (`:26`), actor/actor_id (`:27-28`), prev/new state snapshots (`:30-31`), `prev_hash` = prior event_id or None (`:22`).

Example (approve, as built):
| Field | Value |
|---|---|
| event_id | `uuid.uuid4()` hex (`:24`) |
| timestamp | e.g. `2026-09-11T12:34:56.789Z` (`:26`) |
| actor / actor_id | `analyst` / submitted `analyst_id` (`:27-28`) |
| previous_state / new_state | prior vs new `ApprovalState` dict (`:30-31`) |
| prev_hash | previous event's `event_id` or `None` (`:22`) |

## Verified restart loss
- Stores are in-memory dicts only: `_cases_store`/`_audit_store` (`case_routes.py:12-13`), imported by approval/audit routers (`approval_routes.py:7`, `audit_routes.py:3`).
- Master doc Phase 4: audit status **PARTIAL** — "lost on restart". No SQLite/file persistence exists (`INTEGRATION_GAPS.md` GAP 8).
- Reproduced: fresh server after approve+restart → `GET /api/cases/{id}/audit` → 404 (master doc Phase 3).

## Frontend seeded audit log (MOCK — the real backend never reproduces it)
- `seedAuditLog()` (`frontend/lib/api/mockProvider.ts:224-301`) fabricates a 3–4 event lifecycle per case at startup:
  - `clustered` (`:253-261`) → `evidence validated` (`:262-274`) → `priority calculated` (`:275-287`) → `analysis generated` (`:288-298`).
  - Event ids like `seed-CASE-001-1` (`:239`); actor ids `normalizer`/`validator`/`prioritizer`/`cyberyukti-ai-v1.0`.
- The real backend only ever writes `approve`/`reject`/`override` and starts with empty `_audit_store` (`case_routes.py:13`) — the clustered→validated→prioritized pipeline never happened (it does not exist).

## 404-vs-[] divergence
- Backend `GET /api/cases/{id}/audit` → **404** when no events exist (`audit_routes.py:10-11`).
- Frontend mock `getAudit()` → **`[]`** (`mockProvider.ts:305-308`).
- Real mode calls `getAudit()` (`realProvider.ts:78-83`); a real backend 404 triggers the provider's mock fallback, masking emptiness (branches_docs.md §11).

## Integrity assessment
- What the trail proves: a decision occurred, by a claimed actor, at a claimed time, in this process instance.
- What it does NOT prove: durable record (gone on restart), tamper-resistance (no hashes/signatures), or identity (actor is self-asserted).

## Coverage gap
- No automated tests for the audit route or restart behavior — both verified by manual live probes only (master doc Phase 15; `TESTING.md`).