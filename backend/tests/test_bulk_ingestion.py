"""Tests for bulk scanner ingestion, 10,000 benchmark, CSV/JSON parsing, and exact reporting."""

import pytest
from backend.app.ingestion.bulk_processor import (
    generate_10k_benchmark_findings,
    parse_csv_content,
    parse_json_content,
    run_bulk_pipeline,
)


def test_csv_parser():
    sample_csv = """Title,Severity,Asset,CVE,CWE,Tool,Path
Log4j RCE,CRITICAL,auth-service-prod:latest,CVE-2021-44228,CWE-502,trivy,pom.xml
Log4j RCE,CRITICAL,auth-service-prod:latest,CVE-2021-44228,CWE-502,trivy,pom.xml
Path Traversal,HIGH,frontend-proxy,,CWE-22,semgrep,static.py
Path Traversal,HIGH,frontend-proxy,,CWE-22,nuclei,/api/static/download
"""
    findings = parse_csv_content(sample_csv)
    assert len(findings) == 4

    report = run_bulk_pipeline(findings, sync_to_store=False)
    summary = report["summary"]
    assert summary["total_raw_findings"] == 4
    # The 2 Log4j findings collapse into 1, Path Traversal SAST + DAST correlate into 1
    assert summary["total_clusters"] == 2
    assert summary["noise_reduction_percentage"] == 50.0
    assert summary["cross_tool_correlated_count"] == 1


def test_json_generic_parser():
    sample_json = """[
        {"title": "Spring4Shell RCE", "severity": "CRITICAL", "asset": "order-api", "cve": "CVE-2022-22965", "tool": "trivy"},
        {"title": "Spring4Shell RCE", "severity": "CRITICAL", "asset": "order-api", "cve": "CVE-2022-22965", "tool": "trivy"},
        {"title": "SQL Injection", "severity": "HIGH", "asset": "user-db", "cwe": "CWE-89", "tool": "semgrep", "file": "repo.py", "line": 42}
    ]"""
    findings = parse_json_content(sample_json)
    assert len(findings) == 3

    report = run_bulk_pipeline(findings, sync_to_store=False)
    summary = report["summary"]
    assert summary["total_raw_findings"] == 3
    assert summary["total_clusters"] == 2
    assert summary["noise_reduction_percentage"] == 33.33


def test_10k_benchmark_pipeline():
    findings = generate_10k_benchmark_findings(total_count=1000)
    assert len(findings) == 1000

    report = run_bulk_pipeline(findings, sync_to_store=False)
    summary = report["summary"]
    assert summary["total_raw_findings"] == 1000
    assert summary["total_clusters"] < 350
    assert summary["noise_reduction_percentage"] > 65.0
    assert summary["total_assets_covered"] == 12
    assert "P1" in summary["breakdown_by_priority"]
    assert len(report["clusters_sample"]) > 0
