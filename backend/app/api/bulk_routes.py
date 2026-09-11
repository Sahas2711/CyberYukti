"""Bulk scan ingestion routes supporting Multi-Format File Upload (JSON, CSV, SARIF),
Remote Report URL fetching, and 10,000-finding Enterprise Benchmark Execution.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from backend.app.ingestion.bulk_processor import (
    fetch_and_parse_remote_url,
    generate_10k_benchmark_findings,
    parse_csv_content,
    parse_json_content,
    run_bulk_pipeline,
)

router = APIRouter()


class RemoteUrlRequest(BaseModel):
    url: str = Field(..., description="HTTP or HTTPS URL to raw scan report")
    default_asset: str = Field("remote-asset", description="Default asset name if not in report")
    sync_store: bool = Field(True, description="Whether to update CyberYukti dashboard store")


class RawContentRequest(BaseModel):
    content: str = Field(..., description="Raw text content of scan report (JSON or CSV)")
    format: Optional[str] = Field(None, description="Format hint: json, csv, or sarif")
    filename: Optional[str] = Field("scan_report.json", description="Source filename")
    default_asset: str = Field("uploaded-target", description="Default asset name")
    sync_store: bool = Field(True, description="Whether to update CyberYukti dashboard store")


@router.post("/benchmark-10k")
def run_benchmark_10k(
    count: int = Query(10000, ge=100, le=25000, description="Number of vulnerabilities to benchmark"),
    sync_store: bool = Query(True, description="Sync results to live CyberYukti dashboard"),
) -> Dict[str, Any]:
    """Generates and processes ~10,000 enterprise-scale vulnerability findings through the full
    CyberYukti pipeline (Normalization, Exact Hash Dedup, GitLab Triple-Tuple Clustering,
    SAST-to-DAST Correlation, and Person 3 Dynamic Risk Scoring).
    
    Returns the exact comprehensive executive and technical report.
    """
    findings = generate_10k_benchmark_findings(total_count=count)
    report = run_bulk_pipeline(
        findings,
        sync_to_store=sync_store,
        pipeline_name=f"Enterprise Stress Benchmark ({count:,} Findings)",
    )
    return report


@router.post("/upload")
async def upload_scan_file(
    file: UploadFile = File(...),
    sync_store: bool = Query(True, description="Sync results to live CyberYukti dashboard"),
    default_asset: str = Query("uploaded-target", description="Default asset name"),
) -> Dict[str, Any]:
    """Uploads a vulnerability report file in JSON, CSV, or SARIF format and processes it
    through the complete triage pipeline.
    """
    filename = (file.filename or "unknown").lower()
    try:
        content_bytes = await file.read()
        text = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        if filename.endswith(".csv") or ("," in text[:500] and "\n" in text[:500] and not text.strip().startswith("{")):
            findings = parse_csv_content(text, default_asset=default_asset)
        else:
            findings = parse_json_content(text, default_asset=default_asset)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error parsing scan file '{filename}': {str(e)}")

    if not findings:
        raise HTTPException(status_code=422, detail="No valid vulnerability findings could be extracted from file.")

    report = run_bulk_pipeline(
        findings,
        sync_to_store=sync_store,
        pipeline_name=f"Uploaded File: {file.filename} ({len(findings):,} Findings)",
    )
    return report


@router.post("/url")
def ingest_remote_url(payload: RemoteUrlRequest) -> Dict[str, Any]:
    """Fetches a remote vulnerability scan report from a web link / URL and processes it."""
    try:
        findings = fetch_and_parse_remote_url(payload.url, default_asset=payload.default_asset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching/parsing remote URL: {str(e)}")

    if not findings:
        raise HTTPException(status_code=422, detail="No valid vulnerability findings found at remote URL.")

    report = run_bulk_pipeline(
        findings,
        sync_to_store=payload.sync_store,
        pipeline_name=f"Remote Link: {payload.url} ({len(findings):,} Findings)",
    )
    return report


@router.post("/raw")
def ingest_raw_content(payload: RawContentRequest) -> Dict[str, Any]:
    """Ingests raw scanner output string (JSON or CSV) directly from browser memory."""
    text = payload.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    fmt = (payload.format or "").lower()
    filename = (payload.filename or "").lower()

    try:
        if fmt == "csv" or filename.endswith(".csv") or ("," in text[:300] and "\n" in text[:300] and not text.startswith("{")):
            findings = parse_csv_content(text, default_asset=payload.default_asset)
        else:
            findings = parse_json_content(text, default_asset=payload.default_asset)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error parsing content: {str(e)}")

    if not findings:
        raise HTTPException(status_code=422, detail="No valid vulnerability findings could be parsed.")

    report = run_bulk_pipeline(
        findings,
        sync_to_store=payload.sync_store,
        pipeline_name=f"Payload: {payload.filename} ({len(findings):,} Findings)",
    )
    return report


@router.get("/samples/{sample_name}")
def get_sample_file(sample_name: str):
    """Downloads sample test files (JSON / CSV)."""
    from pathlib import Path
    from fastapi.responses import FileResponse

    base_samples = Path(__file__).resolve().parent.parent.parent / "fixtures" / "samples"
    file_map = {
        "test-cases.csv": base_samples / "sample_test_scans.csv",
        "test-cases.json": base_samples / "sample_test_scans.json",
        "10k.csv": base_samples / "sample_10000_vulnerabilities.csv",
        "10k.json": base_samples / "sample_10000_vulnerabilities.json",
    }
    target = file_map.get(sample_name)
    if not target or not target.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{sample_name}' not found. Available: {list(file_map.keys())}")

    media_type = "text/csv" if sample_name.endswith(".csv") else "application/json"
    return FileResponse(path=str(target), media_type=media_type, filename=sample_name)

