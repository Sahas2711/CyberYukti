"use client";

import { useEffect, useCallback, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getProvider } from "@/lib/providers";
import type {
  AnalysisCreateRequest,
  AnalysisStatusResponse,
  AnalysisLogsResponse,
  AnalysisFindingsResponse,
  AnalysisClustersResponse,
  AnalysisReportResponse,
  AnalysisStatus,
  ScannerStatus,
  CanonicalFindingResponse,
} from "@/lib/api/types";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Skeleton } from "@/components/shared/Skeleton";
import {
  GitBranch,
  Container,
  Play,
  Loader,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Download,
  ChevronDown,
  ChevronUp,
  Terminal,
  FileText,
  Package,
  Search,
} from "lucide-react";

interface StageLogInfo {
  findings_count?: number | null;
  duration_seconds?: number | null;
  raw_output_path?: string | null;
  error?: string | null;
}

const STAGE_ORDER: { key: string; label: string; icon: React.ReactNode }[] = [
  { key: "github_acquisition", label: "GitHub Repository", icon: <GitBranch className="w-4 h-4" /> },
  { key: "semgrep", label: "Semgrep SAST Scan", icon: <Search className="w-4 h-4" /> },
  { key: "docker_pull", label: "Docker Image Pull", icon: <Container className="w-4 h-4" /> },
  { key: "trivy", label: "Trivy Image Scan", icon: <Package className="w-4 h-4" /> },
  { key: "pipeline", label: "Pipeline Processing", icon: <GitBranch className="w-4 h-4" /> },
];

function getStatusBadge(status: AnalysisStatus | ScannerStatus | undefined) {
  if (!status) return <Badge variant="secondary">Pending</Badge>;
  switch (status) {
    case "queued":
    case "pending":
      return <Badge variant="secondary">Queued</Badge>;
    case "running":
    case "github_clone":
    case "semgrep_scan":
    case "docker_pull":
    case "trivy_scan":
    case "normalizing":
    case "deduplicating":
    case "correlating":
      return <Badge variant="primary"><Loader className="w-3 h-3 animate-spin mr-1" /> Running</Badge>;
    case "completed":
      return <Badge variant="success"><CheckCircle className="w-3 h-3 mr-1" /> Completed</Badge>;
    case "failed":
      return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" /> Failed</Badge>;
    case "partial":
      return <Badge variant="warning"><AlertCircle className="w-3 h-3 mr-1" /> Partial</Badge>;
    case "skipped":
      return <Badge variant="secondary">Skipped</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

function AnalysisForm({ onStart }: { onStart: (request: AnalysisCreateRequest) => void }) {
  const [githubUrl, setGithubUrl] = useState("");
  const [dockerhubImage, setDockerhubImage] = useState("");
  const [authorization, setAuthorization] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!githubUrl && !dockerhubImage) {
      newErrors.general = "At least one of GitHub URL or DockerHub image is required";
    }
    if (githubUrl && !/^https?:\/\/github\.com\/[\w-]+\/[\w.-]+/.test(githubUrl)) {
      newErrors.githubUrl = "Invalid GitHub URL format (expected: https://github.com/owner/repository)";
    }
    if (dockerhubImage && !/^([\w-]+\/[\w.-]+|https:\/\/hub\.docker\.com\/r\/[\w-]+\/[\w.-]+)(:\w+)?$/.test(dockerhubImage)) {
      newErrors.dockerhubImage = "Invalid DockerHub image format (expected: owner/image:tag or https://hub.docker.com/r/owner/image)";
    }
    if (!authorization) {
      newErrors.authorization = "You must authorize the scan";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onStart({
      github_url: githubUrl || null,
      dockerhub_image: dockerhubImage || null,
      authorization: true,
    });
  };

  return (
    <Card className="p-6">
      <div className="space-y-2 mb-4">
        <h2 className="hk-label">New Security Analysis</h2>
        <p className="text-sm text-tx-secondary">
          Provide a GitHub repository and/or DockerHub image to run a real security analysis.
          Semgrep will scan the source code, Trivy will scan the container image, and CyberYukti
          will correlate and deduplicate findings into actionable incident clusters.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-tx-primary mb-2">
            <GitBranch className="w-4 h-4 inline mr-1" /> GitHub Repository
          </label>
          <Input
            type="url"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/owner/repository"
            error={errors.githubUrl}
          />
          <p className="text-xs text-tx-tertiary mt-1">Public repositories only. Format: https://github.com/owner/repository</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-tx-primary mb-2">
            <Container className="w-4 h-4 inline mr-1" /> DockerHub Image
          </label>
          <Input
            type="text"
            value={dockerhubImage}
            onChange={(e) => setDockerhubImage(e.target.value)}
            placeholder="owner/image:tag or https://hub.docker.com/r/owner/image"
            error={errors.dockerhubImage}
          />
          <p className="text-xs text-tx-tertiary mt-1">Public images only. Format: owner/image:tag or https://hub.docker.com/r/owner/image</p>
        </div>

        {errors.general && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-sm">
            {errors.general}
          </div>
        )}

        <div className="flex items-start gap-3 p-4 rounded-sm border border-line bg-graphite">
          <input
            type="checkbox"
            id="authorization"
            checked={authorization}
            onChange={(e) => setAuthorization(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-line bg-graphite-deep text-accent focus:ring-accent"
          />
          <label htmlFor="authorization" className="text-sm text-tx-primary leading-relaxed">
            <strong>I authorize CyberYukti to scan these resources.</strong>
            <br />
            The scan will: clone/read the GitHub repository, run SAST analysis using Semgrep,
            pull/analyze the Docker image, run container/image analysis using Trivy, collect
            complete scanner output, normalize findings, deduplicate findings, correlate related
            findings, generate incident clusters, and store analysis artifacts.
          </label>
        </div>

<Button type="submit" disabled={!authorization || (!githubUrl && !dockerhubImage)} className="w-full">
        <Play className="w-4 h-4 mr-2" /> Start Analysis
      </Button>
      </form>
    </Card>
  );
}

function StageRow({ stage, status, logs }: { stage: typeof STAGE_ORDER[0]; status: AnalysisStatus | ScannerStatus | undefined; logs?: StageLogInfo | null }) {

  return (
    <div className="flex items-center gap-3 p-3 rounded-sm border border-line bg-graphite transition-colors">
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-graphite-deep border border-line">
        {stage.icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-tx-primary truncate">{stage.label}</p>
        {logs && (
          <p className="text-xs text-tx-tertiary truncate">
            {logs.findings_count !== undefined && `Findings: ${logs.findings_count}`}
            {logs.duration_seconds != null && ` · Duration: ${logs.duration_seconds.toFixed(1)}s`}
            {logs.error && ` · Error: ${logs.error}`}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {logs?.raw_output_path && (
          <Button variant="ghost" size="sm" className="text-tx-secondary hover:text-tx-primary">
            <Eye className="w-4 h-4" />
          </Button>
        )}
        {getStatusBadge(status)}
      </div>
    </div>
  );
}

function LogViewer({ title, content, emptyMessage = "No logs available" }: { title: string; content?: string; emptyMessage?: string }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!content) {
    return (
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="hk-label">{title}</h3>
        </div>
        <p className="text-tx-tertiary text-sm">{emptyMessage}</p>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="hk-label">{title}</h3>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? <CheckCircle className="w-4 h-4" /> : <Download className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>
      {expanded && (
        <div className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
          <pre>{content}</pre>
        </div>
      )}
    </Card>
  );
}

function FindingRow({ finding }: { finding: CanonicalFindingResponse }) {
  const severityColors: Record<string, string> = {
    CRITICAL: "text-red-400",
    HIGH: "text-orange-400",
    MEDIUM: "text-amber-400",
    LOW: "text-green-400",
    INFO: "text-blue-400",
    UNKNOWN: "text-tx-tertiary",
  };

  return (
    <tr className="border-b border-line hover:bg-graphite-deep/50">
      <td className="px-3 py-2 font-mono text-xs text-tx-secondary">{finding.finding_id}</td>
      <td className="px-3 py-2 text-sm text-tx-primary truncate max-w-xs">{finding.title}</td>
      <td className="px-3 py-2">
        <Badge variant="secondary" className={severityColors[finding.raw_severity] || ""}>
          {finding.raw_severity}
        </Badge>
      </td>
      <td className="px-3 py-2 text-sm text-tx-secondary">{finding.tool_name}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary font-mono">{finding.scan_type}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary truncate max-w-xs">{finding.file_path || finding.http_endpoint || finding.package_name || "-"}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{finding.cve_id || "-"}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{finding.cwe_ids?.join(", ") || "-"}</td>
    </tr>
  );
}

interface AnalysisClusterSummary {
  cluster_id: string;
  title: string;
  primary_cve?: string | null;
  root_cause_cwe?: string | null;
  target_asset?: string | null;
  affected_component?: string | null;
  raw_findings_count?: number;
  participating_tools?: string[];
}

function ClusterRow({ cluster }: { cluster: AnalysisClusterSummary }) {
  return (
    <tr className="border-b border-line hover:bg-graphite-deep/50">
      <td className="px-3 py-2 font-mono text-xs text-tx-secondary">{cluster.cluster_id}</td>
      <td className="px-3 py-2 text-sm text-tx-primary">{cluster.title}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.primary_cve || "N/A"}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.root_cause_cwe || "N/A"}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.target_asset}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.affected_component}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.raw_findings_count}</td>
      <td className="px-3 py-2 text-sm text-tx-tertiary">{cluster.participating_tools?.join(", ") || "-"}</td>
    </tr>
  );
}

function AnalysisDetail({ analysisId }: { analysisId: string }) {
  const [status, setStatus] = useState<AnalysisStatusResponse | null>(null);
  const [logs, setLogs] = useState<AnalysisLogsResponse | null>(null);
  const [findings, setFindings] = useState<AnalysisFindingsResponse | null>(null);
  const [clusters, setClusters] = useState<AnalysisClustersResponse | null>(null);
  const [report, setReport] = useState<AnalysisReportResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "logs" | "findings" | "clusters" | "report">("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const provider = getProvider();

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusRes, logsRes, findingsRes, clustersRes, reportRes] = await Promise.all([
        provider.getAnalysisStatus(analysisId),
        provider.getAnalysisLogs(analysisId),
        provider.getAnalysisFindings(analysisId).catch(() => null),
        provider.getAnalysisClusters(analysisId).catch(() => null),
        provider.getAnalysisReport(analysisId).catch(() => null),
      ]);
      setStatus(statusRes);
      setLogs(logsRes);
      setFindings(findingsRes);
      setClusters(clustersRes);
      setReport(reportRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analysis");
    } finally {
      setLoading(false);
    }
  }, [analysisId, provider]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 3000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (loading && !status) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-96" />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="rounded-sm border border-line bg-graphite py-16 text-center">
          <h2 className="hk-label">Failed to load analysis</h2>
          <p className="mt-2 text-sm text-tx-secondary">{error}</p>
          <Button onClick={fetchAll} className="mt-5">Retry</Button>
        </div>
      </div>
    );
  }

  const isCompleted = status?.status === "completed" || status?.status === "partial" || status?.status === "failed";

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-5 py-6 lg:px-8">
      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="hk-label">Analysis {status?.analysis_id}</h2>
            <p className="text-sm text-tx-secondary">
              GitHub: {status?.github_url || "—"} · DockerHub: {status?.dockerhub_image || "—"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {getStatusBadge(status?.status)}
            {isCompleted && (
              <Button variant="secondary" size="sm" onClick={() => router.push("/analysis")}>
                New Analysis
              </Button>
            )}
          </div>
        </div>
      </section>

      <div className="flex gap-2 border-b border-line mb-4">
        {[
          { id: "overview", label: "Overview", icon: <FileText className="w-4 h-4" /> },
          { id: "logs", label: "Scanner Logs", icon: <Terminal className="w-4 h-4" /> },
          { id: "findings", label: "Findings", icon: <Search className="w-4 h-4" /> },
          { id: "clusters", label: "Clusters", icon: <GitBranch className="w-4 h-4" /> },
          { id: "report", label: "Full Report", icon: <FileText className="w-4 h-4" /> },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "primary" : "ghost"}
            className="gap-2"
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
          >
            {tab.icon} {tab.label}
          </Button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4">
              <p className="text-xs text-tx-tertiary uppercase tracking-wider">Semgrep</p>
              <p className="text-2xl font-bold text-tx-primary">{logs?.semgrep?.findings_count || 0}</p>
              <p className="text-xs text-tx-tertiary">Findings</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-tx-tertiary uppercase tracking-wider">Trivy</p>
              <p className="text-2xl font-bold text-tx-primary">{logs?.trivy?.findings_count || 0}</p>
              <p className="text-xs text-tx-tertiary">Findings</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-tx-tertiary uppercase tracking-wider">Total Findings</p>
              <p className="text-2xl font-bold text-tx-primary">{findings?.total_findings || 0}</p>
              <p className="text-xs text-tx-tertiary">Normalized</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-tx-tertiary uppercase tracking-wider">Clusters</p>
              <p className="text-2xl font-bold text-tx-primary">{clusters?.total_clusters || 0}</p>
              <p className="text-xs text-tx-tertiary">Incidents</p>
            </Card>
          </div>

          <Card className="p-4">
            <h3 className="hk-label mb-3">Pipeline Progress</h3>
            <div className="space-y-2">
              {STAGE_ORDER.map((stage) => (
                <StageRow
                  key={stage.key}
                  stage={stage}
                  status={status?.progress?.[stage.key] as AnalysisStatus | ScannerStatus | undefined}
                  logs={
                    stage.key === "semgrep" ? logs?.semgrep :
                    stage.key === "trivy" ? logs?.trivy :
                    stage.key === "github_acquisition" ? logs?.github_acquisition :
                    stage.key === "docker_pull" ? logs?.docker_pull :
                    logs?.pipeline
                  }
                />
              ))}
            </div>
          </Card>

          {(status?.status === "failed" || status?.status === "partial") && status?.error && (
            <Card className="p-4 border-destructive/50 bg-destructive/5">
              <h3 className="hk-label text-destructive mb-2">Analysis Error</h3>
              <p className="text-sm text-tx-secondary">{status.error}</p>
            </Card>
          )}
        </div>
      )}

      {activeTab === "logs" && logs && (
        <div className="space-y-4">
          {logs.github_acquisition && (
            <LogViewer
              title="GitHub Acquisition"
              content={logs.github_acquisition.stdout + "\n" + logs.github_acquisition.stderr}
            />
          )}
          {logs.semgrep && (
            <LogViewer
              title="Semgrep SAST Scan"
              content={logs.semgrep.stdout + "\n" + logs.semgrep.stderr}
            />
          )}
          {logs.docker_pull && (
            <LogViewer
              title="Docker Image Pull"
              content={logs.docker_pull.stdout + "\n" + logs.docker_pull.stderr}
            />
          )}
          {logs.trivy && (
            <LogViewer
              title="Trivy Image Scan"
              content={logs.trivy.stdout + "\n" + logs.trivy.stderr}
            />
          )}
          {logs.pipeline && (
            <LogViewer
              title="Pipeline Processing"
              content={JSON.stringify(logs.pipeline, null, 2)}
            />
          )}
        </div>
      )}

      {activeTab === "findings" && findings && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="hk-label">Normalized Findings ({findings.total_findings})</h3>
            <div className="flex gap-2 text-sm text-tx-tertiary">
              <span>Semgrep: {findings.semgrep_findings}</span>
              <span>Trivy: {findings.trivy_findings}</span>
            </div>
          </div>
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-line bg-graphite text-left text-xs font-medium text-tx-tertiary uppercase tracking-wider">
                    <th className="px-3 py-2">ID</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Severity</th>
                    <th className="px-3 py-2">Tool</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Location</th>
                    <th className="px-3 py-2">CVE</th>
                    <th className="px-3 py-2">CWEs</th>
                  </tr>
                </thead>
                <tbody>
                  {findings.findings.slice(0, 100).map((f) => (
                    <FindingRow key={f.finding_id} finding={f} />
                  ))}
                  {findings.findings.length > 100 && (
                    <tr>
                      <td colSpan={8} className="px-3 py-2 text-center text-tx-tertiary">
                        Showing 100 of {findings.findings.length} findings
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {activeTab === "clusters" && clusters && (
        <div className="space-y-4">
          <h3 className="hk-label">Incident Clusters ({clusters.total_clusters})</h3>
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-line bg-graphite text-left text-xs font-medium text-tx-tertiary uppercase tracking-wider">
                    <th className="px-3 py-2">Cluster ID</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Primary CVE</th>
                    <th className="px-3 py-2">Root CWE</th>
                    <th className="px-3 py-2">Target Asset</th>
                    <th className="px-3 py-2">Component</th>
                    <th className="px-3 py-2">Findings</th>
                    <th className="px-3 py-2">Tools</th>
                  </tr>
                </thead>
                <tbody>
                  {clusters.clusters.map((c, i) => (
                    <ClusterRow key={(c as unknown as AnalysisClusterSummary).cluster_id ?? `cluster-${i}`} cluster={c as unknown as AnalysisClusterSummary} />
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {activeTab === "report" && report && (
        <div className="space-y-6">
          <Card className="p-4">
            <h3 className="hk-label mb-3">Analysis Summary</h3>
            <pre className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
              {JSON.stringify(report.summary, null, 2)}
            </pre>
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="p-4">
              <h3 className="hk-label mb-3">Scanner Summary</h3>
              <pre className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
                {JSON.stringify(report.scanner_summary, null, 2)}
              </pre>
            </Card>
            <Card className="p-4">
              <h3 className="hk-label mb-3">Deduplication Summary</h3>
              <pre className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
                {JSON.stringify(report.deduplication_summary, null, 2)}
              </pre>
            </Card>
            <Card className="p-4">
              <h3 className="hk-label mb-3">Correlation Summary</h3>
              <pre className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
                {JSON.stringify(report.correlation_summary, null, 2)}
              </pre>
            </Card>
            <Card className="p-4 md:col-span-2">
              <h3 className="hk-label mb-3">Incident Clusters</h3>
              <pre className="font-mono text-xs bg-graphite-deep border border-line rounded-sm p-3 max-h-96 overflow-auto text-tx-secondary">
                {JSON.stringify(report.incident_clusters, null, 2)}
              </pre>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function AnalysisPageContent() {
  const searchParams = useSearchParams();
  const analysisId = searchParams.get("id");
  const router = useRouter();

  const handleStart = async (request: AnalysisCreateRequest) => {
    const provider = getProvider();
    try {
      const res = await provider.createAnalysis(request);
      router.push(`/analysis?id=${res.analysis_id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to start analysis");
    }
  };

  return (
    <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
      <section className="space-y-2 mb-6">
        <h2 className="hk-label">CyberYukti / Security Analysis</h2>
        <p className="text-xl font-semibold tracking-tight text-tx-primary">
          Real-time GitHub + DockerHub vulnerability analysis pipeline
        </p>
      </section>

      {analysisId ? (
        <AnalysisDetail analysisId={analysisId} />
      ) : (
        <AnalysisForm onStart={handleStart} />
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="space-y-6">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    }>
      <AnalysisPageContent />
    </Suspense>
  );
}
