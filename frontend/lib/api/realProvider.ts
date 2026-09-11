import { apiFetch } from "./client";
import type {
  TriageCase,
  AIAnalysis,
  AuditEvent,
  DashboardStats,
} from "./types";
import type { Provider } from "./mockProvider";
import { createMockProvider } from "./mockProvider";

export function createRealProvider(): Provider {
  const mock = createMockProvider();

  return {
    async listCases(): Promise<TriageCase[]> {
      try {
        return await apiFetch<TriageCase[]>("/api/cases");
      } catch (err) {
        console.warn("[realProvider] listCases failed, falling back to mock:", err);
        return mock.listCases();
      }
    },

    async getCase(id: string): Promise<TriageCase> {
      try {
        return await apiFetch<TriageCase>(`/api/cases/${id}`);
      } catch (err) {
        console.warn(`[realProvider] getCase(${id}) failed, falling back to mock:`, err);
        return mock.getCase(id);
      }
    },

    async analyzeCase(id: string): Promise<AIAnalysis> {
      try {
        return await apiFetch<AIAnalysis>(`/api/ai/analyze/${id}`, { method: "POST" });
      } catch (err) {
        console.warn(`[realProvider] analyzeCase(${id}) failed, falling back to mock:`, err);
        return mock.analyzeCase(id);
      }
    },

    async approveCase(id: string, reason: string): Promise<TriageCase> {
      try {
        return await apiFetch<TriageCase>(`/api/cases/${id}/approve`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", reason }),
        });
      } catch (err) {
        console.warn(`[realProvider] approveCase(${id}) failed, falling back to mock:`, err);
        return mock.approveCase(id, reason);
      }
    },

    async rejectCase(id: string, reason: string): Promise<TriageCase> {
      try {
        return await apiFetch<TriageCase>(`/api/cases/${id}/reject`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", reason }),
        });
      } catch (err) {
        console.warn(`[realProvider] rejectCase(${id}) failed, falling back to mock:`, err);
        return mock.rejectCase(id, reason);
      }
    },

    async overrideCase(id: string, newPriority: string, reason: string): Promise<TriageCase> {
      try {
        return await apiFetch<TriageCase>(`/api/cases/${id}/override`, {
          method: "POST",
          body: JSON.stringify({ analyst_id: "analyst-1", override_priority: newPriority, reason }),
        });
      } catch (err) {
        console.warn(`[realProvider] overrideCase(${id}) failed, falling back to mock:`, err);
        return mock.overrideCase(id, newPriority, reason);
      }
    },

    async getAudit(caseId: string): Promise<AuditEvent[]> {
      try {
        return await apiFetch<AuditEvent[]>(`/api/cases/${caseId}/audit`);
      } catch (err) {
        console.warn(`[realProvider] getAudit(${caseId}) failed, falling back to mock:`, err);
        return mock.getAudit(caseId);
      }
    },

    async getDashboardStats(): Promise<DashboardStats> {
      try {
        return await apiFetch<DashboardStats>("/api/dashboard/stats");
      } catch (err) {
        console.warn("[realProvider] getDashboardStats failed, falling back to mock:", err);
        return mock.getDashboardStats();
      }
    },
  };
}
