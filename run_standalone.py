#!/usr/bin/env python3
"""CyberYukti Person 1: Finding Intelligence & Deduplication Engine Standalone CLI Runner."""

import json
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ingestion.normalizer import FindingIntelligenceEngine


def run_pipeline() -> None:
    # Ensure UTF-8 output if supported
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    console = Console()

    console.print(
        Panel.fit(
            "[bold cyan]CyberYukti - Autonomous Vulnerability Triage & Evidence Engine (PS16)[/bold cyan]\n"
            "[yellow]Person 1: Finding Intelligence & Deduplication Engine[/yellow]",
            border_style="cyan",
        )
    )

    # Define fixture paths
    raw_fixtures_dir = PROJECT_ROOT / "backend" / "fixtures" / "raw_scans"
    mock_output_dir = PROJECT_ROOT / "backend" / "fixtures" / "mock_output"
    mock_output_dir.mkdir(parents=True, exist_ok=True)

    scan_files = [
        str(raw_fixtures_dir / "trivy_scan.json"),
        str(raw_fixtures_dir / "semgrep_scan.json"),
        str(raw_fixtures_dir / "nuclei_scan.json"),
    ]

    for fpath in scan_files:
        if not os.path.exists(fpath):
            console.print(f"[bold red]Error:[/] Required scan fixture not found: {fpath}")
            sys.exit(1)

    console.print("[bold green]==> Loading and ingesting multi-scanner raw scans...[/bold green]")
    engine = FindingIntelligenceEngine(default_asset="cyberyukti-target:v1.2")
    clusters, summary = engine.process_raw_files(scan_files)

    # Ingestion Summary Table
    summary_table = Table(title="Finding Ingestion & Noise Reduction Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="bold magenta")

    summary_table.add_row("Total Raw Findings Ingested", str(summary.total_raw_findings))
    summary_table.add_row("Actionable Incident Clusters", str(summary.total_clusters))
    summary_table.add_row(
        "Noise Reduction Percentage", f"[bold green]{summary.noise_reduction_percentage:.2f}%[/bold green]"
    )

    for tool, count in summary.breakdown_by_tool.items():
        summary_table.add_row(f"Raw Findings ({tool})", str(count))

    console.print(summary_table)
    console.print()

    # Clusters Detail Table
    clusters_table = Table(title="Triaged Actionable Incident Clusters", box=box.ROUNDED)
    clusters_table.add_column("Cluster ID", style="bold yellow", no_wrap=True)
    clusters_table.add_column("Incident Title", style="white")
    clusters_table.add_column("Primary CVE", style="bold red", no_wrap=True)
    clusters_table.add_column("Root CWE", style="blue", no_wrap=True)
    clusters_table.add_column("Participating Tools", style="cyan")
    clusters_table.add_column("Raw Findings Collapsed", style="magenta", justify="right")
    clusters_table.add_column("Normalized Route / Target", style="dim")

    for cluster in clusters:
        cve_display = cluster.primary_cve or "N/A"
        cwe_display = cluster.root_cause_cwe or "N/A"
        tools_display = ", ".join(cluster.participating_tools)
        route_display = cluster.normalized_route or cluster.affected_component

        clusters_table.add_row(
            cluster.cluster_id,
            cluster.title,
            cve_display,
            cwe_display,
            tools_display,
            str(cluster.raw_findings_count),
            route_display,
        )

    console.print(clusters_table)
    console.print()

    # Export to mock_output/verified_clusters.json
    output_file = mock_output_dir / "verified_clusters.json"
    export_data = {
        "summary": summary.model_dump(),
        "clusters": [c.model_dump() for c in clusters],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    console.print(
        f"[bold green][OK] Successfully exported canonical triaged clusters to:[/bold green] [underline]{output_file}[/underline]"
    )
    console.print(
        "[dim]Ready for Person 2 (Graph Context/KEV/EPSS), Person 3 (Exploitability Proof), and Person 4 (Remediation).[/dim]\n"
    )


if __name__ == "__main__":
    run_pipeline()
