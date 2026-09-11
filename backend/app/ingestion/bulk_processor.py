"""Bulk scanner ingestion, multi-format parser (JSON, CSV, SARIF), remote URL fetcher,
and 10,000-finding enterprise benchmark engine for CyberYukti (Person 1 + Person 3).
"""

from collections import defaultdict
import csv
import io
import json
import os
import random
import re
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from backend.app.ingestion.models import (
    CanonicalFinding,
    IncidentCluster,
    IngestionSummary,
    ScanType,
)
from backend.app.ingestion.deduplicator import DeduplicationEngine
from services.risk_engine.scoring import calculate_risk_score
from services.risk_engine.models import AssetContext, FindingInput, ValidationResult


# ---------------------------------------------------------------------------
# Multi-Format Parsers (JSON, CSV, SARIF, Remote URL)
# ---------------------------------------------------------------------------

def parse_csv_content(csv_text: str, default_asset: str = "cyberyukti-target") -> List[CanonicalFinding]:
    """Parses standard CSV vulnerability reports into CanonicalFinding models."""
    findings: List[CanonicalFinding] = []
    reader = csv.DictReader(io.StringIO(csv_text))

    for idx, row in enumerate(reader):
        row_lower = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}

        # Resolve Title
        title = (
            row_lower.get("title")
            or row_lower.get("vulnerability")
            or row_lower.get("name")
            or row_lower.get("issue")
            or f"Vulnerability #{idx + 1}"
        )

        # Resolve Severity
        raw_sev = (
            row_lower.get("severity")
            or row_lower.get("risk")
            or row_lower.get("raw_severity")
            or "MEDIUM"
        ).upper()
        if raw_sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            raw_sev = "MEDIUM"

        # Resolve Tool / Scan Type
        tool = (
            row_lower.get("tool")
            or row_lower.get("scanner")
            or row_lower.get("tool_name")
            or "csv-importer"
        ).lower()

        scan_type_str = (row_lower.get("scan_type") or row_lower.get("type") or "").lower()
        if "sast" in scan_type_str or "semgrep" in tool:
            scan_type = ScanType.SAST
        elif "dast" in scan_type_str or "nuclei" in tool:
            scan_type = ScanType.DAST
        elif "container" in scan_type_str:
            scan_type = ScanType.CONTAINER
        else:
            scan_type = ScanType.SCA

        # Resolve Asset
        asset = (
            row_lower.get("asset")
            or row_lower.get("target")
            or row_lower.get("host")
            or row_lower.get("target_asset")
            or default_asset
        )

        # Resolve CVE / CWE
        cve = row_lower.get("cve") or row_lower.get("cve_id") or row_lower.get("cve-id")
        if cve and not cve.upper().startswith("CVE-"):
            cve = None
        elif cve:
            cve = cve.upper()

        cwe_raw = row_lower.get("cwe") or row_lower.get("cwe_id") or ""
        cwes: List[str] = []
        if cwe_raw:
            found = re.findall(r"CWE-\d+", cwe_raw, re.IGNORECASE)
            cwes = [c.upper() for c in found]

        # Resolve Location (File / Line / Endpoint)
        raw_path = row_lower.get("file") or row_lower.get("file_path") or row_lower.get("path")
        line_str = row_lower.get("line") or row_lower.get("line_number")
        line_number = int(line_str) if line_str and line_str.isdigit() else None

        endpoint = row_lower.get("endpoint") or row_lower.get("http_endpoint") or row_lower.get("url")
        file_path = raw_path

        if not endpoint and raw_path and (raw_path.startswith("/") or raw_path.startswith("http") or tool == "nuclei"):
            endpoint = raw_path
            file_path = None

        method = row_lower.get("method") or row_lower.get("http_method") or "GET"

        package = row_lower.get("package") or row_lower.get("package_name") or row_lower.get("component")
        installed_ver = row_lower.get("installed_version") or row_lower.get("version")
        fixed_ver = row_lower.get("fixed_version") or row_lower.get("fix")

        desc = (
            row_lower.get("description")
            or row_lower.get("details")
            or row_lower.get("summary")
            or f"{title} on {asset}"
        )

        fid = f"csv-{tool}-{idx + 1:05d}"

        findings.append(
            CanonicalFinding(
                finding_id=fid,
                tool_name=tool,
                scan_type=scan_type,
                title=title,
                description=desc,
                cve_id=cve,
                cwe_ids=cwes,
                raw_severity=raw_sev,
                target_asset=asset,
                file_path=file_path or None,
                line_number=line_number,
                http_endpoint=endpoint or None,
                http_method=method if endpoint else None,
                package_name=package or None,
                installed_version=installed_ver or None,
                fixed_version=fixed_ver or None,
                raw_payload={"csv_row": row},
            )
        )

    return findings


def parse_json_content(json_text: str, default_asset: str = "cyberyukti-target") -> List[CanonicalFinding]:
    """Parses various JSON scan formats: Trivy, Semgrep/SARIF, Nuclei NDJSON/array, or Generic list."""
    findings: List[CanonicalFinding] = []

    # Handle NDJSON (Newline Delimited JSON, often output by Nuclei)
    trimmed = json_text.strip()
    if "\n" in trimmed and not trimmed.startswith("[") and not trimmed.startswith("{"):
        lines = [line.strip() for line in trimmed.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    f = _parse_single_finding_dict(obj, idx, default_asset)
                    if f:
                        findings.append(f)
            except Exception:
                continue
        if findings:
            return findings

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content: {str(e)}")

    # 1. SARIF format (runs -> results)
    if isinstance(data, dict) and "runs" in data:
        from backend.app.ingestion.parsers.semgrep_parser import SemgrepParser
        parser = SemgrepParser()
        return parser.parse_sarif_data(data, default_asset=default_asset)

    # 2. Trivy format (Results or SchemaVersion)
    if isinstance(data, dict) and ("Results" in data or "ArtifactName" in data):
        from backend.app.ingestion.parsers.trivy_parser import TrivyParser
        parser = TrivyParser()
        return parser.parse_data(data, default_asset=default_asset)

    # 3. Semgrep JSON (results array)
    if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
        from backend.app.ingestion.parsers.semgrep_parser import SemgrepParser
        parser = SemgrepParser()
        return parser.parse_data(data, default_asset=default_asset)

    # 4. Nuclei JSON array
    if isinstance(data, list) and data and isinstance(data[0], dict) and "template-id" in data[0]:
        from backend.app.ingestion.parsers.nuclei_parser import NucleiParser
        parser = NucleiParser()
        return parser.parse_data(data, default_asset=default_asset)

    # 5. Generic vulnerability dictionary with list: {"findings": [...]}, {"vulnerabilities": [...]}, etc.
    vuln_list = None
    if isinstance(data, dict):
        for k in ("findings", "vulnerabilities", "items", "alerts", "issues", "records"):
            if k in data and isinstance(data[k], list):
                vuln_list = data[k]
                break
    elif isinstance(data, list):
        vuln_list = data

    if vuln_list is not None:
        for idx, item in enumerate(vuln_list):
            if isinstance(item, dict):
                f = _parse_single_finding_dict(item, idx, default_asset)
                if f:
                    findings.append(f)
        return findings

    raise ValueError("Unrecognized JSON scan schema. Please upload Trivy, Semgrep, Nuclei, SARIF, or generic vulnerability array.")


def _parse_single_finding_dict(item: Dict[str, Any], idx: int, default_asset: str) -> Optional[CanonicalFinding]:
    """Helper to convert an arbitrary vulnerability dictionary into a CanonicalFinding."""
    item_lower = {k.lower(): v for k, v in item.items()}

    title = (
        item_lower.get("title")
        or item_lower.get("name")
        or item_lower.get("vulnerability")
        or item_lower.get("check_id")
        or item_lower.get("template-id")
        or f"Finding #{idx + 1}"
    )

    sev = str(
        item_lower.get("severity")
        or item_lower.get("raw_severity")
        or item_lower.get("risk")
        or "MEDIUM"
    ).upper()
    if sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        sev = "MEDIUM"

    tool = str(item_lower.get("tool") or item_lower.get("tool_name") or item_lower.get("scanner") or "scanner").lower()
    asset = str(item_lower.get("asset") or item_lower.get("target_asset") or item_lower.get("target") or default_asset)

    cve = item_lower.get("cve") or item_lower.get("cve_id") or item_lower.get("vulnerabilityid")
    if cve and isinstance(cve, str) and cve.upper().startswith("CVE-"):
        cve = cve.upper()
    else:
        cve = None

    cwes: List[str] = []
    cwe_val = item_lower.get("cwe") or item_lower.get("cwe_id") or item_lower.get("cwe_ids")
    if isinstance(cwe_val, list):
        cwes = [str(c).upper() for c in cwe_val if "CWE" in str(c).upper()]
    elif isinstance(cwe_val, str):
        cwes = [c.upper() for c in re.findall(r"CWE-\d+", cwe_val, re.IGNORECASE)]

    file_path = item_lower.get("file_path") or item_lower.get("file") or item_lower.get("path")
    line = item_lower.get("line_number") or item_lower.get("line")
    line_number = int(line) if line and str(line).isdigit() else None

    endpoint = item_lower.get("http_endpoint") or item_lower.get("endpoint") or item_lower.get("url")
    method = item_lower.get("http_method") or item_lower.get("method") or "GET"

    pkg = item_lower.get("package_name") or item_lower.get("pkgname") or item_lower.get("package")
    inst_v = item_lower.get("installed_version") or item_lower.get("installedversion") or item_lower.get("version")
    fix_v = item_lower.get("fixed_version") or item_lower.get("fixedversion")

    scan_type = ScanType.SCA
    if "sast" in tool or file_path and line_number:
        scan_type = ScanType.SAST
    elif "nuclei" in tool or endpoint:
        scan_type = ScanType.DAST
    elif "container" in tool or "trivy" in tool:
        scan_type = ScanType.CONTAINER

    return CanonicalFinding(
        finding_id=f"{tool}-{idx + 1:05d}",
        tool_name=tool,
        scan_type=scan_type,
        title=str(title),
        description=str(item_lower.get("description") or f"{title} detected on {asset}"),
        cve_id=cve,
        cwe_ids=cwes,
        raw_severity=sev,
        target_asset=asset,
        file_path=str(file_path) if file_path else None,
        line_number=line_number,
        http_endpoint=str(endpoint) if endpoint else None,
        http_method=str(method) if endpoint else None,
        package_name=str(pkg) if pkg else None,
        installed_version=str(inst_v) if inst_v else None,
        fixed_version=str(fix_v) if fix_v else None,
        raw_payload=item,
    )


def fetch_and_parse_remote_url(url: str, default_asset: str = "cyberyukti-remote") -> List[CanonicalFinding]:
    """Fetches a remote scanner report from a URL (HTTP/HTTPS) and parses it."""
    if not url.startswith("http://") and not url.startswith("https://"):
        raise ValueError("URL must start with http:// or https://")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CyberYukti-Ingestion-Engine/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            content_bytes = response.read(15 * 1024 * 1024)  # Limit 15MB
            text = content_bytes.decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to fetch remote scan report from {url}: {e.reason}")
    except Exception as e:
        raise ValueError(f"Error fetching URL {url}: {str(e)}")

    # Try JSON first
    trimmed = text.strip()
    if trimmed.startswith("{") or trimmed.startswith("["):
        return parse_json_content(text, default_asset=default_asset)
    # Try CSV
    if "," in trimmed and "\n" in trimmed:
        return parse_csv_content(text, default_asset=default_asset)

    # Fallback to JSON Lines
    return parse_json_content(text, default_asset=default_asset)


# ---------------------------------------------------------------------------
# 10,000-Finding Enterprise Benchmark Generator
# ---------------------------------------------------------------------------

ENTERPRISE_ASSETS = [
    "auth-service-prod:latest",
    "payment-gateway-api:v2.4",
    "customer-portal-frontend:v1.9",
    "k8s-ingress-controller:v1.10",
    "checkout-service-worker:v3.1",
    "notification-dispatch:v2.0",
    "analytics-reporting-engine:v1.5",
    "db-cluster-proxy:v1.2",
    "session-store-cache:latest",
    "identity-provider-iam:v4.0",
    "order-fulfillment-hub:v2.2",
    "inventory-sync-service:v1.8",
]

ENTERPRISE_VULN_TEMPLATES = [
    {
        "title": "Remote Code Execution via Apache Log4j JNDI Lookup",
        "cve": "CVE-2021-44228",
        "cwe": ["CWE-502", "CWE-20"],
        "severity": "CRITICAL",
        "package": "org.apache.logging.log4j:log4j-core",
        "file": "pom.xml",
        "route": "/api/v1/auth/session",
        "component": "log4j-core",
        "tools": ["trivy", "semgrep", "nuclei"],
    },
    {
        "title": "Spring Framework RCE via Data Binding (Spring4Shell)",
        "cve": "CVE-2022-22965",
        "cwe": ["CWE-94", "CWE-20"],
        "severity": "CRITICAL",
        "package": "org.springframework:spring-beans",
        "file": "build.gradle",
        "route": "/api/v2/orders/create",
        "component": "spring-beans",
        "tools": ["trivy", "semgrep", "nuclei"],
    },
    {
        "title": "Malicious Code Execution in XZ Utils Embedded Backdoor",
        "cve": "CVE-2024-3094",
        "cwe": ["CWE-506"],
        "severity": "CRITICAL",
        "package": "xz-utils",
        "file": "Dockerfile",
        "route": None,
        "component": "xz-utils",
        "tools": ["trivy"],
    },
    {
        "title": "Heap Buffer Overflow in libwebp Processing (WebP 0day)",
        "cve": "CVE-2023-4863",
        "cwe": ["CWE-787", "CWE-122"],
        "severity": "HIGH",
        "package": "libwebp-dev",
        "file": "Dockerfile",
        "route": "/api/v1/user/avatar/upload",
        "component": "libwebp",
        "tools": ["trivy", "nuclei"],
    },
    {
        "title": "SQL Injection in User Search Parameter via Raw SQL Query",
        "cve": None,
        "cwe": ["CWE-89"],
        "severity": "HIGH",
        "package": None,
        "file": "repositories/user_repo.go",
        "route": "/api/v1/users/search",
        "component": "user_repo.go",
        "tools": ["semgrep", "nuclei"],
    },
    {
        "title": "Path Traversal in Static File Serving Controller",
        "cve": None,
        "cwe": ["CWE-22"],
        "severity": "HIGH",
        "package": None,
        "file": "handlers/static.py",
        "route": "/api/static/download",
        "component": "static.py",
        "tools": ["semgrep", "nuclei"],
    },
    {
        "title": "Server-Side Request Forgery (SSRF) in Webhook Dispatcher",
        "cve": "CVE-2023-38606",
        "cwe": ["CWE-918"],
        "severity": "HIGH",
        "package": "requests",
        "file": "services/webhook_service.py",
        "route": "/api/v1/webhooks/test",
        "component": "webhook_service.py",
        "tools": ["semgrep", "nuclei"],
    },
    {
        "title": "Hardcoded Production JWT Signing Secret in Controller",
        "cve": None,
        "cwe": ["CWE-798"],
        "severity": "HIGH",
        "package": None,
        "file": "auth/token_manager.ts",
        "route": "/api/v1/oauth/token",
        "component": "token_manager.ts",
        "tools": ["semgrep"],
    },
    {
        "title": "Cross-Site Scripting (Reflected XSS) in Audit Log Viewer",
        "cve": None,
        "cwe": ["CWE-79"],
        "severity": "MEDIUM",
        "package": None,
        "file": "views/audit_viewer.tsx",
        "route": "/portal/audit/logs",
        "component": "audit_viewer.tsx",
        "tools": ["semgrep", "nuclei"],
    },
    {
        "title": "Insecure Deserialization in Redis Session Serializer",
        "cve": "CVE-2022-42889",
        "cwe": ["CWE-502"],
        "severity": "MEDIUM",
        "package": "commons-text",
        "file": "pom.xml",
        "route": "/api/session/restore",
        "component": "commons-text",
        "tools": ["trivy", "semgrep"],
    },
    {
        "title": "Missing Authorization Check on Tenant Deletion Endpoint",
        "cve": None,
        "cwe": ["CWE-862"],
        "severity": "HIGH",
        "package": None,
        "file": "controllers/tenant_controller.py",
        "route": "/api/v1/tenants/delete",
        "component": "tenant_controller.py",
        "tools": ["semgrep", "nuclei"],
    },
    {
        "title": "Outdated Node.js Dependency with Prototype Pollution",
        "cve": "CVE-2023-26159",
        "cwe": ["CWE-1321"],
        "severity": "MEDIUM",
        "package": "follow-redirects",
        "file": "package-lock.json",
        "route": None,
        "component": "follow-redirects",
        "tools": ["trivy"],
    },
    {
        "title": "CORS Misconfiguration Allowing Arbitrary Origin Access",
        "cve": None,
        "cwe": ["CWE-346"],
        "severity": "LOW",
        "package": None,
        "file": "middleware/cors.go",
        "route": "/api/v1/public/config",
        "component": "cors.go",
        "tools": ["nuclei", "semgrep"],
    },
    {
        "title": "Verbose Server Error Messages Exposing Stack Trace",
        "cve": None,
        "cwe": ["CWE-209"],
        "severity": "LOW",
        "package": None,
        "file": "middleware/error_handler.py",
        "route": "/api/health/diagnostics",
        "component": "error_handler.py",
        "tools": ["nuclei"],
    },
    {
        "title": "TLS 1.0/1.1 Weak Cipher Suite Enabled on Public Listener",
        "cve": None,
        "cwe": ["CWE-327"],
        "severity": "INFO",
        "package": None,
        "file": "nginx/conf.d/ssl.conf",
        "route": "https://gateway.cyberyukti.internal",
        "component": "ssl.conf",
        "tools": ["nuclei"],
    },
]


def generate_10k_benchmark_findings(total_count: int = 10000) -> List[CanonicalFinding]:
    """Generates an enterprise-scale dataset of ~10,000 realistic multi-scanner findings
    distributed across 12 microservices and 15 vulnerability classes.
    """
    findings: List[CanonicalFinding] = []
    rnd = random.Random(42)  # Deterministic seed for reproducible national hackathon results

    # We distribute findings across assets and templates
    # This creates realistic scanner alert storms (many duplicate/overlapping alerts from CI/CD,
    # Trivy container scans across nodes, Semgrep running on multiple branches, and Nuclei DAST probing routes).
    for i in range(total_count):
        asset = rnd.choice(ENTERPRISE_ASSETS)
        template = rnd.choice(ENTERPRISE_VULN_TEMPLATES)
        tool = rnd.choice(template["tools"])

        # Determine scan type
        if tool == "semgrep":
            scan_type = ScanType.SAST
        elif tool == "nuclei":
            scan_type = ScanType.DAST
        elif "Dockerfile" in (template["file"] or ""):
            scan_type = ScanType.CONTAINER
        else:
            scan_type = ScanType.SCA

        # Create realistic file/line/endpoint permutations
        line_no = None
        if scan_type == ScanType.SAST and template["file"]:
            line_no = rnd.randint(12, 450)

        endpoint = template["route"] if scan_type == ScanType.DAST else None

        fid = f"BENCH-{tool.upper()}-{i + 1:05d}"

        findings.append(
            CanonicalFinding(
                finding_id=fid,
                tool_name=tool,
                scan_type=scan_type,
                title=template["title"],
                description=f"{template['title']} identified in {asset} by {tool.upper()} automated inspection pipeline.",
                cve_id=template["cve"],
                cwe_ids=template["cwe"],
                raw_severity=template["severity"],
                target_asset=asset,
                file_path=template["file"],
                line_number=line_no,
                http_endpoint=endpoint,
                http_method="POST" if endpoint and "upload" in endpoint else "GET" if endpoint else None,
                package_name=template["package"],
                installed_version="1.0.0-vulnerable" if template["package"] else None,
                fixed_version="1.0.1-patched" if template["package"] else None,
                raw_payload={
                    "benchmark_run_id": "CY-10K-NATIONAL-HACKATHON-BENCHMARK",
                    "simulation_batch": (i // 500) + 1,
                    "scanner_rule_id": f"{tool}-rule-{template['component']}",
                },
            )
        )

    return findings


# ---------------------------------------------------------------------------
# High-Scale Pipeline Execution & Exact Report Compilation
# ---------------------------------------------------------------------------

def run_bulk_pipeline(
    findings: List[CanonicalFinding],
    sync_to_store: bool = True,
    pipeline_name: str = "Enterprise Multi-Scanner Pipeline",
) -> Dict[str, Any]:
    """Runs the 3-stage deduplication & Person 3 risk scoring pipeline on any finding batch,
    producing an exact comprehensive report.
    """
    start_time = time.time()
    total_raw = len(findings)

    # 1. Run 3-stage deduplication engine (Person 1)
    clusters, noise_reduction = DeduplicationEngine.process(findings)

    # 2. Tool breakdown
    tool_breakdown: Dict[str, int] = defaultdict(int)
    severity_breakdown: Dict[str, int] = defaultdict(int)
    scan_type_breakdown: Dict[str, int] = defaultdict(int)
    asset_set = set()

    for f in findings:
        tool_breakdown[f.tool_name] += 1
        severity_breakdown[f.raw_severity] += 1
        scan_type_breakdown[f.scan_type.value] += 1
        asset_set.add(f.target_asset)

    # 3. Person 3 Risk Scoring for each cluster
    scored_clusters = []
    priority_counts: Dict[str, int] = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    cross_tool_clusters = 0

    for cluster in clusters:
        rep = cluster.representative_finding
        sev_lower = (rep.raw_severity or "medium").lower()
        if sev_lower not in ("critical", "high", "medium", "low", "informational"):
            sev_lower = "medium"

        # Check multi-tool correlation
        if len(cluster.participating_tools) > 1:
            cross_tool_clusters += 1

        is_internet_facing = bool(cluster.normalized_route or "prod" in cluster.target_asset.lower())
        asset_criticality = 0.9 if "prod" in cluster.target_asset or "gateway" in cluster.target_asset else 0.7

        validation_status = "CONFIRMED" if "nuclei" in cluster.participating_tools and len(cluster.participating_tools) > 1 else "UNAVAILABLE"
        validation_conf = 0.92 if validation_status == "CONFIRMED" else 0.0

        finding_input = FindingInput(
            finding_id=cluster.cluster_id,
            cluster_id=cluster.cluster_id,
            title=cluster.title,
            severity=sev_lower,
            cve=cluster.primary_cve,
            cvss=9.8 if sev_lower == "critical" else 7.5 if sev_lower == "high" else 5.0,
            asset=AssetContext(
                id=cluster.target_asset,
                criticality=asset_criticality,
                internet_exposed=is_internet_facing,
                environment="production",
            ),
            validation=ValidationResult(status=validation_status, confidence=validation_conf),
        )

        score_result = calculate_risk_score(finding_input)
        p_val = score_result.priority if isinstance(score_result.priority, str) else str(score_result.priority)
        priority_counts[p_val] = priority_counts.get(p_val, 0) + 1

        sla_map = {"P1": "24 hours", "P2": "72 hours", "P3": "7 days", "P4": "30 days"}
        final_score = round(score_result.risk_score * 100.0, 1)

        factors = score_result.factors if isinstance(score_result.factors, dict) else score_result.factors.model_dump()

        scored_clusters.append({
            "cluster_id": cluster.cluster_id,
            "title": cluster.title,
            "primary_cve": cluster.primary_cve,
            "root_cause_cwe": cluster.root_cause_cwe,
            "target_asset": cluster.target_asset,
            "affected_component": cluster.affected_component,
            "normalized_route": cluster.normalized_route,
            "raw_findings_count": cluster.raw_findings_count,
            "participating_tools": cluster.participating_tools,
            "representative_severity": rep.raw_severity,
            "priority": p_val,
            "final_score": final_score,
            "sla": sla_map.get(p_val, "7 days"),
            "factors": factors,
            "reasons": score_result.reasons,
        })

    # Sort clusters by risk score descending
    scored_clusters.sort(key=lambda x: x["final_score"], reverse=True)

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    summary = {
        "pipeline_name": pipeline_name,
        "total_raw_findings": total_raw,
        "total_clusters": len(clusters),
        "noise_reduction_percentage": noise_reduction,
        "execution_time_ms": elapsed_ms,
        "total_assets_covered": len(asset_set),
        "cross_tool_correlated_count": cross_tool_clusters,
        "breakdown_by_tool": dict(tool_breakdown),
        "breakdown_by_severity": dict(severity_breakdown),
        "breakdown_by_priority": priority_counts,
        "breakdown_by_scan_type": dict(scan_type_breakdown),
    }

    # Optionally sync to backend shared store
    if sync_to_store:
        try:
            from backend.app.store import sync_bulk_clusters
            sync_bulk_clusters(clusters, scored_clusters, summary)
        except Exception:
            pass

    return {
        "status": "success",
        "summary": summary,
        "clusters_sample": scored_clusters[:100],  # Top 100 for instant UI inspection
        "all_clusters_count": len(scored_clusters),
        "top_actionable_p1_p2": [c for c in scored_clusters if c["priority"] in ("P1", "P2")][:25],
    }
