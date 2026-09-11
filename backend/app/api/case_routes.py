import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.mock.fixtures import CASES
from backend.app.cases.models import TriageCase, AuditEvent

router = APIRouter()

_cases_store: dict[str, dict] = {c["case_id"]: c for c in CASES}
_audit_store: dict[str, list[dict]] = {}


def _ensure_audit(case_id: str) -> list[dict]:
    if case_id not in _audit_store:
        _audit_store[case_id] = []
    return _audit_store[case_id]


@router.get("")
async def list_cases(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    cases = list(_cases_store.values())
    if priority:
        cases = [c for c in cases if c["priority"]["level"] == priority.upper()]
    if status:
        cases = [c for c in cases if c["approval"]["status"] == status.upper()]
    return cases


@router.get("/{case_id}")
async def get_case(case_id: str):
    case = _cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case["audit"] = _ensure_audit(case_id)
    return case
