import { apiFetch } from "./client";
import type {
  AttestationReceipt,
  AttestationVerificationResult,
  RemediationPlaybook,
} from "./types";

export interface ChatMessagePayload {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  model: string;
  source: string;
}

export async function fetchCaseAttestation(caseId: string): Promise<AttestationReceipt> {
  return await apiFetch<AttestationReceipt>(`/api/cases/${caseId}/attestation`);
}

export async function verifyAttestationReceipt(
  receipt: Record<string, unknown>
): Promise<AttestationVerificationResult> {
  return await apiFetch<AttestationVerificationResult>("/api/cases/attestation/verify", {
    method: "POST",
    body: JSON.stringify(receipt),
  });
}

export async function fetchTop10Remediations(): Promise<RemediationPlaybook[]> {
  return await apiFetch<RemediationPlaybook[]>("/api/cases/remediation/top10");
}

export async function fetchCaseRemediation(caseId: string): Promise<RemediationPlaybook> {
  return await apiFetch<RemediationPlaybook>(`/api/cases/${caseId}/remediation`);
}

export async function sendAiChatMessage(
  message: string,
  caseId?: string,
  history?: ChatMessagePayload[]
): Promise<ChatResponse> {
  return await apiFetch<ChatResponse>("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      case_id: caseId || undefined,
      history: history || undefined,
    }),
  });
}
