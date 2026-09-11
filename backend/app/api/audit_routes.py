from fastapi import APIRouter, HTTPException

from backend.app.api.case_routes import _audit_store

router = APIRouter()


@router.get("/{case_id}/audit")
async def get_audit(case_id: str):
    if case_id not in _audit_store:
        raise HTTPException(status_code=404, detail="Audit trail not found")
    return _audit_store[case_id]
