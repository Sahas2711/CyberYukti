# Person 4 Integration Contracts

## Status: INITIAL (no Person 1–3 schemas observed)

All contracts below are **proposed**. Person 4 must reconcile with Persons 1–3 in Prompt 1 before coding. If their contracts differ, adapt via the typed layer — never silently rename.

---

## A. Inputs Person 4 Consumes

### From Person 1

```typescript
interface Finding {
  finding_id: string;
  cluster_id: string;
  scanner: string;
  scanner_rule_id?: string;
  cve?: string | null;
  cwe?: string | null;
  title: string;
  description?: string;         // UNTRUSTED
  asset: Asset;
  raw_evidence?: string;        // UNTRUSTED
  observed_at: string;          // ISO 8601
}

interface Cluster {
  cluster_id: string;
  finding_ids: string[];
  primary_finding_id: string;
  dedup_confidence: number;     // 0..1
  dedup_method: string;         // "hash" | "normalized" | "fuzzy" | "graph"
}

interface Asset {
  asset_id: string;
  hostname: string;
  environment: "production" | "staging" | "dev";
  internet_exposed: boolean;
  criticality: "critical" | "high" | "medium" | "low";
}
```

### From Person 2

```typescript
interface ValidationResult {
  cluster_id: string;
  status: "CONFIRMED" | "NOT_CONFIRMED" | "INCONCLUSIVE" | "STALE";
  confidence: number;           // 0..1
  observations: EvidenceObservation[];
  validated_at: string;
  validator_version: string;
}

interface EvidenceObservation {
  observation_id: string;
  type: "package_version" | "file_exists" | "endpoint_status" | "config_value";
  target: string;               // UNTRUSTED
  observed_value: string;       // UNTRUSTED
  expected_value?: string;
  method: string;               // "dpkg" | "stat" | "http_get"
}
```

### From Person 3

```typescript
interface PriorityResult {
  cluster_id: string;
  score: number;                // 0..100
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
```

---

## B. Person 4 Produces

```typescript
interface TriageCase {
  case_id: string;
  cluster_id: string;
  title: string;
  asset: Asset;
  sources: string[];
  finding_count: number;
  vulnerability: { cwe?: string; cve?: string };
  evidence: ValidationResult;
  threat_intelligence: {
    cvss?: number;
    epss?: number;
    kev?: boolean;
  };
  priority: PriorityResult;
  ai_analysis: AIAnalysis | null;
  approval: ApprovalState;
  audit: AuditEvent[];
}

interface AIAnalysis {
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

interface ApprovalState {
  status: "PENDING" | "APPROVED" | "REJECTED" | "OVERRIDDEN";
  decided_by?: string;
  decided_at?: string;
  override_priority?: "P1" | "P2" | "P3" | "P4";
  reason?: string;
}

interface ApprovalAction {
  action: "approve" | "reject" | "override";
  analyst_id: string;
  reason?: string;
  override_priority?: "P1" | "P2" | "P3" | "P4";
}

interface AuditEvent {
  event_id: string;
  case_id: string;
  timestamp: string;
  actor: "system" | "analyst" | "ai";
  actor_id?: string;
  action: string;
  previous_state?: object;
  new_state?: object;
  metadata?: object;
}
```

---

## C. HTTP Endpoints (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/cases` | List cases (filters: priority, status) |
| GET | `/api/cases/{case_id}` | Full case detail |
| POST | `/api/ai/analyze/{case_id}` | Trigger AI analysis (idempotent) |
| POST | `/api/cases/{case_id}/approve` | Approve |
| POST | `/api/cases/{case_id}/reject` | Reject |
| POST | `/api/cases/{case_id}/override` | Override priority |
| GET | `/api/cases/{case_id}/audit` | Audit trail |
| GET | `/api/dashboard/stats` | Aggregate counts |

---

## D. Conflict Log

| Field | Section D Proposal | Person 1–3 Actual | Status |
|---|---|---|---|
| (none yet) | — | — | Awaiting Person 1–3 commits |
