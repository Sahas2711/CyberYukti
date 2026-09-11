"""Parser for Nuclei DAST vulnerability scan reports (JSON and JSONL formats)."""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from backend.app.ingestion.models import CanonicalFinding, ScanType


class NucleiParser:
    """Ingests and normalizes Nuclei DAST JSON/JSONL scan outputs."""

    @staticmethod
    def parse_file(file_path: str, default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses a Nuclei scan file (JSON array or JSONL) into CanonicalFindings."""
        raw_items: List[Dict[str, Any]] = []
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []

            # Try parsing as standard JSON
            if content.startswith("["):
                try:
                    raw_items = json.loads(content)
                except json.JSONDecodeError:
                    raw_items = []

            # Fallback / try JSONL line-by-line
            if not raw_items:
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            raw_items.append(obj)
                    except json.JSONDecodeError:
                        continue

        return NucleiParser.parse_items(raw_items, default_asset=default_asset)

    @staticmethod
    def parse_items(items: List[Dict[str, Any]], default_asset: Optional[str] = None) -> List[CanonicalFinding]:
        """Parses a list of Nuclei JSON finding dictionaries."""
        findings: List[CanonicalFinding] = []

        for idx, item in enumerate(items, start=1):
            template_id = item.get("template-id") or item.get("templateID") or "unknown-template"
            info = item.get("info", {})
            name = info.get("name") or template_id
            raw_sev = (info.get("severity") or "INFO").upper()
            desc = info.get("description") or f"Nuclei DAST matched template {template_id}"

            # Classification
            classification = info.get("classification", {})
            raw_cves = classification.get("cve-id", [])
            if isinstance(raw_cves, str):
                raw_cves = [raw_cves]

            cve_id: Optional[str] = None
            for c in raw_cves:
                match = re.search(r"CVE-\d{4}-\d+", str(c), re.IGNORECASE)
                if match:
                    cve_id = match.group(0).upper()
                    break

            raw_cwes = classification.get("cwe-id", [])
            if isinstance(raw_cwes, str):
                raw_cwes = [raw_cwes]
            cwe_ids: List[str] = []
            for c in raw_cwes:
                match = re.search(r"CWE-\d+", str(c), re.IGNORECASE)
                if match:
                    cwe_ids.append(match.group(0).upper())

            # Host and URL matching
            host = item.get("host") or ""
            matched_at = item.get("matched-at") or host

            # Parse URL and normalize path
            parsed_url = urlparse(matched_at if "://" in matched_at else f"http://{matched_at}")
            http_endpoint = parsed_url.path or "/"
            
            # Asset determination
            target_asset = default_asset or parsed_url.hostname or host or "cyberyukti-target"

            # Parse HTTP method from request line if present
            http_method = "GET"
            req_str = item.get("request", "")
            if req_str:
                first_line = req_str.splitlines()[0]
                m = re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+", first_line)
                if m:
                    http_method = m.group(1)

            hash_input = f"nuclei:{target_asset}:{template_id}:{http_endpoint}:{http_method}:{idx}"
            finding_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

            canonical = CanonicalFinding(
                finding_id=finding_id,
                tool_name="nuclei",
                scan_type=ScanType.DAST,
                title=name,
                description=desc,
                cve_id=cve_id,
                cwe_ids=sorted(list(set(cwe_ids))),
                raw_severity=raw_sev,
                target_asset=target_asset,
                file_path=None,
                line_number=None,
                http_endpoint=http_endpoint,
                http_method=http_method,
                package_name=None,
                installed_version=None,
                fixed_version=None,
                raw_payload=item,
            )
            findings.append(canonical)

        return findings
