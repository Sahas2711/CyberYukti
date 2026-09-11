"""Engine Orchestrator: FindingIntelligenceEngine for multi-scanner ingestion and deduplication."""

import json
import os
from typing import Dict, List, Tuple
from backend.app.ingestion.models import (
    CanonicalFinding,
    IncidentCluster,
    IngestionSummary,
)
from backend.app.ingestion.parsers.trivy_parser import TrivyParser
from backend.app.ingestion.parsers.semgrep_parser import SemgrepParser
from backend.app.ingestion.parsers.nuclei_parser import NucleiParser
from backend.app.ingestion.deduplicator import DeduplicationEngine


class FindingIntelligenceEngine:
    """Orchestrates multi-scanner parsing, canonicalization, deduplication, and metrics generation."""

    def __init__(self, default_asset: str = "cyberyukti-target"):
        self.default_asset = default_asset
        self.trivy_parser = TrivyParser()
        self.semgrep_parser = SemgrepParser()
        self.nuclei_parser = NucleiParser()
        self.deduplicator = DeduplicationEngine()

    def detect_file_type(self, file_path: str) -> str:
        """Heuristically detects scanner output format from file content or name."""
        base_name = os.path.basename(file_path).lower()
        if "trivy" in base_name:
            return "trivy"
        if "semgrep" in base_name or "sarif" in base_name:
            return "semgrep"
        if "nuclei" in base_name:
            return "nuclei"

        # Content inspection
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_chunk = f.read(4096)
                if "ArtifactName" in first_chunk or "VulnerabilityID" in first_chunk:
                    return "trivy"
                if "check_id" in first_chunk or '"runs":' in first_chunk:
                    return "semgrep"
                if "template-id" in first_chunk or "matched-at" in first_chunk:
                    return "nuclei"
        except Exception:
            pass

        return "unknown"

    def parse_file(self, file_path: str) -> List[CanonicalFinding]:
        """Parses an individual scan file using the appropriate parser."""
        file_type = self.detect_file_type(file_path)

        if file_type == "trivy":
            return self.trivy_parser.parse_file(file_path, default_asset=self.default_asset)
        elif file_type == "semgrep":
            return self.semgrep_parser.parse_file(file_path, default_asset=self.default_asset)
        elif file_type == "nuclei":
            return self.nuclei_parser.parse_file(file_path, default_asset=self.default_asset)
        else:
            raise ValueError(f"Unable to determine scanner format for file: {file_path}")

    def process_raw_files(self, file_paths: List[str]) -> Tuple[List[IncidentCluster], IngestionSummary]:
        """Ingests multiple raw scan files, canonicalizes findings, deduplicates, and correlates.
        
        Returns:
            Tuple of (IncidentCluster list, IngestionSummary)
        """
        all_findings: List[CanonicalFinding] = []

        for path in file_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Scanner output file not found: {path}")
            parsed = self.parse_file(path)
            all_findings.extend(parsed)

        return self.process_findings(all_findings)

    def process_findings(self, findings: List[CanonicalFinding]) -> Tuple[List[IncidentCluster], IngestionSummary]:
        """Deduplicates and clusters a pre-parsed list of CanonicalFindings."""
        total_raw = len(findings)

        # Calculate breakdown by tool
        tool_breakdown: Dict[str, int] = {}
        for f in findings:
            tool_breakdown[f.tool_name] = tool_breakdown.get(f.tool_name, 0) + 1

        # Run 3-stage deduplication and cross-tool correlation
        clusters, noise_reduction = self.deduplicator.process(findings)

        summary = IngestionSummary(
            total_raw_findings=total_raw,
            total_clusters=len(clusters),
            noise_reduction_percentage=noise_reduction,
            breakdown_by_tool=tool_breakdown,
        )

        return clusters, summary
