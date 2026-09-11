"""API routes for Cryptographic Proof-of-Triage Attestation."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, Response

from backend.app.store import get_case
from backend.app.attestation import generate_case_attestation, verify_attestation

router = APIRouter()


@router.get("/{case_id}/attestation")
def get_case_attestation(case_id: str) -> Dict[str, Any]:
    """Generates and returns the cryptographic Proof-of-Triage digital receipt for a case."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    receipt = generate_case_attestation(case)
    return receipt


@router.post("/attestation/verify")
async def verify_case_attestation(request: Request) -> Dict[str, Any]:
    """Validates an uploaded or submitted cryptographic attestation receipt.
    
    Checks leaf hashes, reconstructs the Merkle tree, and verifies digital signature.
    """
    try:
        receipt = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(receipt, dict):
        raise HTTPException(status_code=400, detail="Receipt must be a JSON object")

    result = verify_attestation(receipt)
    return result
