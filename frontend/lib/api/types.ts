export interface Asset {
  asset_id: string;
  hostname: string;
  environment: "production" | "staging" | "dev";
  internet_exposed: boolean;
  criticality: "critical" | "high" | "medium" | "low";
}

export interface EvidenceObservation {
  observation_id: string;
  type: "package_version" | "file_exists" | "endpoint_status" | "config_value";
  target: string;
  observed_value: string;
  expected_value?: string;
  method: string;
}

export interface ValidationResult {
  cluster_id: string;
  status: "CONFIRMED" | "NOT_CONFIRMED" | "INCONCLUSIVE" | "STALE";
  confidence: number;
  observations: EvidenceObservation[];
  validated_at: string;
  validator_version: string;
}

export interface PriorityResult {
  cluster_id: string;
  score: number;
  level: "P1" | "P2" | "P3" | "P4";
  factors: {
    cvss?: number;
    epss?: number;
    kev?: boolean;
    asset_criticality?: string;
    internet_exposed?: boolean;
    evidence_confidence?: number;
  };
  formula_version: string;
}

export interface AIAnalysis {
  summary: string;
  why_it_matters: string;
  evidence_summary: string;
  priority_explanation: string;
  investigation_questions: string[];
  recommended_remediation: string[];
  confidence_notes: string[];
  limitations: string[];
  model: string;
  generated_at: string;
  grounded_on: string[];
}

export interface ApprovalState {
  status: "PENDING" | "APPROVED" | "REJECTED" | "OVERRIDDEN";
  decided_by?: string;
  decided_at?: string;
  override_priority?: "P1" | "P2" | "P3" | "P4";
  reason?: string;
}

export interface AuditEvent {
  event_id: string;
  case_id: string;
  timestamp: string;
  actor: "system" | "analyst" | "ai";
  actor_id?: string;
  action: string;
  previous_state?: Record<string, unknown>;
  new_state?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  prev_hash?: string;
}

export interface TriageCase {
  case_id: string;
  cluster_id: string;
  title: string;
  asset: Asset;
  sources: string[];
  finding_count: number;
  vulnerability: { cwe?: string; cve?: string };
  evidence: ValidationResult;
  threat_intelligence: { cvss?: number; epss?: number; kev?: boolean };
  priority: PriorityResult;
  ai_analysis: AIAnalysis | null;
  approval: ApprovalState;
  audit: AuditEvent[];
}

export interface DashboardStats {
  total_findings: number;
  unique_clusters: number;
  confirmed: number;
  not_confirmed: number;
  inconclusive: number;
  p1: number;
  p2: number;
  p3: number;
  p4: number;
  ingestion?: IngestionSummary;
}

export interface IngestionSummary {
  total_raw_findings: number;
  total_clusters: number;
  noise_reduction_percentage: number;
  breakdown_by_tool: Record<string, number>;
}

export interface IngestionCluster {
  cluster_id: string;
  title: string;
  primary_cve?: string | null;
  root_cause_cwe?: string | null;
  target_asset: string;
  affected_component: string;
  normalized_route?: string | null;
  raw_findings_count: number;
  participating_tools: string[];
  underlying_finding_ids: string[];
  representative_finding: {
    finding_id: string;
    tool_name: string;
    scan_type: string;
    title: string;
    description: string;
    raw_severity: string;
    target_asset: string;
    package_name?: string | null;
    installed_version?: string | null;
    fixed_version?: string | null;
  };
}

// Analysis types
export type AnalysisStatus =
  | "queued"
  | "running"
  | "github_clone"
  | "semgrep_scan"
  | "docker_pull"
  | "trivy_scan"
  | "normalizing"
  | "deduplicating"
  | "correlating"
  | "completed"
  | "failed"
  | "partial";

export type ScannerStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface GitHubRepoInfo {
  url: string;
  owner: string;
  name: string;
  full_name: string;
  commit_sha?: string | null;
  branch?: string | null;
  default_branch?: string | null;
  size_kb?: number | null;
}

export interface DockerImageInfo {
  image_ref: string;
  repository: string;
  tag: string;
  digest?: string | null;
  size_bytes?: number | null;
  architecture?: string | null;
  os?: string | null;
}

export interface ScannerExecution {
  scanner: string;
  version?: string | null;
  status: ScannerStatus;
  command: string[];
  stdout: string;
  stderr: string;
  exit_code?: number | null;
  start_time?: string | null;
  end_time?: string | null;
  duration_seconds?: number | null;
  raw_output_path?: string | null;
  findings_count: number;
  error?: string | null;
}

export interface GitHubAcquisition {
  clone_command: string[];
  stdout: string;
  stderr: string;
  exit_code?: number | null;
  start_time?: string | null;
  end_time?: string | null;
  duration_seconds?: number | null;
  repository?: GitHubRepoInfo | null;
  error?: string | null;
}

export interface DockerAcquisition {
  pull_command: string[];
  stdout: string;
  stderr: string;
  exit_code?: number | null;
  start_time?: string | null;
  end_time?: string | null;
  duration_seconds?: number | null;
  image?: DockerImageInfo | null;
  error?: string | null;
}

export interface PipelineProcessing {
  canonical_findings_count: number;
  exact_duplicates_removed: number;
  triple_tuple_duplicates_removed: number;
  cross_tool_correlations: number;
  incident_clusters_created: number;
  start_time?: string | null;
  end_time?: string | null;
  duration_seconds?: number | null;
  error?: string | null;
}

export interface AnalysisArtifacts {
  metadata_path?: string | null;
  github_acquisition_path?: string | null;
  semgrep_stdout_path?: string | null;
  semgrep_stderr_path?: string | null;
  semgrep_raw_path?: string | null;
  docker_pull_path?: string | null;
  trivy_stdout_path?: string | null;
  trivy_stderr_path?: string | null;
  trivy_raw_path?: string | null;
  canonical_findings_path?: string | null;
  deduplication_path?: string | null;
  correlations_path?: string | null;
  incident_clusters_path?: string | null;
  analysis_summary_path?: string | null;
  final_report_path?: string | null;
}

export interface AnalysisMetadata {
  analysis_id: string;
  status: AnalysisStatus;
  github_url?: string | null;
  dockerhub_image?: string | null;
  authorization: boolean;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  github?: GitHubAcquisition | null;
  docker?: DockerAcquisition | null;
  semgrep?: ScannerExecution | null;
  trivy?: ScannerExecution | null;
  pipeline?: PipelineProcessing | null;
  artifacts?: AnalysisArtifacts | null;
  error?: string | null;
  partial_results: boolean;
}

export interface AnalysisCreateRequest {
  github_url?: string | null;
  dockerhub_image?: string | null;
  authorization: boolean;
}

export interface AnalysisCreateResponse {
  analysis_id: string;
  status: AnalysisStatus;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: AnalysisStatus;
  github_url?: string | null;
  dockerhub_image?: string | null;
  progress: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  error?: string | null;
  partial_results: boolean;
}

export interface AnalysisLogsResponse {
  analysis_id: string;
  github_acquisition?: GitHubAcquisition | null;
  semgrep?: ScannerExecution | null;
  docker_pull?: DockerAcquisition | null;
  trivy?: ScannerExecution | null;
  pipeline?: PipelineProcessing | null;
}

export interface CanonicalFindingResponse {
  finding_id: string;
  tool_name: string;
  scan_type: string;
  title: string;
  description: string;
  cve_id?: string | null;
  cwe_ids: string[];
  raw_severity: string;
  target_asset: string;
  file_path?: string | null;
  line_number?: number | null;
  http_endpoint?: string | null;
  http_method?: string | null;
  package_name?: string | null;
  installed_version?: string | null;
  fixed_version?: string | null;
}

export interface AnalysisFindingsResponse {
  analysis_id: string;
  total_findings: number;
  semgrep_findings: number;
  trivy_findings: number;
  findings: CanonicalFindingResponse[];
}

export interface AnalysisClustersResponse {
  analysis_id: string;
  total_clusters: number;
  clusters: Record<string, unknown>[];
}

export interface AnalysisReportResponse {
  analysis_id: string;
  metadata: AnalysisMetadata;
  summary: Record<string, unknown>;
  scanner_summary: Record<string, unknown>;
  finding_summary: Record<string, unknown>;
  deduplication_summary: Record<string, unknown>;
  correlation_summary: Record<string, unknown>;
  incident_clusters: Record<string, unknown>[];
}
