import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.app.mock.fixtures import CASES
from backend.app.api.case_routes import _cases_store, _audit_store

router = APIRouter()


def _ensure_audit(case_id: str) -> list[dict]:
    if case_id not in _audit_store:
        _audit_store[case_id] = []
    return _audit_store[case_id]


def _add_audit_event(case_id: str, actor: str, actor_id: str | None, action: str,
                     previous_state: dict | None, new_state: dict | None,
                     metadata: dict | None = None) -> dict:
    audit = _ensure_audit(case_id)
    prev_hash = audit[-1]["event_id"] if audit else None
    event = {
        "event_id": str(uuid.uuid4()),
        "case_id": case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "actor_id": actor_id,
        "action": action,
        "previous_state": previous_state,
        "new_state": new_state,
        "metadata": metadata,
        "prev_hash": prev_hash,
    }
    audit.append(event)
    return event


@router.post("/{case_id}/approve")
async def approve_case(case_id: str, request: Request):
    case = _cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    body = await request.json()
    analyst_id = body.get("analyst_id")
    reason = body.get("reason")

    if not analyst_id:
        raise HTTPException(status_code=400, detail="analyst_id is required")

    prev = dict(case["approval"])
    if prev["status"] not in ("PENDING", "REJECTED", "OVERRIDDEN"):
        raise HTTPException(status_code=409, detail="Case already decided")

    case["approval"] = {
        "status": "APPROVED",
        "decided_by": analyst_id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "override_priority": None,
        "reason": reason,
    }

    _add_audit_event(case_id, "analyst", analyst_id, "approve", prev, case["approval"])
    return case["approval"]


@router.post("/{case_id}/reject")
async def reject_case(case_id: str, request: Request):
    case = _cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    body = await request.json()
    analyst_id = body.get("analyst_id")
    reason = body.get("reason")

    if not analyst_id:
        raise HTTPException(status_code=400, detail="analyst_id is required")
    if not reason:
        raise HTTPException(status_code=400, detail="reason is required for reject")

    prev = dict(case["approval"])
    if prev["status"] not in ("PENDING", "OVERRIDDEN"):
        raise HTTPException(status_code=409, detail="Case already decided")

    case["approval"] = {
        "status": "REJECTED",
        "decided_by": analyst_id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "override_priority": None,
        "reason": reason,
    }

    _add_audit_event(case_id, "analyst", analyst_id, "reject", prev, case["approval"])
    return case["approval"]


@router.post("/{case_id}/override")
async def override_case(case_id: str, request: Request):
    case = _cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    body = await request.json()
    analyst_id = body.get("analyst_id")
    new_priority = body.get("override_priority")
    reason = body.get("reason")

    if not analyst_id:
        raise HTTPException(status_code=400, detail="analyst_id is required")
    if not new_priority or new_priority not in ("P1", "P2", "P3", "P4"):
        raise HTTPException(status_code=400, detail="override_priority must be P1, P2, P3, or P4")
    if not reason:
        raise HTTPException(status_code=400, detail="reason is required for override")

    prev = dict(case["approval"])
    old_priority = case["priority"]["level"]

    case["approval"] = {
        "status": "OVERRIDDEN",
        "decided_by": analyst_id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "override_priority": new_priority,
        "reason": reason,
    }

    case["priority"]["level"] = new_priority

    _add_audit_event(
        case_id, "analyst", analyst_id, "override", prev, case["approval"],
        metadata={"old_priority": old_priority, "new_priority": new_priority, "reason": reason},
    )
    return case["approval"]
