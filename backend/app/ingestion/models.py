"""Canonical Data Models for Finding Intelligence and Ingestion Engine (CyberYukti Person 1)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScanType(str, Enum):
    """Supported vulnerability scan types across heterogeneous tools."""
    SAST = "sast"
    SCA = "sca"
    DAST = "dast"
    CONTAINER = "container"


class CanonicalFinding(BaseModel):
    """Normalized finding representation across Trivy, Semgrep, and Nuclei."""
    finding_id: str = Field(..., description="Unique deterministic identifier for the finding")
    tool_name: str = Field(..., description="Source scanner name: trivy, semgrep, or nuclei")
    scan_type: ScanType = Field(..., description="Scan category (sast, sca, dast, container)")
    title: str = Field(..., description="Human-readable title or rule summary")
    description: str = Field(..., description="Detailed description or message")
    cve_id: Optional[str] = Field(None, description="CVE identifier (e.g. CVE-2023-38606)")
    cwe_ids: List[str] = Field(default_factory=list, description="Associated CWE identifiers (e.g. ['CWE-22'])")
    raw_severity: str = Field(..., description="Scanner severity: CRITICAL, HIGH, MEDIUM, LOW, INFO")
    target_asset: str = Field(..., description="Target repository, container image tag, or host domain")
    file_path: Optional[str] = Field(None, description="Relative code path or lockfile path")
    line_number: Optional[int] = Field(None, description="Source code line number if applicable")
    http_endpoint: Optional[str] = Field(None, description="Normalized HTTP route or URI path")
    http_method: Optional[str] = Field(None, description="HTTP request method (GET, POST, etc.)")
    package_name: Optional[str] = Field(None, description="Software package or library name")
    installed_version: Optional[str] = Field(None, description="Installed component version")
    fixed_version: Optional[str] = Field(None, description="Remediation target version")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Original raw scanner finding snippet")


class IncidentCluster(BaseModel):
    """Actionable vulnerability incident cluster collapsed by deduplication & correlation."""
    cluster_id: str = Field(..., description="Unique cluster identifier, e.g. CLUST-001")
    title: str = Field(..., description="Consolidated incident title")
    primary_cve: Optional[str] = Field(None, description="Primary CVE ID for the cluster")
    root_cause_cwe: Optional[str] = Field(None, description="Dominant root cause CWE ID")
    target_asset: str = Field(..., description="Target asset affected")
    affected_component: str = Field(..., description="Normalized package name, controller, or route")
    normalized_route: Optional[str] = Field(None, description="Associated HTTP endpoint or API route if correlated")
    raw_findings_count: int = Field(..., description="Number of raw scanner findings collapsed into this cluster")
    participating_tools: List[str] = Field(..., description="Tools that detected this vulnerability cluster")
    underlying_finding_ids: List[str] = Field(..., description="List of raw canonical finding IDs in this cluster")
    representative_finding: CanonicalFinding = Field(..., description="Highest-fidelity representative finding")


class IngestionSummary(BaseModel):
    """Aggregate metrics and noise reduction statistics from scan processing."""
    total_raw_findings: int = Field(..., description="Total raw findings ingested across all scanners")
    total_clusters: int = Field(..., description="Actionable incident clusters created")
    noise_reduction_percentage: float = Field(..., description="Noise reduction percentage: (1 - clusters/raw) * 100")
    breakdown_by_tool: Dict[str, int] = Field(default_factory=dict, description="Raw finding counts grouped by scanner")
