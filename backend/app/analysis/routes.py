"""Analysis API routes for GitHub + DockerHub security analysis."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.app.analysis.models import (
    AnalysisCreateRequest,
    AnalysisCreateResponse,
    AnalysisStatusResponse,
    AnalysisLogsResponse,
    AnalysisFindingsResponse,
    AnalysisClustersResponse,
    AnalysisReportResponse,
)
from backend.app.analysis.service import analysis_service

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisCreateResponse)
async def create_analysis(request: AnalysisCreateRequest):
    """Create a new GitHub + DockerHub security analysis."""
    try:
        metadata = await analysis_service.create_analysis(
            github_url=str(request.github_url) if request.github_url else None,
            dockerhub_image=request.dockerhub_image,
            authorization=request.authorization,
        )
        return AnalysisCreateResponse(
            analysis_id=metadata.analysis_id,
            status=metadata.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """Get analysis status and progress."""
    metadata = await analysis_service.get_analysis(analysis_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Build progress info
    progress = {}
    if metadata.github:
        progress["github_acquisition"] = metadata.github.status.value if hasattr(metadata.github, 'status') else "completed"
    if metadata.semgrep:
        progress["semgrep"] = metadata.semgrep.status.value
    if metadata.docker:
        progress["docker_pull"] = "completed" if metadata.docker.exit_code == 0 else "failed"
    if metadata.trivy:
        progress["trivy"] = metadata.trivy.status.value
    if metadata.pipeline:
        # A pipeline object present but not yet finished (no end_time) is still running
        progress["pipeline"] = "completed" if metadata.pipeline.end_time else "running"

    return AnalysisStatusResponse(
        analysis_id=metadata.analysis_id,
        status=metadata.status,
        github_url=str(metadata.github_url) if metadata.github_url else None,
        dockerhub_image=metadata.dockerhub_image,
        progress=progress,
        started_at=metadata.started_at,
        completed_at=metadata.completed_at,
        duration_seconds=metadata.duration_seconds,
        error=metadata.error,
        partial_results=metadata.partial_results,
    )


@router.get("/{analysis_id}/logs", response_model=AnalysisLogsResponse)
async def get_analysis_logs(analysis_id: str):
    """Get detailed execution logs for an analysis."""
    logs = await analysis_service.get_analysis_logs(analysis_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisLogsResponse(**logs)


@router.get("/{analysis_id}/findings", response_model=AnalysisFindingsResponse)
async def get_analysis_findings(analysis_id: str):
    """Get normalized findings for an analysis."""
    findings = await analysis_service.get_analysis_findings(analysis_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Analysis not found or findings not available")
    return AnalysisFindingsResponse(**findings)


@router.get("/{analysis_id}/clusters", response_model=AnalysisClustersResponse)
async def get_analysis_clusters(analysis_id: str):
    """Get incident clusters for an analysis."""
    clusters = await analysis_service.get_analysis_clusters(analysis_id)
    if clusters is None:
        raise HTTPException(status_code=404, detail="Analysis not found or clusters not available")
    return AnalysisClustersResponse(**clusters)


@router.get("/{analysis_id}/report", response_model=AnalysisReportResponse)
async def get_analysis_report(analysis_id: str):
    """Get complete analysis report."""
    report = await analysis_service.get_analysis_report(analysis_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisReportResponse(**report)


@router.get("", response_model=list)
async def list_analyses(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List analyses (metadata only)."""
    # This would need a persistent store - for now return empty
    # In a real implementation, this would query a database
    return []


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis and its artifacts."""
    # This would need a persistent store - for now just return success
    # In a real implementation, this would delete from database and filesystem
    return {"message": "Analysis deleted", "analysis_id": analysis_id}