"""CyberYukti Backend API Service — unified app.

Combines:
- Person 1: finding ingestion + 3-tier dedup (POST /api/v1/scan/demo-ingest, GET /api/v1/clusters)
- Person 4: triage cases, AI analysis, approvals, audit, dashboard stats

All routes operate on a single shared store seeded from fixtures and
enriched with real ingestion + risk-engine output.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.ingestion.normalizer import FindingIntelligenceEngine
from backend.app.ingestion.models import IncidentCluster, IngestionSummary
from backend.app.store import init_store, get_pipeline_meta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

app = FastAPI(
    title="CyberYukti API",
    description="Autonomous Vulnerability Triage & Evidence Engine (PS16)",
    version="2.0.0",
)

# CORS: explicit origins (fixes person1's wildcard + credentials combo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    init_store()


@app.get("/")
def read_root():
    """Health check and service status."""
    meta = get_pipeline_meta()
    return {
        "app": "CyberYukti",
        "status": "online",
        "version": "2.0.0",
        "pipeline_source": meta.get("source"),
        "docs_url": "/docs",
    }


# ---------------------------------------------------------------------------
# Ingestion (Person 1)
# ---------------------------------------------------------------------------

engine = FindingIntelligenceEngine()


@app.get("/api/v1/clusters", response_model=List[IncidentCluster])
def get_ingestion_clusters():
    """Deduplicated clusters from the ingestion engine (real dedup output)."""
    from backend.app.store import get_clusters

    clusters = get_clusters()
    if not clusters:
        raise HTTPException(
            status_code=404,
            detail="No clusters yet. Run POST /api/v1/scan/demo-ingest first.",
        )
    return clusters


@app.get("/api/v1/report")
def get_full_report() -> Dict[str, Any]:
    """Summary metrics and the full cluster list from ingestion."""
    from backend.app.store import get_clusters, get_pipeline_meta

    meta = get_pipeline_meta()
    clusters = get_clusters()
    if not clusters:
        raise HTTPException(
            status_code=404,
            detail="No report yet. Run POST /api/v1/scan/demo-ingest first.",
        )
    return {"summary": meta.get("summary"), "clusters": clusters}


@app.post("/api/v1/scan/demo-ingest")
def run_demo_ingest():
    """Runs ingestion + 3-tier dedup over the bundled scanner fixtures."""
    fixtures = [
        BASE_DIR / "backend" / "fixtures" / "raw_scans" / "trivy_scan.json",
        BASE_DIR / "backend" / "fixtures" / "raw_scans" / "semgrep_scan.json",
        BASE_DIR / "backend" / "fixtures" / "raw_scans" / "nuclei_scan.json",
    ]
    for fpath in fixtures:
        if not fpath.exists():
            raise HTTPException(status_code=404, detail=f"Fixture file missing: {fpath}")

    clusters, summary = engine.process_raw_files([str(f) for f in fixtures])

    output_dir = BASE_DIR / "backend" / "fixtures" / "mock_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "verified_clusters.json"
    export_data = {
        "summary": summary.model_dump(),
        "clusters": [c.model_dump() for c in clusters],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    return export_data


# ---------------------------------------------------------------------------
# Case / triage API (Person 4, backed by the shared store)
# ---------------------------------------------------------------------------

from backend.app.api.case_routes import router as case_router  # noqa: E402
from backend.app.api.approval_routes import router as approval_router  # noqa: E402
from backend.app.api.ai_routes import router as ai_router  # noqa: E402
from backend.app.api.audit_routes import router as audit_router  # noqa: E402
from backend.app.api.dashboard_routes import router as dashboard_router  # noqa: E402

app.include_router(case_router, prefix="/api/cases", tags=["cases"])
app.include_router(approval_router, prefix="/api/cases", tags=["approvals"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(audit_router, prefix="/api/cases", tags=["audit"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
