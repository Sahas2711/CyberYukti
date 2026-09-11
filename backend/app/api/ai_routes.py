from fastapi import APIRouter, HTTPException

from backend.app.mock.fixtures import CASES
from backend.app.ai.engine import analyze_case

router = APIRouter()

_cases_store: dict[str, dict] = {c["case_id"]: c for c in CASES}


@router.post("/analyze/{case_id}")
async def analyze(case_id: str):
    case = _cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        analysis = await analyze_case(case)
        case["ai_analysis"] = analysis.model_dump()
        return analysis.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
