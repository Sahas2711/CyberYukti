from fastapi import APIRouter, HTTPException

from backend.app.store import get_case
from backend.app.ai.engine import analyze_case

router = APIRouter()


@router.post("/analyze/{case_id}")
async def analyze(case_id: str):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        analysis = await analyze_case(case)
        case["ai_analysis"] = analysis.model_dump()
        return analysis.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
