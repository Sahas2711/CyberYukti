"""Analysis models for GitHub + DockerHub security analysis pipeline."""

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    GITHUB_CLONE = "github_clone"
    SEMGREP_SCAN = "semgrep_scan"
    DOCKER_PULL = "docker_pull"
    TRIVY_SCAN = "trivy_scan"
    NORMALIZING = "normalizing"
    DEDUPLICATING = "deduplicating"
    CORRELATING = "correlating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ScannerStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GitHubRepoInfo(BaseModel):
    url: HttpUrl
    owner: str
    name: str
    full_name: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    default_branch: Optional[str] = None
    size_kb: Optional[int] = None


class DockerImageInfo(BaseModel):
    image_ref: str
    repository: str
    tag: str = "latest"
    digest: Optional[str] = None
    size_bytes: Optional[int] = None
    architecture: Optional[str] = None
    os: Optional[str] = None


class ScannerExecution(BaseModel):
    scanner: str
    version: Optional[str] = None
    status: ScannerStatus = ScannerStatus.PENDING
    command: List[str] = []
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    raw_output_path: Optional[str] = None
    findings_count: int = 0
    error: Optional[str] = None


class GitHubAcquisition(BaseModel):
    clone_command: List[str] = []
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    repository: Optional[GitHubRepoInfo] = None
    error: Optional[str] = None


class DockerAcquisition(BaseModel):
    pull_command: List[str] = []
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    image: Optional[DockerImageInfo] = None
    error: Optional[str] = None


class PipelineProcessing(BaseModel):
    canonical_findings_count: int = 0
    exact_duplicates_removed: int = 0
    triple_tuple_duplicates_removed: int = 0
    cross_tool_correlations: int = 0
    incident_clusters_created: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class AnalysisArtifacts(BaseModel):
    metadata_path: Optional[str] = None
    github_acquisition_path: Optional[str] = None
    semgrep_stdout_path: Optional[str] = None
    semgrep_stderr_path: Optional[str] = None
    semgrep_raw_path: Optional[str] = None
    docker_pull_path: Optional[str] = None
    trivy_stdout_path: Optional[str] = None
    trivy_stderr_path: Optional[str] = None
    trivy_raw_path: Optional[str] = None
    canonical_findings_path: Optional[str] = None
    deduplication_path: Optional[str] = None
    correlations_path: Optional[str] = None
    incident_clusters_path: Optional[str] = None
    analysis_summary_path: Optional[str] = None
    final_report_path: Optional[str] = None


class AnalysisMetadata(BaseModel):
    analysis_id: str
    status: AnalysisStatus = AnalysisStatus.QUEUED
    github_url: Optional[HttpUrl] = None
    dockerhub_image: Optional[str] = None
    authorization: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    github: Optional[GitHubAcquisition] = None
    docker: Optional[DockerAcquisition] = None
    semgrep: Optional[ScannerExecution] = None
    trivy: Optional[ScannerExecution] = None
    pipeline: Optional[PipelineProcessing] = None
    artifacts: Optional[AnalysisArtifacts] = None
    error: Optional[str] = None
    partial_results: bool = False


class AnalysisCreateRequest(BaseModel):
    github_url: Optional[HttpUrl] = None
    dockerhub_image: Optional[str] = None
    authorization: bool = False

    @field_validator("github_url")
    def validate_github_url(cls, v):
        if v is not None:
            url_str = str(v)
            if not (url_str.startswith("https://github.com/") or url_str.startswith("http://github.com/")):
                raise ValueError("GitHub URL must be a valid github.com repository URL")
            parts = url_str.rstrip("/").split("/")
            if len(parts) < 5 or parts[2] != "github.com":
                raise ValueError("GitHub URL must be in format https://github.com/owner/repository")
        return v

    @field_validator("dockerhub_image")
    def validate_dockerhub_image(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("DockerHub image cannot be empty")
            # Support formats: owner/image, owner/image:tag, https://hub.docker.com/r/owner/image
            if v.startswith("https://hub.docker.com/"):
                parts = v.rstrip("/").split("/")
                if len(parts) < 6 or parts[2] != "hub.docker.com" or parts[3] != "r":
                    raise ValueError("DockerHub URL must be in format https://hub.docker.com/r/owner/image")
            elif "/" not in v:
                raise ValueError("DockerHub image must be in format owner/image or owner/image:tag")
        return v

    @field_validator("authorization")
    def validate_authorization(cls, v):
        if not v:
            raise ValueError("Authorization is required to start analysis")
        return v


class AnalysisCreateResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    github_url: Optional[str] = None
    dockerhub_image: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    partial_results: bool = False


class AnalysisLogsResponse(BaseModel):
    analysis_id: str
    github_acquisition: Optional[GitHubAcquisition] = None
    semgrep: Optional[ScannerExecution] = None
    docker_pull: Optional[DockerAcquisition] = None
    trivy: Optional[ScannerExecution] = None
    pipeline: Optional[PipelineProcessing] = None


class CanonicalFindingResponse(BaseModel):
    finding_id: str
    tool_name: str
    scan_type: str
    title: str
    description: str
    cve_id: Optional[str] = None
    cwe_ids: List[str] = []
    raw_severity: str
    target_asset: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    http_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    package_name: Optional[str] = None
    installed_version: Optional[str] = None
    fixed_version: Optional[str] = None


class AnalysisFindingsResponse(BaseModel):
    analysis_id: str
    total_findings: int
    semgrep_findings: int
    trivy_findings: int
    findings: List[CanonicalFindingResponse]


class AnalysisClustersResponse(BaseModel):
    analysis_id: str
    total_clusters: int
    clusters: List[Dict[str, Any]]


class AnalysisReportResponse(BaseModel):
    analysis_id: str
    metadata: AnalysisMetadata
    summary: Dict[str, Any]
    scanner_summary: Dict[str, Any]
    finding_summary: Dict[str, Any]
    deduplication_summary: Dict[str, Any]
    correlation_summary: Dict[str, Any]
    incident_clusters: List[Dict[str, Any]]


def create_analysis_id() -> str:
    return uuid.uuid4().hex[:12]


def get_analysis_dir(analysis_id: str) -> Path:
    base = Path(__file__).resolve().parent.parent.parent / "analyses"
    base.mkdir(parents=True, exist_ok=True)
    return base / analysis_id