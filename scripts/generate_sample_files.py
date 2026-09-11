"""Generates sample test files (JSON & CSV) for testing the CyberYukti pipeline
at both representative scale (18 test cases) and enterprise stress scale (10,000 vulnerabilities).
"""

import csv
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.ingestion.bulk_processor import generate_10k_benchmark_findings

def generate_10k_files():
    out_dir = BASE_DIR / "backend" / "fixtures" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[*] Generating 10,000 vulnerability benchmark findings...")
    findings = generate_10k_benchmark_findings(10000)

    # 1. JSON Export
    json_file = out_dir / "sample_10000_vulnerabilities.json"
    data = [f.model_dump() for f in findings]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[+] Written 10,000 findings JSON: {json_file} ({json_file.stat().st_size / (1024*1024):.2f} MB)")

    # 2. CSV Export
    csv_file = out_dir / "sample_10000_vulnerabilities.csv"
    fields = [
        "title", "severity", "asset", "cve", "cwe", "tool",
        "path", "endpoint", "package", "installed_version", "fixed_version", "description"
    ]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for x in findings:
            writer.writerow({
                "title": x.title,
                "severity": x.raw_severity,
                "asset": x.target_asset,
                "cve": x.cve_id or "",
                "cwe": ",".join(x.cwe_ids),
                "tool": x.tool_name,
                "path": x.file_path or "",
                "endpoint": x.http_endpoint or "",
                "package": x.package_name or "",
                "installed_version": x.installed_version or "",
                "fixed_version": x.fixed_version or "",
                "description": x.description,
            })
    print(f"[+] Written 10,000 findings CSV:  {csv_file} ({csv_file.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    generate_10k_files()
