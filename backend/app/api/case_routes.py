from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.store import (
    get_case,
    get_cases,
    get_clusters,
    ensure_audit,
)

router = APIRouter()


@router.get("")
async def list_cases(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    cases = get_cases()
    if priority:
        cases = [c for c in cases if c["priority"]["level"] == priority.upper()]
    if status:
        cases = [c for c in cases if c["approval"]["status"] == status.upper()]
    return cases


@router.get("/clusters/all")
async def list_clusters():
    """Deduplicated clusters produced by the real ingestion engine."""
    return get_clusters()


@router.get("/{case_id}")
async def get_case_route(case_id: str):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case["audit"] = ensure_audit(case_id)
    return case
