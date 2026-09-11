from fastapi import APIRouter, HTTPException

from backend.app.store import ensure_audit, get_case

router = APIRouter()


@router.get("/{case_id}/audit")
async def get_audit(case_id: str):
    if not get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return ensure_audit(case_id)
