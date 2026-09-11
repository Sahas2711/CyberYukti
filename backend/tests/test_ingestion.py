"""Comprehensive test suite for Finding Intelligence & Deduplication Engine (CyberYukti Person 1)."""

import os
from pathlib import Path
import pytest

from backend.app.ingestion.models import CanonicalFinding, ScanType
from backend.app.ingestion.parsers.trivy_parser import TrivyParser
from backend.app.ingestion.parsers.semgrep_parser import SemgrepParser
from backend.app.ingestion.parsers.nuclei_parser import NucleiParser
from backend.app.ingestion.deduplicator import DeduplicationEngine
from backend.app.ingestion.normalizer import FindingIntelligenceEngine

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "raw_scans"


@pytest.fixture
def trivy_fixture_path() -> str:
    return str(FIXTURES_DIR / "trivy_scan.json")


@pytest.fixture
def semgrep_fixture_path() -> str:
    return str(FIXTURES_DIR / "semgrep_scan.json")


@pytest.fixture
def nuclei_fixture_path() -> str:
    return str(FIXTURES_DIR / "nuclei_scan.json")


def test_trivy_parser(trivy_fixture_path: str):
    """Verifies Trivy parser correctly extracts SCA and Container findings."""
    findings = TrivyParser.parse_file(trivy_fixture_path)
    assert len(findings) == 25

    # Check SCA aiohttp finding
    aiohttp_vulns = [f for f in findings if f.package_name == "aiohttp"]
    assert len(aiohttp_vulns) == 15
    for f in aiohttp_vulns:
        assert f.scan_type == ScanType.SCA
        assert f.cve_id == "CVE-2023-38606"
        assert f.installed_version == "3.8.4"
        assert f.fixed_version == "3.8.5"
        assert "CWE-22" in f.cwe_ids

    # Check Container libssl3 finding
    libssl_vulns = [f for f in findings if f.package_name == "libssl3"]
    assert len(libssl_vulns) == 10
    for f in libssl_vulns:
        assert f.scan_type == ScanType.CONTAINER
        assert f.cve_id == "CVE-2023-0286"
        assert "CWE-843" in f.cwe_ids


def test_semgrep_parser(semgrep_fixture_path: str):
    """Verifies Semgrep parser correctly normalizes SAST results and infers routes."""
    findings = SemgrepParser.parse_file(semgrep_fixture_path)
    assert len(findings) == 12

    # Path traversal in handlers/static.py
    static_vulns = [f for f in findings if "static.py" in (f.file_path or "")]
    assert len(static_vulns) == 8
    for f in static_vulns:
        assert f.scan_type == ScanType.SAST
        assert f.http_endpoint == "/api/static/download"
        assert "CWE-22" in f.cwe_ids
        assert f.raw_severity in ["HIGH", "ERROR"]

    # Improper auth in admin/auth.py
    admin_vulns = [f for f in findings if "admin/auth.py" in (f.file_path or "")]
    assert len(admin_vulns) == 4
    for f in admin_vulns:
        assert f.scan_type == ScanType.SAST
        assert f.http_endpoint == "/api/admin/auth"
        assert "CWE-287" in f.cwe_ids


def test_nuclei_parser(nuclei_fixture_path: str):
    """Verifies Nuclei parser correctly normalizes DAST findings and URL paths."""
    findings = NucleiParser.parse_file(nuclei_fixture_path)
    assert len(findings) == 5

    # Path traversal findings
    path_traversal = [f for f in findings if f.http_endpoint == "/api/static/download"]
    assert len(path_traversal) == 3
    for f in path_traversal:
        assert f.scan_type == ScanType.DAST
        assert f.cve_id == "CVE-2023-38606"
        assert "CWE-22" in f.cwe_ids
        assert f.http_method == "GET"

    # Admin auth bypass findings
    admin_auth = [f for f in findings if f.http_endpoint == "/api/admin/auth"]
    assert len(admin_auth) == 2
    for f in admin_auth:
        assert f.scan_type == ScanType.DAST
        assert "CWE-287" in f.cwe_ids


def test_stage1_exact_hash_dedup():
    """Verifies Stage 1 exact hash deduplication collapses byte-for-byte identical reports."""
    finding1 = CanonicalFinding(
        finding_id="f1",
        tool_name="semgrep",
        scan_type=ScanType.SAST,
        title="Path Traversal",
        description="Arbitrary file read",
        cve_id="CVE-2023-38606",
        cwe_ids=["CWE-22"],
        raw_severity="HIGH",
        target_asset="app:v1",
        file_path="handlers/static.py",
        line_number=45,
        http_endpoint="/api/static/download",
    )
    # Exact duplicate
    finding2 = finding1.model_copy(update={"finding_id": "f2"})
    # Different line
    finding3 = finding1.model_copy(update={"finding_id": "f3", "line_number": 90})

    unique, raw_mapping = DeduplicationEngine.stage1_exact_hash_dedup([finding1, finding2, finding3])
    assert len(unique) == 2  # f1 and f2 collapsed to 1, f3 is separate line


def test_stage2_generic_cwe_exclusion():
    """CRUCIAL TEST: Verifies that generic CWEs (e.g. CWE-79, CWE-22) are NOT clustered alone.
    
    Two distinct findings in different files sharing only CWE-79 MUST remain separate.
    """
    finding_a = CanonicalFinding(
        finding_id="xss1",
        tool_name="semgrep",
        scan_type=ScanType.SAST,
        title="rules.python.security.xss.search",
        description="Reflected XSS in search",
        cwe_ids=["CWE-79"],
        raw_severity="HIGH",
        target_asset="app:v1",
        file_path="controllers/search.py",
        line_number=20,
    )
    finding_b = CanonicalFinding(
        finding_id="xss2",
        tool_name="semgrep",
        scan_type=ScanType.SAST,
        title="rules.python.security.xss.profile",
        description="Stored XSS in user profile",
        cwe_ids=["CWE-79"],  # Same generic CWE!
        raw_severity="HIGH",
        target_asset="app:v1",
        file_path="controllers/profile.py",  # Different file!
        line_number=55,
    )

    clusters, _ = DeduplicationEngine.process([finding_a, finding_b])
    # They MUST NOT be clustered into 1 cluster because generic CWEs are strictly excluded!
    assert len(clusters) == 2
    files = {c.affected_component for c in clusters}
    assert "controllers/search.py" in files
    assert "controllers/profile.py" in files


def test_stage3_cross_tool_route_correlation():
    """Verifies SAST and DAST correlation on matching route and weakness."""
    sast_finding = CanonicalFinding(
        finding_id="s1",
        tool_name="semgrep",
        scan_type=ScanType.SAST,
        title="rules.python.path-traversal.open",
        description="Path traversal in file reader",
        cve_id="CVE-2023-38606",
        cwe_ids=["CWE-22"],
        raw_severity="HIGH",
        target_asset="app:v1",
        file_path="handlers/static.py",
        line_number=34,
        http_endpoint="/api/static/download",
    )
    dast_finding = CanonicalFinding(
        finding_id="d1",
        tool_name="nuclei",
        scan_type=ScanType.DAST,
        title="Generic Path Traversal",
        description="Active file read on endpoint",
        cve_id="CVE-2023-38606",
        cwe_ids=["CWE-22"],
        raw_severity="HIGH",
        target_asset="app:v1",
        http_endpoint="/api/static/download",
        http_method="GET",
    )

    clusters, noise = DeduplicationEngine.process([sast_finding, dast_finding])
    assert len(clusters) == 1
    cluster = clusters[0]
    assert "semgrep" in cluster.participating_tools
    assert "nuclei" in cluster.participating_tools
    assert cluster.normalized_route == "/api/static/download"
    assert cluster.raw_findings_count == 2
    assert noise == 50.0


def test_full_pipeline_42_findings_to_4_clusters(
    trivy_fixture_path: str, semgrep_fixture_path: str, nuclei_fixture_path: str
):
    """End-to-end integration test:
    Ingests 42 raw findings across 3 tools.
    Must collapse into 4 actionable incident clusters with >85% noise reduction.
    """
    engine = FindingIntelligenceEngine(default_asset="cyberyukti-target:v1.2")
    scan_files = [trivy_fixture_path, semgrep_fixture_path, nuclei_fixture_path]

    clusters, summary = engine.process_raw_files(scan_files)

    # Validate raw counts
    assert summary.total_raw_findings == 42
    assert summary.breakdown_by_tool == {"trivy": 25, "semgrep": 12, "nuclei": 5}

    # Validate clusters count
    assert summary.total_clusters == 4
    assert len(clusters) == 4

    # Validate noise reduction exceeds 85% requirement
    assert summary.noise_reduction_percentage > 85.0
    assert summary.noise_reduction_percentage == 90.48

    # Validate individual clusters
    cluster_titles = [c.title for c in clusters]
    assert any("Path Traversal" in t and "Correlated" in t for t in cluster_titles)
    assert any("Authentication" in t and "Correlated" in t for t in cluster_titles)
    assert any("aiohttp" in t for t in cluster_titles)
    assert any("libssl" in t or "openssl" in t for t in cluster_titles)

    # Check tool participation in correlated clusters
    path_traversal_cluster = next(c for c in clusters if "Path Traversal" in c.title)
    assert set(path_traversal_cluster.participating_tools) == {"nuclei", "semgrep"}
    assert path_traversal_cluster.raw_findings_count == 11
    assert path_traversal_cluster.normalized_route == "/api/static/download"
    assert path_traversal_cluster.primary_cve == "CVE-2023-38606"
    assert path_traversal_cluster.root_cause_cwe == "CWE-22"

    admin_cluster = next(c for c in clusters if "Authentication" in c.title)
    assert set(admin_cluster.participating_tools) == {"nuclei", "semgrep"}
    assert admin_cluster.raw_findings_count == 6
    assert admin_cluster.normalized_route == "/api/admin/auth"
    assert admin_cluster.root_cause_cwe == "CWE-287"

    sca_cluster = next(c for c in clusters if "aiohttp" in c.title)
    assert sca_cluster.participating_tools == ["trivy"]
    assert sca_cluster.raw_findings_count == 15
    assert sca_cluster.primary_cve == "CVE-2023-38606"

    container_cluster = next(c for c in clusters if "libssl" in c.title or "openssl" in c.title)
    assert container_cluster.participating_tools == ["trivy"]
    assert container_cluster.raw_findings_count == 10
    assert container_cluster.primary_cve == "CVE-2023-0286"
