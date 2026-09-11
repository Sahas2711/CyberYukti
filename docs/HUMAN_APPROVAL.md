# CyberYukti — Human Approval Workflow

**Status:** IMPLEMENTED (in-memory). Approve/reject/override with live-verified guards (400/404/409) — but zero persistence and no authentication; `analyst_id` is trusted verbatim.

## Routes (`backend/app/api/approval_routes.py`)
- **Approve** `POST /api/cases/{id}/approve` (`approval_routes.py:39-65`):
  - 404 case-missing (`:42-43`); 400 missing `analyst_id` (`:49-50`); 409 already decided (`:53-54`, blocks re-approve).
  - Success: `approval.status=APPROVED` with `decided_by`/`decided_at`/`reason` (`:56-62`); audit event written (`:64`). `reason` is optional here.
- **Reject** `POST /api/cases/{id}/reject` (`:68-96`):
  - 404 (`:71-72`); 400 missing `analyst_id` (`:78-79`) or `reason` (`:80-81`); 409 not PENDING/OVERRIDDEN (`:84-85`).
  - Success: `status=REJECTED` (`:87-93`); audit event (`:95`).
- **Override** `POST /api/cases/{id}/override` (`:99-134`):
  - 404 (`:102-103`); 400 missing `analyst_id` (`:110-111`), `override_priority` outside P1–P4 (`:112-113`), or missing `reason` (`:114-115`).
  - **No 409 branch** — no status gate exists (`:117` flows straight into mutation); override is permitted after any prior state.
  - Success: `status=OVERRIDDEN` (`:120-126`); **mutates `priority.level` in place** (`:128` — `score` never recomputed); audit metadata `old_priority`/`new_priority`/`reason` (`:130-133`).

## State-transition matrix (from guard code)
| From state | approve | reject | override |
|---|---|---|---|
| PENDING | OK | OK | OK |
| REJECTED | OK (`:53`) | 409 (`:84`) | OK |
| OVERRIDDEN | OK (`:53`) | OK (`:84`) | OK |
| APPROVED | 409 (`:53`) | 409 (`:84`) | OK (no gate) |

## Verified (master doc Phase 3/10)
- Live probes: missing `analyst_id` → 400; double-approve → 409; override CASE-005 P2→P1 → 200 with audit event and dashboard P1 count 2→3.

## Frontend UX (`frontend/components/case/ApprovalControls.tsx`, master doc Phase 23; flow at `ApprovalControls.tsx:73-95`)
- **Approve:** double-click confirm pattern — two-step guard against accidental clicks.
- **Reject:** modal with required reason.
- **Override:** modal with P1–P4 selector + required reason; transition diagram shown.
- Buttons disabled once a decision exists; case re-fetched after each action (`realProvider.ts:24-31`).
- Frontend mock mirrors the flow but hardcodes `analyst_id="analyst-1"` (`mockProvider.ts:368-395`).

## Limitations (must be stated)
- **No persistence** — decisions live in in-memory `_cases_store`/`_audit_store` (`case_routes.py:12-13`); server restart reverts everything (master doc Phase 4, 26 §4).
- **No authentication** — `analyst_id` taken verbatim from the request body (`approval_routes.py:46,76,106`); any caller can impersonate any analyst (master doc Phase 13, INFO).
- **No rate limiting** on decision endpoints (master doc Phase 10).
- `reason` is unvalidated free text (presence-checked only for reject/override); inert via React text escaping (master doc Phase 13).
- No multi-person approval, no first-approval notification, no decision timeouts.

## PS16 traceability
- "Human approval": **SATISFIED** — the only fully satisfied requirement, part of the 1.5/11 (13.6%) completion (master doc Phase 21). PS16 verdict DO NOT MERGE (8 blockers) refers to the system as a whole, not this feature.