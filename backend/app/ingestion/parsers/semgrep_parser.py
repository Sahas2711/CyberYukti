"""Parser for Semgrep SAST vulnerability scan reports (JSON and SARIF formats)."""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from backend.app.ingestion.models import CanonicalFinding, ScanType


class SemgrepParser:
    """Ingests and normalizes Semgrep SAST JSON/SARIF scan outputs."""

    # Route mapping dictionary for controller/handler files to HTTP routes
    PATH_ROUTE_MAP = {
        "handlers/static.py": "/api/static/download",
        "controllers/static.py": "/api/static/download",
        "views/static.py": "/api/static/download",
        "routes/static.py": "/api/static/download",
        "handlers/download.py": "/api/static/download",
        "admin/auth.py": "/api/admin/auth",
        "controllers/admin.py": "/api/admin/auth",
        "views/auth.py": "/api/admin/auth",
    }

    @staticmethod
    def parse_file(file_path: str, default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses a Semgrep scan report JSON/SARIF file into a list of CanonicalFindings."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SemgrepParser.parse_dict(data, default_asset=default_asset)

    @staticmethod
    def parse_dict(data: Dict[str, Any], default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses in-memory Semgrep dictionary (native JSON or SARIF)."""
        findings: List[CanonicalFinding] = []
        target_asset = default_asset or "cyberyukti-repo"

        # SARIF detection
        if "runs" in data:
            return SemgrepParser._parse_sarif(data, target_asset)

        # Standard Semgrep JSON
        results = data.get("results", [])
        for idx, result in enumerate(results, start=1):
            check_id = result.get("check_id", "semgrep-unknown-rule")
            path = result.get("path", "unknown/path")
            start = result.get("start", {})
            line = start.get("line") or (result.get("extra", {}).get("lines"))
            if isinstance(line, str) and line.isdigit():
                line = int(line)
            elif not isinstance(line, int):
                line = 1

            extra = result.get("extra", {})
            message = extra.get("message", "Semgrep SAST rule violation")
            raw_sev = (extra.get("severity") or "WARNING").upper()

            # Map Semgrep severities: ERROR -> HIGH, WARNING -> MEDIUM, INFO -> LOW
            sev_map = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
            severity = sev_map.get(raw_sev, raw_sev)

            metadata = extra.get("metadata", {})

            # Extract CWE IDs
            raw_cwes = metadata.get("cwe", [])
            if isinstance(raw_cwes, str):
                raw_cwes = [raw_cwes]
            cwe_ids: List[str] = []
            for c in raw_cwes:
                match = re.search(r"CWE-\d+", str(c), re.IGNORECASE)
                if match:
                    cwe_ids.append(match.group(0).upper())

            # Also check if check_id or message contains CWE
            if not cwe_ids:
                for src in [check_id, message]:
                    match = re.search(r"CWE-\d+", src, re.IGNORECASE)
                    if match:
                        cwe_ids.append(match.group(0).upper())

            # Extract CVE if available in metadata
            cve_id: Optional[str] = None
            raw_cves = metadata.get("cve", [])
            if isinstance(raw_cves, str):
                raw_cves = [raw_cves]
            for c in raw_cves:
                match = re.search(r"CVE-\d{4}-\d+", str(c), re.IGNORECASE)
                if match:
                    cve_id = match.group(0).upper()
                    break

            # Route resolution: metadata.route or route pattern map
            http_endpoint = metadata.get("route")
            if not http_endpoint:
                norm_path = path.replace("\\", "/").strip("./")
                for map_path, mapped_route in SemgrepParser.PATH_ROUTE_MAP.items():
                    if norm_path.endswith(map_path) or map_path in norm_path:
                        http_endpoint = mapped_route
                        break

            # Infer HTTP method if applicable
            http_method = "GET" if http_endpoint else None

            hash_input = f"semgrep:{target_asset}:{path}:{check_id}:{line}:{idx}"
            finding_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

            canonical = CanonicalFinding(
                finding_id=finding_id,
                tool_name="semgrep",
                scan_type=ScanType.SAST,
                title=check_id,
                description=message,
                cve_id=cve_id,
                cwe_ids=sorted(list(set(cwe_ids))),
                raw_severity=severity,
                target_asset=target_asset,
                file_path=path.replace("\\", "/"),
                line_number=line,
                http_endpoint=http_endpoint,
                http_method=http_method,
                package_name=None,
                installed_version=None,
                fixed_version=None,
                raw_payload=result,
            )
            findings.append(canonical)

        return findings

    @staticmethod
    def _parse_sarif(data: Dict[str, Any], target_asset: str) -> List[CanonicalFinding]:
        """Fallback parser for SARIF outputs produced by Semgrep."""
        findings: List[CanonicalFinding] = []
        runs = data.get("runs", [])
        idx = 0
        for run in runs:
            results = run.get("results", [])
            for res in results:
                idx += 1
                rule_id = res.get("ruleId", "sarif-rule")
                msg = res.get("message", {}).get("text", "SARIF SAST rule finding")
                locations = res.get("locations", [])
                path = "unknown"
                line = 1
                if locations:
                    phys = locations[0].get("physicalLocation", {})
                    path = phys.get("artifactLocation", {}).get("uri", "unknown")
                    line = phys.get("region", {}).get("startLine", 1)

                # Extract CWE
                cwe_match = re.search(r"CWE-\d+", rule_id + " " + msg, re.IGNORECASE)
                cwes = [cwe_match.group(0).upper()] if cwe_match else []

                hash_input = f"semgrep_sarif:{target_asset}:{path}:{rule_id}:{line}:{idx}"
                finding_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

                http_endpoint = None
                norm_path = path.replace("\\", "/").strip("./")
                for map_path, mapped_route in SemgrepParser.PATH_ROUTE_MAP.items():
                    if norm_path.endswith(map_path) or map_path in norm_path:
                        http_endpoint = mapped_route
                        break

                findings.append(
                    CanonicalFinding(
                        finding_id=finding_id,
                        tool_name="semgrep",
                        scan_type=ScanType.SAST,
                        title=rule_id,
                        description=msg,
                        cve_id=None,
                        cwe_ids=cwes,
                        raw_severity="HIGH",
                        target_asset=target_asset,
                        file_path=path.replace("\\", "/"),
                        line_number=line,
                        http_endpoint=http_endpoint,
                        http_method="GET" if http_endpoint else None,
                        raw_payload=res,
                    )
                )
        return findings
