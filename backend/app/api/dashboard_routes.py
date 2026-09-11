from fastapi import APIRouter

from backend.app.store import get_cases, get_pipeline_meta

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    cases = get_cases()
    total_findings = sum(c.get("finding_count", 1) for c in cases)
    unique_clusters = len(cases)

    confirmed = sum(1 for c in cases if (c.get("evidence") or {}).get("status") == "CONFIRMED")
    not_confirmed = sum(1 for c in cases if (c.get("evidence") or {}).get("status") == "NOT_CONFIRMED")
    inconclusive = sum(1 for c in cases if (c.get("evidence") or {}).get("status") == "INCONCLUSIVE")

    p1 = sum(1 for c in cases if (c.get("priority") or {}).get("level") == "P1")
    p2 = sum(1 for c in cases if (c.get("priority") or {}).get("level") == "P2")
    p3 = sum(1 for c in cases if (c.get("priority") or {}).get("level") == "P3")
    p4 = sum(1 for c in cases if (c.get("priority") or {}).get("level") == "P4")

    # Financial Liability Cost Burn metrics
    daily_liability_burn = sum(
        float((c.get("cost_burn") or {}).get("daily_burn", 0.0))
        for c in cases
        if (c.get("approval") or {}).get("status") != "RESOLVED"
    )
    accrued_liability = sum(
        float((c.get("cost_burn") or {}).get("accrued_burn", 0.0))
        for c in cases
        if (c.get("approval") or {}).get("status") != "RESOLVED"
    )

    stats = {
        "total_findings": total_findings,
        "unique_clusters": unique_clusters,
        "confirmed": confirmed,
        "not_confirmed": not_confirmed,
        "inconclusive": inconclusive,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
        "liability_burn": {
            "daily_burn": round(daily_liability_burn, 2),
            "accrued_liability": round(accrued_liability, 2),
            "formatted_daily": f"${daily_liability_burn:,.0f}/day",
            "formatted_accrued": f"${accrued_liability:,.0f}",
        },
    }
    meta = get_pipeline_meta()
    if meta.get("summary"):
        stats["ingestion"] = meta["summary"]
    return stats
