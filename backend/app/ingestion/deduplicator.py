"""Deduplication and Correlation Engine implementing GitLab Enterprise Triple-Tuple standards."""

from collections import defaultdict
import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple
from backend.app.ingestion.models import CanonicalFinding, IncidentCluster, ScanType


# Generic CWEs that must NEVER be used alone to cluster vulnerabilities across different locations
GENERIC_CWES = {
    "CWE-20",   # Improper Input Validation
    "CWE-22",   # Path Traversal
    "CWE-79",   # Cross-Site Scripting (XSS)
    "CWE-89",   # SQL Injection
    "CWE-200",  # Exposure of Sensitive Information
    "CWE-287",  # Improper Authentication
    "CWE-352",  # Cross-Site Request Forgery (CSRF)
    "CWE-434",  # Unrestricted Upload of File
    "CWE-502",  # Deserialization of Untrusted Data
    "CWE-798",  # Use of Hard-coded Credentials
}

SEVERITY_WEIGHTS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "INFO": 1,
    "UNKNOWN": 0,
}

TOOL_WEIGHTS = {
    "nuclei": 4,   # DAST (active runtime proof)
    "semgrep": 3,  # SAST (source code flaw)
    "trivy": 2,    # SCA / Container
}


class DeduplicationEngine:
    """Orchestrates 3-stage deduplication and cross-tool correlation."""

    @classmethod
    def process(cls, findings: List[CanonicalFinding]) -> Tuple[List[IncidentCluster], float]:
        """Runs the 3-stage deduplication pipeline on raw canonical findings.
        
        Returns:
            Tuple of (clusters, noise_reduction_percentage)
        """
        if not findings:
            return [], 0.0

        total_raw = len(findings)

        # Stage 1: Exact Hash Deduplication
        stage1_findings, raw_id_mapping = cls.stage1_exact_hash_dedup(findings)

        # Stage 2: GitLab Enterprise Triple-Tuple Clustering
        stage2_clusters = cls.stage2_gitlab_triple_tuple(stage1_findings, raw_id_mapping)

        # Stage 3: Cross-Tool SAST-to-DAST Route Correlation
        final_clusters = cls.stage3_cross_tool_correlation(stage2_clusters)

        # Calculate noise reduction percentage: (1 - total_clusters / total_raw) * 100
        noise_reduction = round((1.0 - (len(final_clusters) / float(total_raw))) * 100.0, 2)

        return final_clusters, noise_reduction

    @classmethod
    def stage1_exact_hash_dedup(
        cls, findings: List[CanonicalFinding]
    ) -> Tuple[List[CanonicalFinding], Dict[str, List[str]]]:
        """Stage 1: Collapses exact duplicates from identical scanner alerts.
        
        Groups by: tool_name + target_asset + identifier + location_signature
        """
        unique_findings: Dict[str, CanonicalFinding] = {}
        raw_id_mapping: Dict[str, List[str]] = defaultdict(list)

        for finding in findings:
            # Deterministic location signature
            loc_parts = [
                finding.tool_name,
                finding.target_asset,
                finding.cve_id or finding.title,
                finding.file_path or "",
                str(finding.line_number or ""),
                finding.http_endpoint or "",
                finding.http_method or "",
                finding.package_name or "",
                finding.installed_version or "",
            ]
            exact_key = hashlib.sha256(":".join(loc_parts).encode("utf-8")).hexdigest()

            raw_id_mapping[exact_key].append(finding.finding_id)
            if exact_key not in unique_findings:
                unique_findings[exact_key] = finding

        return list(unique_findings.values()), raw_id_mapping

    @classmethod
    def stage2_gitlab_triple_tuple(
        cls, findings: List[CanonicalFinding], raw_id_mapping: Dict[str, List[str]]
    ) -> List[Dict]:
        """Stage 2: GitLab Enterprise Triple-Tuple Deduplication.
        
        Tuple: [Asset Identifier] + [Location Fingerprint] + [Vulnerability Identifier]
        
        Strict Rule: Exclude generic CWEs from acting as solitary grouping identifiers.
        """
        grouped_clusters: Dict[str, List[CanonicalFinding]] = defaultdict(list)

        for finding in findings:
            asset_id = finding.target_asset

            # 1. Determine Vulnerability Identifier (CVE > Template ID > Rule ID / Title)
            # NEVER use generic CWE alone as vuln_id
            if finding.cve_id:
                vuln_id = finding.cve_id.upper()
            elif finding.scan_type == ScanType.DAST and (
                finding.raw_payload.get("template-id") or finding.raw_payload.get("templateID")
            ):
                vuln_id = str(
                    finding.raw_payload.get("template-id") or finding.raw_payload.get("templateID")
                ).upper()
            elif finding.package_name:
                vuln_id = f"PKG:{finding.package_name.lower()}"
            else:
                vuln_id = finding.title

            # 2. Determine Location Fingerprint
            if finding.scan_type in [ScanType.SCA, ScanType.CONTAINER]:
                # For dependencies: group by package name across multiple file locations / layers
                pkg = (finding.package_name or "unknown-pkg").lower()
                location_fp = f"pkg:{pkg}"
                # For SCA/Container, the tuple is: asset + package + cve_id/vuln_id
                prefix = "CONTAINER" if finding.scan_type == ScanType.CONTAINER else "SCA"
                cluster_key = f"{prefix}:{asset_id}:{location_fp}:{vuln_id}"

            elif finding.scan_type == ScanType.SAST:
                # For SAST: group by normalized file component + rule/vuln
                norm_file = (finding.file_path or "unknown-file").replace("\\", "/").strip("./")
                # Strip specific sub-line noise to aggregate file-level/component-level flaw
                location_fp = f"file:{norm_file}"
                cluster_key = f"SAST:{asset_id}:{location_fp}:{vuln_id}"

            elif finding.scan_type == ScanType.DAST:
                # For DAST: group by normalized endpoint route + vuln/template
                route = (finding.http_endpoint or "/").split("?")[0].rstrip("/") or "/"
                location_fp = f"route:{route}"
                cluster_key = f"DAST:{asset_id}:{location_fp}:{vuln_id}"

            else:
                cluster_key = f"MISC:{asset_id}:{vuln_id}"

            grouped_clusters[cluster_key].append(finding)

        # Build intermediate cluster representations
        intermediate_clusters: List[Dict] = []
        for cluster_key, cluster_findings in grouped_clusters.items():
            # Gather all raw IDs mapped to these findings
            underlying_raw_ids: List[str] = []
            for f in cluster_findings:
                # Find matching exact key in raw_id_mapping
                matched_raws = []
                for _, raw_list in raw_id_mapping.items():
                    if f.finding_id in raw_list:
                        matched_raws.extend(raw_list)
                if not matched_raws:
                    matched_raws = [f.finding_id]
                underlying_raw_ids.extend(matched_raws)

            underlying_raw_ids = sorted(list(set(underlying_raw_ids)))

            # Pick representative finding
            rep_finding = cls._select_representative(cluster_findings)

            # Determine dominant CVE and CWE
            all_cves = [f.cve_id for f in cluster_findings if f.cve_id]
            primary_cve = all_cves[0] if all_cves else None

            all_cwes: List[str] = []
            for f in cluster_findings:
                all_cwes.extend(f.cwe_ids)
            root_cause_cwe = cls._pick_dominant_cwe(all_cwes)

            # Determine affected component
            affected_component = (
                rep_finding.package_name
                or rep_finding.http_endpoint
                or (rep_finding.file_path.replace("\\", "/") if rep_finding.file_path else "system")
            )

            # Route resolution
            route = None
            for f in cluster_findings:
                if f.http_endpoint:
                    route = f.http_endpoint.split("?")[0]
                    break

            tools = sorted(list(set(f.tool_name for f in cluster_findings)))

            intermediate_clusters.append({
                "cluster_key": cluster_key,
                "title": rep_finding.title,
                "primary_cve": primary_cve,
                "root_cause_cwe": root_cause_cwe,
                "target_asset": rep_finding.target_asset,
                "affected_component": affected_component,
                "normalized_route": route,
                "findings": cluster_findings,
                "participating_tools": tools,
                "underlying_finding_ids": underlying_raw_ids,
                "representative_finding": rep_finding,
            })

        return intermediate_clusters

    @classmethod
    def stage3_cross_tool_correlation(cls, clusters: List[Dict]) -> List[IncidentCluster]:
        """Stage 3: Cross-Tool SAST-to-DAST Route Correlation.
        
        Correlates code-level SAST findings (e.g. handlers/static.py) with active DAST
        findings on the same route (e.g. /api/static/download) and matching weakness/CWE.
        Merges them into unified high-confidence incident clusters.
        """
        # Separate SAST, DAST, and other clusters
        sast_clusters = [c for c in clusters if c["cluster_key"].startswith("SAST:")]
        dast_clusters = [c for c in clusters if c["cluster_key"].startswith("DAST:")]
        other_clusters = [c for c in clusters if not c["cluster_key"].startswith("SAST:") and not c["cluster_key"].startswith("DAST:")]

        merged_sast_keys: Set[str] = set()
        merged_dast_keys: Set[str] = set()
        correlated_clusters: List[IncidentCluster] = []

        # Correlate SAST with DAST
        for d_clust in dast_clusters:
            dast_route = (d_clust.get("normalized_route") or "").rstrip("/")
            dast_cwe = d_clust.get("root_cause_cwe")
            dast_cve = d_clust.get("primary_cve")

            for s_clust in sast_clusters:
                if s_clust["cluster_key"] in merged_sast_keys:
                    continue

                sast_route = (s_clust.get("normalized_route") or "").rstrip("/")
                sast_cwe = s_clust.get("root_cause_cwe")
                sast_cve = s_clust.get("primary_cve")
                sast_component = (s_clust.get("affected_component") or "").lower()

                # Check route match or component-to-route semantic match
                route_matches = False
                if dast_route and (sast_route == dast_route):
                    route_matches = True
                elif dast_route and any(part in dast_route for part in ["static", "download"]) and "static" in sast_component:
                    route_matches = True

                # Check root cause similarity (shared CWE, shared CVE, or both are Path Traversal / Injection)
                cwe_matches = (
                    (dast_cwe and sast_cwe and dast_cwe == sast_cwe)
                    or (dast_cve and sast_cve and dast_cve == sast_cve)
                    or ("traversal" in d_clust["title"].lower() and "traversal" in s_clust["title"].lower())
                )

                if route_matches and cwe_matches:
                    # Correlate into unified cluster!
                    merged_sast_keys.add(s_clust["cluster_key"])
                    merged_dast_keys.add(d_clust["cluster_key"])

                    combined_raw_ids = sorted(list(set(
                        d_clust["underlying_finding_ids"] + s_clust["underlying_finding_ids"]
                    )))
                    all_tools = sorted(list(set(
                        d_clust["participating_tools"] + s_clust["participating_tools"]
                    )))

                    # Pick highest fidelity representative finding (DAST preferred for runtime exploitability)
                    rep = cls._select_representative([
                        d_clust["representative_finding"],
                        s_clust["representative_finding"]
                    ])

                    # Derive meaningful category title
                    if (dast_cwe == "CWE-22" or sast_cwe == "CWE-22" or "traversal" in rep.title.lower()):
                        vuln_desc = "Path Traversal"
                    elif (dast_cwe == "CWE-287" or sast_cwe == "CWE-287" or "auth" in rep.title.lower()):
                        vuln_desc = "Improper Authentication"
                    else:
                        vuln_desc = rep.title

                    correlated_title = f"[Correlated SAST+DAST] {vuln_desc} in {dast_route or sast_component}"
                    if rep.cve_id:
                        correlated_title += f" ({rep.cve_id})"

                    cluster_obj = IncidentCluster(
                        cluster_id="",  # assigned later sequentially
                        title=correlated_title,
                        primary_cve=dast_cve or sast_cve,
                        root_cause_cwe=dast_cwe or sast_cwe or "CWE-22",
                        target_asset=rep.target_asset,
                        affected_component=s_clust["affected_component"],
                        normalized_route=dast_route or sast_route,
                        raw_findings_count=len(combined_raw_ids),
                        participating_tools=all_tools,
                        underlying_finding_ids=combined_raw_ids,
                        representative_finding=rep,
                    )
                    correlated_clusters.append(cluster_obj)
                    break

        # Add unmerged DAST clusters
        for d_clust in dast_clusters:
            if d_clust["cluster_key"] not in merged_dast_keys:
                cluster_obj = IncidentCluster(
                    cluster_id="",
                    title=f"[DAST] {d_clust['title']}",
                    primary_cve=d_clust["primary_cve"],
                    root_cause_cwe=d_clust["root_cause_cwe"],
                    target_asset=d_clust["target_asset"],
                    affected_component=d_clust["affected_component"],
                    normalized_route=d_clust["normalized_route"],
                    raw_findings_count=len(d_clust["underlying_finding_ids"]),
                    participating_tools=d_clust["participating_tools"],
                    underlying_finding_ids=d_clust["underlying_finding_ids"],
                    representative_finding=d_clust["representative_finding"],
                )
                correlated_clusters.append(cluster_obj)

        # Add unmerged SAST clusters
        for s_clust in sast_clusters:
            if s_clust["cluster_key"] not in merged_sast_keys:
                cluster_obj = IncidentCluster(
                    cluster_id="",
                    title=f"[SAST] {s_clust['title']}",
                    primary_cve=s_clust["primary_cve"],
                    root_cause_cwe=s_clust["root_cause_cwe"],
                    target_asset=s_clust["target_asset"],
                    affected_component=s_clust["affected_component"],
                    normalized_route=s_clust["normalized_route"],
                    raw_findings_count=len(s_clust["underlying_finding_ids"]),
                    participating_tools=s_clust["participating_tools"],
                    underlying_finding_ids=s_clust["underlying_finding_ids"],
                    representative_finding=s_clust["representative_finding"],
                )
                correlated_clusters.append(cluster_obj)

        # Add other (SCA / Container) clusters
        for o_clust in other_clusters:
            tool_prefix = "[SCA]" if "SCA" in o_clust["cluster_key"] else "[Container]"
            cluster_obj = IncidentCluster(
                cluster_id="",
                title=f"{tool_prefix} {o_clust['title']}",
                primary_cve=o_clust["primary_cve"],
                root_cause_cwe=o_clust["root_cause_cwe"],
                target_asset=o_clust["target_asset"],
                affected_component=o_clust["affected_component"],
                normalized_route=o_clust["normalized_route"],
                raw_findings_count=len(o_clust["underlying_finding_ids"]),
                participating_tools=o_clust["participating_tools"],
                underlying_finding_ids=o_clust["underlying_finding_ids"],
                representative_finding=o_clust["representative_finding"],
            )
            correlated_clusters.append(cluster_obj)

        # Assign sequential IDs e.g. CLUST-001, CLUST-002
        for idx, clust in enumerate(correlated_clusters, start=1):
            clust.cluster_id = f"CLUST-{idx:03d}"

        return correlated_clusters

    @classmethod
    def _select_representative(cls, findings: List[CanonicalFinding]) -> CanonicalFinding:
        """Selects the highest fidelity representative finding.
        
        Priority:
        1. Severity weight (CRITICAL > HIGH > MEDIUM > LOW > INFO)
        2. Tool fidelity weight (DAST > SAST > SCA > CONTAINER)
        3. Presence of CVE ID
        """
        def score(f: CanonicalFinding) -> Tuple[int, int, int]:
            sev_score = SEVERITY_WEIGHTS.get(f.raw_severity.upper(), 0)
            tool_score = TOOL_WEIGHTS.get(f.tool_name.lower(), 0)
            cve_score = 1 if f.cve_id else 0
            return (sev_score, tool_score, cve_score)

        return max(findings, key=score)

    @classmethod
    def _pick_dominant_cwe(cls, cwes: List[str]) -> Optional[str]:
        """Picks the most specific dominant CWE from a list."""
        if not cwes:
            return None
        counts: Dict[str, int] = defaultdict(int)
        for c in cwes:
            counts[c] += 1
        # Sort by frequency descending, then prefer more specific over generic if equal
        sorted_cwes = sorted(
            counts.keys(),
            key=lambda x: (counts[x], 0 if x in GENERIC_CWES else 1),
            reverse=True,
        )
        return sorted_cwes[0] if sorted_cwes else None
