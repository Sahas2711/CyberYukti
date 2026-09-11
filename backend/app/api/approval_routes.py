from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.app.store import get_case, add_audit_event

router = APIRouter()


def _analyst_decision(analyst_id: str, status: str, reason: str | None,
                     override_priority: str | None = None) -> dict:
    return {
        "status": status,
        "decided_by": analyst_id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "override_priority": override_priority,
        "reason": reason,
    }


@router.post("/{case_id}/approve")
async def approve_case(case_id: str, request: Request):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        body = await request.json()
    except Exception:
        body = {}

    analyst_id = body.get("analyst_id") or "analyst-1"
    reason = body.get("reason") or "Approved by analyst"

    prev = dict(case["approval"])
    if prev["status"] not in ("PENDING", "REJECTED", "OVERRIDDEN"):
        raise HTTPException(status_code=409, detail="Case already decided")

    case["approval"] = _analyst_decision(analyst_id, "APPROVED", reason)
    add_audit_event(case_id, "analyst", analyst_id, "approve", prev, case["approval"])
    return case["approval"]


@router.post("/{case_id}/reject")
async def reject_case(case_id: str, request: Request):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        body = await request.json()
    except Exception:
        body = {}

    analyst_id = body.get("analyst_id") or "analyst-1"
    reason = body.get("reason")

    if not reason:
        raise HTTPException(status_code=400, detail="reason is required for reject")

    prev = dict(case["approval"])
    if prev["status"] not in ("PENDING", "OVERRIDDEN"):
        raise HTTPException(status_code=409, detail="Case already decided")

    case["approval"] = _analyst_decision(analyst_id, "REJECTED", reason)
    add_audit_event(case_id, "analyst", analyst_id, "reject", prev, case["approval"])
    return case["approval"]


@router.post("/{case_id}/override")
async def override_case(case_id: str, request: Request):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        body = await request.json()
    except Exception:
        body = {}

    analyst_id = body.get("analyst_id") or "analyst-1"
    new_priority = body.get("override_priority")
    reason = body.get("reason") or "Priority overridden by analyst"

    if not new_priority or new_priority not in ("P1", "P2", "P3", "P4"):
        raise HTTPException(status_code=400, detail="override_priority must be P1, P2, P3, or P4")

    prev = dict(case["approval"])
    old_priority = case["priority"]["level"]

    case["approval"] = _analyst_decision(analyst_id, "OVERRIDDEN", reason, new_priority)
    case["priority"]["level"] = new_priority

    add_audit_event(
        case_id, "analyst", analyst_id, "override", prev, case["approval"],
        metadata={"old_priority": old_priority, "new_priority": new_priority, "reason": reason},
    )
    return case["approval"]
