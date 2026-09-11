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
}
