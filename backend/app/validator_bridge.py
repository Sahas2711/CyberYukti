"""Live Bridge between CyberYukti Backend and Evidence Validation Engine (Person 2).

Converts backend TriageCase objects into canonical findings, executes safe non-destructive
probes (package_version, http_endpoint, port_check, file_check), deterministically evaluates
observed evidence, and updates case evidence and observations.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure services/evidence-engine is in sys.path
SERVICE_PATH = Path(__file__).resolve().parent.parent.parent / "services" / "evidence-engine"
if str(SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(SERVICE_PATH))

import models as ee_models
from validator.evaluator import evaluate
from validator.registry import select_probe_for_finding
from validator.target_registry import resolve_target

# Asset mapping for demo and lab targets
ASSET_ALIAS_MAP: Dict[str, str] = {
    "asset-001": "shop-api-01",
    "asset-002": "shop-api-01-patched",
    "asset-003": "shop-api-01",
    "asset-004": "shop-api-01-patched",
    "asset-005": "shop-api-01",
    "asset-006": "shop-api-01-patched",
}


def resolve_case_asset_id(case: Dict[str, Any], target_override: Optional[str] = None) -> str:
    """Resolve an asset ID for a case against registered lab targets."""
    if target_override:
        return target_override.strip()

    asset = case.get("asset", {})
    hostname = (asset.get("hostname") or "").lower()

    if "shop-api-01-patched" in hostname or "patched" in hostname:
        return "shop-api-01-patched"
    if "shop-api-01" in hostname or "shop-api" in hostname:
        return "shop-api-01"

    raw_asset_id = asset.get("asset_id", "")
    if raw_asset_id in ASSET_ALIAS_MAP:
        return ASSET_ALIAS_MAP[raw_asset_id]

    return raw_asset_id or "shop-api-01"


def map_case_to_canonical_finding(
    case: Dict[str, Any],
    target_override: Optional[str] = None,
) -> ee_models.CanonicalFinding:
    """Map a backend TriageCase dictionary into a CanonicalFinding model."""
    case_id = case.get("case_id", "CASE-001")
    cluster_id = case.get("cluster_id", "CLUSTER-001")
    title = case.get("title", "Vulnerability Finding")
    vuln = case.get("vulnerability", {})

    target_asset_id = resolve_case_asset_id(case, target_override)
    asset_ref = ee_models.AssetRef(id=target_asset_id, name=case.get("asset", {}).get("hostname"))

    # Determine location type and parameters
    loc_type = "package"
    pkg_name = vuln.get("package")
    claimed_ver = vuln.get("version")
    path_val = vuln.get("path")
    endpoint_val = vuln.get("endpoint")
    port_val = vuln.get("port")

    # Check if case already has an existing observation type to guide probe selection
    existing_obs = case.get("evidence", {}).get("observations", [])
    primary_obs_type = existing_obs[0].get("type") if existing_obs and isinstance(existing_obs[0], dict) else None

    lower_title = title.lower()
    if "jquery" in lower_title or "aiohttp" in lower_title or "log4j" in lower_title or primary_obs_type == "package_version":
        loc_type = "package"
        if "jquery" in lower_title:
            pkg_name = "jquery"
            claimed_ver = "1.12.4"
        elif "aiohttp" in lower_title:
            pkg_name = "aiohttp"
            claimed_ver = "3.8.4"
        elif "log4j" in lower_title:
            pkg_name = "log4j"
            claimed_ver = "2.14.0"
        else:
            pkg_name = pkg_name or "example-package"
            claimed_ver = claimed_ver or "1.2.3"
    elif primary_obs_type == "file_exists" or "file" in vuln or "config" in lower_title or "flag" in lower_title or "traversal" in lower_title or "deserialization" in lower_title or "resize" in lower_title:
        loc_type = "file"
        path_val = path_val or "vulnerable_app.conf"
    elif primary_obs_type == "endpoint_status" or "endpoint" in vuln or "login" in lower_title or "http" in lower_title or "api" in lower_title:
        loc_type = "endpoint"
        endpoint_val = endpoint_val or "/api/health"
    elif primary_obs_type == "port_status" or "port" in vuln:
        loc_type = "port"
        port_val = port_val or 8080

    loc_ref = ee_models.LocationRef(
        type=loc_type,
        package=pkg_name,
        path=path_val,
        endpoint=endpoint_val,
        port=port_val,
    )

    evidence_claim = ee_models.EvidenceClaim(
        claimed_version=claimed_ver,
        expected_status=200 if loc_type == "endpoint" else None,
        expected_state="OPEN" if loc_type == "port" else None,
        expected_exists=True if loc_type == "file" else None,
    )

    vuln_ref = ee_models.VulnerabilityRef(
        title=title,
        cve=vuln.get("cve"),
        cwe=vuln.get("cwe"),
    )

    return ee_models.CanonicalFinding(
        finding_id=case_id,
        cluster_id=cluster_id,
        asset=asset_ref,
        vulnerability=vuln_ref,
        location=loc_ref,
        evidence=evidence_claim,
    )


def execute_case_validation(
    case: Dict[str, Any],
    target_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute live validation probe against controlled lab target and return

    updated evidence dictionary matching backend schema.
    """
    finding = map_case_to_canonical_finding(case, target_override)
    target_config = resolve_target(finding.asset.id)

    if not target_config:
        return {
            "cluster_id": case.get("cluster_id", "CLUSTER-001"),
            "status": "INCONCLUSIVE",
            "confidence": 0.10,
            "observations": [
                {
                    "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                    "type": "unregistered_asset",
                    "target": finding.asset.id,
                    "observed_value": "Target asset is not registered in lab allowlist",
                    "expected_value": "Registered controlled lab asset",
                    "method": "target_registry_check",
                }
            ],
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validator_version": "2.1.0",
            "reasons": ["Target asset not in allowlisted lab registry"],
        }

    selected = select_probe_for_finding(finding)
    if not selected:
        return {
            "cluster_id": case.get("cluster_id", "CLUSTER-001"),
            "status": "INCONCLUSIVE",
            "confidence": 0.30,
            "observations": [
                {
                    "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                    "type": "unmapped_probe",
                    "target": finding.location.type,
                    "observed_value": f"No safe probe registered for type '{finding.location.type}'",
                    "expected_value": "Registered probe type",
                    "method": "probe_registry_lookup",
                }
            ],
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validator_version": "2.1.0",
            "reasons": [f"No safe probe registered for location type '{finding.location.type}'"],
        }

    probe_name, probe_func = selected
    exec_status, observed_data, error_detail = probe_func(finding, target_config)

    custom_reasons = [error_detail] if error_detail else []
    val_status, confidence, reasons = evaluate(
        expected=finding.evidence,
        observed=observed_data,
        execution_status=exec_status,
        probe_type=probe_name,
        custom_reasons=custom_reasons,
    )

    # Format observations for backend and frontend schema
    observations = []
    if probe_name == "PACKAGE_VERSION":
        observed_ver = observed_data.get("version") or "Not installed"
        claimed_ver = finding.evidence.claimed_version or "N/A"
        observations.append(
            {
                "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                "type": "package_version",
                "target": f"{finding.asset.id} / {finding.location.package}",
                "observed_value": f"Installed version: {observed_ver}",
                "expected_value": f"Vulnerable claimed version: {claimed_ver}",
                "method": "controlled_manifest_inspection",
            }
        )
    elif probe_name == "HTTP_ENDPOINT":
        obs_code = observed_data.get("status_code", "Unreachable")
        observations.append(
            {
                "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                "type": "endpoint_status",
                "target": f"{finding.asset.id} {finding.location.endpoint or '/'}",
                "observed_value": f"HTTP response: {obs_code}",
                "expected_value": "HTTP 200 OK",
                "method": "safe_get_probe",
            }
        )
    elif probe_name == "FILE_EXISTS":
        exists = observed_data.get("exists", False)
        observations.append(
            {
                "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                "type": "file_exists",
                "target": f"{finding.asset.id}:{finding.location.path}",
                "observed_value": "File exists on target" if exists else "File absent",
                "expected_value": "File exists",
                "method": "path_contained_read",
            }
        )
    elif probe_name == "PORT_CHECK":
        state = observed_data.get("state", "CLOSED")
        observations.append(
            {
                "observation_id": f"obs-{uuid.uuid4().hex[:6]}",
                "type": "port_status",
                "target": f"{finding.asset.id}:{finding.location.port}",
                "observed_value": f"Port state: {state}",
                "expected_value": "Port state: OPEN",
                "method": "safe_tcp_connect",
            }
        )

    return {
        "cluster_id": case.get("cluster_id", "CLUSTER-001"),
        "status": val_status.value,
        "confidence": round(confidence, 2),
        "observations": observations,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "validator_version": "2.1.0",
        "reasons": reasons,
    }
