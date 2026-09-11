"""Data models and schemas for Evidence Validation Engine.

Defines Pydantic models for Canonical Findings, Evidence Claims,
Validation Results, and Execution Audit trails.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ValidationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    INCONCLUSIVE = "INCONCLUSIVE"


class AssetRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(..., description="Unique lab asset identifier")
    name: Optional[str] = Field(None, description="Human readable asset name")


class VulnerabilityRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(..., description="Vulnerability title or claim")
    cve: Optional[str] = Field(None, description="CVE identifier if applicable")
    cwe: Optional[Union[str, int, None]] = Field(None, description="CWE identifier if applicable")


class LocationRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = Field(..., description="Location type: 'package', 'endpoint', 'port', 'file'")
    package: Optional[str] = Field(None, description="Package name for package checks")
    endpoint: Optional[str] = Field(None, description="Endpoint path or URL")
    path: Optional[str] = Field(None, description="File path or endpoint path")
    port: Optional[Union[int, str]] = Field(None, description="Port number for port checks")


class EvidenceClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claimed_version: Optional[str] = Field(None, description="Claimed package or software version")
    expected_status: Optional[int] = Field(None, description="Expected HTTP status code")
    expected_state: Optional[str] = Field(None, description="Expected port state e.g. OPEN")
    expected_exists: Optional[bool] = Field(None, description="Expected file existence status")


class CanonicalFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    finding_id: str = Field(..., description="Unique finding ID from Person 1")
    cluster_id: Optional[str] = Field(None, description="Cluster or duplicate group ID")
    asset: AssetRef = Field(..., description="Target asset reference")
    vulnerability: VulnerabilityRef = Field(..., description="Claimed vulnerability metadata")
    location: LocationRef = Field(..., description="Vulnerability location information")
    evidence: EvidenceClaim = Field(..., description="Claimed evidence parameters to validate")


class ProbeAudit(BaseModel):
    type: str = Field(..., description="Selected probe identifier")
    version: str = Field(default="1.0", description="Probe version")
    status: str = Field(..., description="Probe run status: PASS, FAIL, ERROR")


class ExecutionAudit(BaseModel):
    sandbox: str = Field(default="docker", description="Execution sandbox environment")
    duration_ms: int = Field(..., description="Validation execution time in milliseconds")


class ValidationResult(BaseModel):
    finding_id: str = Field(..., description="Validated finding ID")
    status: ValidationStatus = Field(..., description="Final validation status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    observed: Dict[str, Any] = Field(default_factory=dict, description="Observed evidence collected")
    probe: ProbeAudit = Field(..., description="Probe audit information")
    execution: ExecutionAudit = Field(..., description="Execution environment and timing")
    reason: List[str] = Field(default_factory=list, description="Audit rationale list")
    validation_id: str = Field(..., description="Unique validation audit identifier")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error classification string")
    detail: Optional[str] = Field(None, description="Sanitized detail explanation")


class InvalidInputException(Exception):
    """Raised when input fails sanitization or contains dangerous patterns."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class SecurityViolationException(Exception):
    """Raised when an unauthorized or malicious action is detected."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
