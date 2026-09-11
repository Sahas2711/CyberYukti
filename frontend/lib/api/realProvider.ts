import { apiFetch, ApiError } from "./client";
import type {
  TriageCase,
  AIAnalysis,
  AuditEvent,
  DashboardStats,
  IngestionCluster,
  IngestionSummary,
  AnalysisCreateRequest,
  AnalysisCreateResponse,
  AnalysisStatusResponse,
  AnalysisLogsResponse,
  AnalysisFindingsResponse,
  AnalysisClustersResponse,
  AnalysisReportResponse,
} from "./types";
import type { Provider } from "./mockProvider";

function describeError(err: unknown): Error {
  if (err instanceof ApiError) {
    if (err.status === 0 || err instanceof TypeError) {
      return new Error(
        "Cannot reach the CyberYukti API. Start the backend (see README), or set NEXT_PUBLIC_USE_MOCK=true for demo data."
      );
    }
    if (err.status === 404) {
      return new Error("Not found on the CyberYukti API.");
    }
    return new Error(err.message);
  }
  if (err instanceof TypeError) {
    return new Error(
      "Cannot reach the CyberYukti API. Start the backend (see README), or set NEXT_PUBLIC_USE_MOCK=true for demo data."
    );
  }
  return err instanceof Error ? err : new Error(String(err));
}

export function createRealProvider(): Provider {
  return {
    async listCases(): Promise<TriageCase[]> {
      try {
        return await apiFetch<TriageCase[]>("/api/cases");
      } catch (err) {
        throw describeError(err);
      }
    },

    async getCase(id: string): Promise<TriageCase> {
      try {
        return await apiFetch<TriageCase>(`/api/cases/${id}`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async analyzeCase(id: string): Promise<AIAnalysis> {
      try {
        return await apiFetch<AIAnalysis>(`/api/ai/analyze/${id}`, { method: "POST" });
      } catch (err) {
        throw describeError(err);
      }
    },

    async approveCase(id: string, reason: string): Promise<TriageCase> {
      try {
        await apiFetch<unknown>(`/api/cases/${id}/approve`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", reason }),
        });
        return this.getCase(id);
      } catch (err) {
        throw describeError(err);
      }
    },

    async rejectCase(id: string, reason: string): Promise<TriageCase> {
      try {
        await apiFetch<unknown>(`/api/cases/${id}/reject`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", reason }),
        });
        return this.getCase(id);
      } catch (err) {
        throw describeError(err);
      }
    },

    async overrideCase(id: string, newPriority: string, reason: string): Promise<TriageCase> {
      try {
        await apiFetch<unknown>(`/api/cases/${id}/override`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", override_priority: newPriority, reason }),
        });
        return this.getCase(id);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAudit(caseId: string): Promise<AuditEvent[]> {
      try {
        return await apiFetch<AuditEvent[]>(`/api/cases/${caseId}/audit`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getDashboardStats(): Promise<DashboardStats> {
      try {
        return await apiFetch<DashboardStats>("/api/dashboard/stats");
      } catch (err) {
        throw describeError(err);
      }
    },

    async getIngestion(): Promise<{
      summary: IngestionSummary | null;
      clusters: IngestionCluster[];
    }> {
      try {
        return await apiFetch<{
          summary: IngestionSummary | null;
          clusters: IngestionCluster[];
        }>("/api/v1/report");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return { summary: null, clusters: [] };
        }
        throw describeError(err);
      }
    },

    async createAnalysis(request: AnalysisCreateRequest): Promise<AnalysisCreateResponse> {
      try {
        return await apiFetch<AnalysisCreateResponse>("/api/analyses", {
          method: "POST",
          body: JSON.stringify(request),
        });
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
      try {
        return await apiFetch<AnalysisStatusResponse>(`/api/analyses/${analysisId}`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAnalysisLogs(analysisId: string): Promise<AnalysisLogsResponse> {
      try {
        return await apiFetch<AnalysisLogsResponse>(`/api/analyses/${analysisId}/logs`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAnalysisFindings(analysisId: string): Promise<AnalysisFindingsResponse> {
      try {
        return await apiFetch<AnalysisFindingsResponse>(`/api/analyses/${analysisId}/findings`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAnalysisClusters(analysisId: string): Promise<AnalysisClustersResponse> {
      try {
        return await apiFetch<AnalysisClustersResponse>(`/api/analyses/${analysisId}/clusters`);
      } catch (err) {
        throw describeError(err);
      }
    },

    async getAnalysisReport(analysisId: string): Promise<AnalysisReportResponse> {
      try {
        return await apiFetch<AnalysisReportResponse>(`/api/analyses/${analysisId}/report`);
      } catch (err) {
        throw describeError(err);
      }
    },
  };
}
