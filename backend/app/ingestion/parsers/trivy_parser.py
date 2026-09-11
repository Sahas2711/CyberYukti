"""Parser for Trivy SCA and Container vulnerability scan reports."""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from backend.app.ingestion.models import CanonicalFinding, ScanType


class TrivyParser:
    """Ingests and normalizes Trivy JSON scan outputs."""

    @staticmethod
    def parse_file(file_path: str, default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses a Trivy scan report JSON file into a list of CanonicalFindings."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TrivyParser.parse_dict(data, default_asset=default_asset)

    @staticmethod
    def parse_dict(data: Dict[str, Any], default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses in-memory Trivy JSON dictionary."""
        findings: List[CanonicalFinding] = []

        # ArtifactName or Schema-level target
        artifact_name = data.get("ArtifactName") or default_asset or "default-asset"
        results = data.get("Results", [])

        # If data is a list of results directly
        if isinstance(data, list):
            results = data

        idx = 0
        for result in results:
            target = result.get("Target", "unknown-target")
            result_class = result.get("Class", "")
            result_type = result.get("Type", "").lower()

            # Classify scan type
            if result_class == "os-pkgs" or result_type in ["debian", "alpine", "ubuntu", "redhat", "centos", "amazon"]:
                scan_type = ScanType.CONTAINER
            else:
                scan_type = ScanType.SCA

            vulnerabilities = result.get("Vulnerabilities", []) or []
            for vuln in vulnerabilities:
                idx += 1
                v_id = vuln.get("VulnerabilityID", "UNKNOWN-VULN")
                pkg_name = vuln.get("PkgName", "unknown-pkg")
                installed_ver = vuln.get("InstalledVersion", "unknown")
                fixed_ver = vuln.get("FixedVersion")
                raw_sev = (vuln.get("Severity") or "UNKNOWN").upper()
                title = vuln.get("Title") or f"{v_id} in {pkg_name}"
                desc = vuln.get("Description") or f"Vulnerability {v_id} identified in {pkg_name} {installed_ver}."

                # Normalize CWE IDs
                raw_cwes = vuln.get("CweIDs", []) or []
                cwe_ids: List[str] = []
                for c in raw_cwes:
                    match = re.search(r"CWE-\d+", str(c), re.IGNORECASE)
                    if match:
                        cwe_ids.append(match.group(0).upper())

                cve_id = v_id if v_id.upper().startswith("CVE-") else None

                # Generate deterministic finding_id
                hash_input = f"trivy:{artifact_name}:{target}:{v_id}:{pkg_name}:{installed_ver}:{idx}"
                finding_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

                canonical = CanonicalFinding(
                    finding_id=finding_id,
                    tool_name="trivy",
                    scan_type=scan_type,
                    title=title,
                    description=desc,
                    cve_id=cve_id,
                    cwe_ids=sorted(list(set(cwe_ids))),
                    raw_severity=raw_sev,
                    target_asset=artifact_name,
                    file_path=target,
                    line_number=None,
                    http_endpoint=None,
                    http_method=None,
                    package_name=pkg_name,
                    installed_version=installed_ver,
                    fixed_version=fixed_ver,
                    raw_payload=vuln,
                )
                findings.append(canonical)

        return findings
