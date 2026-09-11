from fastapi import APIRouter

from backend.app.mock.fixtures import CASES

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    cases = CASES
    total_findings = sum(c["finding_count"] for c in cases)
    unique_clusters = len(cases)

    confirmed = sum(1 for c in cases if c["evidence"]["status"] == "CONFIRMED")
    not_confirmed = sum(1 for c in cases if c["evidence"]["status"] == "NOT_CONFIRMED")
    inconclusive = sum(1 for c in cases if c["evidence"]["status"] == "INCONCLUSIVE")

    p1 = sum(1 for c in cases if c["priority"]["level"] == "P1")
    p2 = sum(1 for c in cases if c["priority"]["level"] == "P2")
    p3 = sum(1 for c in cases if c["priority"]["level"] == "P3")
    p4 = sum(1 for c in cases if c["priority"]["level"] == "P4")

    return {
        "total_findings": total_findings,
        "unique_clusters": unique_clusters,
        "confirmed": confirmed,
        "not_confirmed": not_confirmed,
        "inconclusive": inconclusive,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
    }
