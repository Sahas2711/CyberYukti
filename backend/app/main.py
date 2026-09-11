"""CyberYukti Backend API Service."""

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.ingestion.normalizer import FindingIntelligenceEngine
from backend.app.ingestion.models import IngestionSummary, IncidentCluster

BASE_DIR = Path(__file__).resolve().parent.parent.parent

app = FastAPI(
    title="CyberYukti API",
    description="Autonomous Vulnerability Triage & Evidence Engine (PS16)",
    version="1.0.0",
)

# Enable CORS for frontend integrations (e.g., React, Vite, Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = FindingIntelligenceEngine()


@app.get("/")
def read_root():
    """Health check and service status."""
    return {
        "app": "CyberYukti",
        "status": "online",
        "role": "Person 1 - Finding Intelligence & Deduplication",
        "docs_url": "/docs",
    }


@app.get("/api/v1/clusters", response_model=List[IncidentCluster])
def get_clusters():
    """Returns the verified deduplicated incident clusters."""
    output_path = BASE_DIR / "backend" / "fixtures" / "mock_output" / "verified_clusters.json"
    if not output_path.exists():
        raise HTTPException(
            status_code=404, detail="Clusters not found. Run ingestion first via /api/v1/scan/demo-ingest"
        )

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Return clusters list
    return data.get("clusters", [])


@app.get("/api/v1/report")
def get_full_report() -> Dict[str, Any]:
    """Returns both summary metrics and the full cluster list."""
    output_path = BASE_DIR / "backend" / "fixtures" / "mock_output" / "verified_clusters.json"
    if not output_path.exists():
        raise HTTPException(
            status_code=404, detail="Report not found. Run ingestion first via /api/v1/scan/demo-ingest"
        )

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@app.post("/api/v1/scan/demo-ingest")
def run_demo_ingest():
    """Runs ingestion and 3-tier deduplication on demo scanner fixtures."""
    fixtures = [
        str(BASE_DIR / "backend" / "fixtures" / "raw_scans" / "trivy_scan.json"),
        str(BASE_DIR / "backend" / "fixtures" / "raw_scans" / "semgrep_scan.json"),
        str(BASE_DIR / "backend" / "fixtures" / "raw_scans" / "nuclei_scan.json"),
    ]

    for fpath in fixtures:
        if not Path(fpath).exists():
            raise HTTPException(status_code=404, detail=f"Fixture file missing: {fpath}")

    clusters, summary = engine.process_raw_files(fixtures)

    # Persist to mock_output/verified_clusters.json
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

