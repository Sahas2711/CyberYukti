"use client";

import { useState } from "react";
import { Badge } from "@/components/shared/Badge";
import { getProvider } from "@/lib/providers";
import type { ApprovalState, AuditEvent } from "@/lib/api/types";

interface Props {
  caseId: string;
  approval: ApprovalState;
  onAction: () => void;
  audit?: AuditEvent[];
}

const approvalVariantMap: Record<
  string,
  "pending" | "approved" | "rejected" | "overridden"
> = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
  OVERRIDDEN: "overridden",
};

const PRIORITIES = ["P1", "P2", "P3", "P4"] as const;

const buttonBase =
  "inline-flex items-center justify-center gap-2 rounded-sm border px-3 py-[7px] text-[11px] font-semibold uppercase tracking-wider transition-colors disabled:cursor-not-allowed disabled:opacity-40";

function overrideTransition(audit?: AuditEvent[]) {
  if (!Array.isArray(audit)) return null;
  const last = [...audit].reverse().find((e) => e.action === "override");
  if (!last) return null;
  const metadata = last.metadata as { old_priority?: string; new_priority?: string };
  return {
    from: metadata?.old_priority ?? "",
    to: metadata?.new_priority ?? "",
  };
}

export function ApprovalControls({ caseId, approval, onAction, audit }: Props) {
  const [modal, setModal] = useState<null | "reject" | "override">(null);
  const [reason, setReason] = useState("");
  const [priority, setPriority] = useState<"P1" | "P2" | "P3" | "P4">("P2");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const decided = approval ? approval.status !== "PENDING" : true;
  const transition = approval?.status === "OVERRIDDEN" ? overrideTransition(audit) : null;

  function resetModal() {
    setModal(null);
    setReason("");
    setPriority("P2");
    setConfirming(false);
    setError(null);
  }

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      onAction();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  function handleApproveClick() {
    if (!confirming) {
      setConfirming(true);
      resetModal();
      return;
    }
    setConfirming(false);
    void run(() => getProvider().approveCase(caseId, ""));
  }

  function handleReject() {
    const trimmed = reason.trim();
    if (!trimmed) return;
    resetModal();
    void run(() => getProvider().rejectCase(caseId, trimmed));
  }

  function handleOverride() {
    const trimmed = reason.trim();
    if (!trimmed) return;
    resetModal();
    void run(() => getProvider().overrideCase(caseId, priority, trimmed));
  }

  function openModal(kind: "reject" | "override") {
    setConfirming(false);
    setError(null);
    setReason("");
    setModal(kind);
  }

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-3">
        <h2 className="hk-label">Analyst Decision</h2>
        {approval && (
          <Badge variant={approvalVariantMap[approval.status]}>
            {approval.status}
          </Badge>
        )}
      </header>

      <div className="p-4">
        {!decided && (
          <p className="text-[11px] text-tx-tertiary">
            This case has not been decided. Approve it as actionable, reject it as a
            false positive, or override the deterministic priority.
          </p>
        )}

        {decided && approval && (
          <div className="space-y-2 text-xs">
            <p className="text-tx-secondary">
              Decided by{" "}
              <span className="font-mono text-tx-primary">
                {approval.decided_by ?? "—"}
              </span>{" "}
              at{" "}
              <span className="font-mono text-tx-secondary">
                {approval.decided_at
                  ? new Date(approval.decided_at).toLocaleString()
                  : "—"}
              </span>
            </p>

            {transition && (
              <div className="rounded-sm border border-violet-500/40 bg-violet-500/10 px-3 py-2">
                <p className="hk-label text-violet-400">Priority override</p>
                <p className="mt-1 font-mono text-xs text-tx-primary">
                  System {transition.from || "?"}
                  <span className="mx-1.5 text-tx-tertiary" aria-hidden="true">
                    →
                  </span>
                  Analyst {transition.to || "?"}
                </p>
              </div>
            )}

            {approval.reason && (
              <p className="text-tx-secondary">
                Reason:{" "}
                <span className="italic text-tx-primary">“{approval.reason}”</span>
              </p>
            )}
            <p className="pt-1 text-[11px] text-tx-tertiary">
              This case has already been decided.
            </p>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={decided || busy}
            onClick={handleApproveClick}
            className={`${buttonBase} ${
              confirming
                ? "border-emerald-300 bg-emerald-300 text-emerald-950 hover:bg-emerald-200"
                : "border-emerald-600 bg-emerald-600 text-emerald-50 hover:bg-emerald-500"
            }`}
          >
            {confirming ? "Click again to confirm" : "Approve case"}
          </button>
          <button
            type="button"
            disabled={decided || busy}
            onClick={() => openModal("reject")}
            className={`${buttonBase} border-red-700/70 bg-red-700/70 text-red-50 hover:bg-red-600`}
          >
            Reject
          </button>
          <button
            type="button"
            disabled={decided || busy}
            onClick={() => openModal("override")}
            className={`${buttonBase} border-line-strong bg-transparent text-tx-secondary hover:border-violet-500/50 hover:text-violet-300`}
          >
            Override
          </button>
        </div>

        {error && !modal && (
          <p className="mt-3 text-xs text-red-400">{error}</p>
        )}
      </div>

      {modal === "reject" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="reject-title"
            className="w-full max-w-md rounded-sm border border-line bg-graphite-raised p-5"
          >
            <h3 id="reject-title" className="hk-label text-red-400">
              Reject case
            </h3>
            <p className="mt-1 text-xs text-tx-secondary">
              Reason is required. Rejection records the case as a false positive in the
              audit trail.
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              placeholder="False positive — patched version installed."
              className="mt-3 w-full rounded-sm border border-line bg-graphite-deep px-2.5 py-2 text-sm text-tx-primary placeholder:text-tx-tertiary focus:border-accent focus:outline-none"
            />
            {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={resetModal}
                disabled={busy}
                className="rounded-sm border border-line px-3 py-2 text-xs font-medium text-tx-secondary transition-colors hover:text-tx-primary disabled:opacity-40"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!reason.trim() || busy}
                onClick={handleReject}
                className={`${buttonBase} border-red-700/70 bg-red-700/70 text-red-50 hover:bg-red-600`}
              >
                {busy ? "Rejecting..." : "Reject case"}
              </button>
            </div>
          </div>
        </div>
      )}

      {modal === "override" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="override-title"
            className="w-full max-w-md rounded-sm border border-line bg-graphite-raised p-5"
          >
            <h3 id="override-title" className="hk-label text-violet-400">
              Override case
            </h3>
            <p className="mt-1 text-xs text-tx-secondary">
              Select a new priority and provide a reason. The override and its rationale
              are recorded in the audit trail.
            </p>
            <div className="mt-4">
              <span className="hk-label mb-1.5 block">New priority</span>
              <div className="flex gap-2">
                {PRIORITIES.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    aria-pressed={priority === p}
                    className={`rounded-sm border px-3 py-1.5 font-mono text-sm font-semibold transition-colors ${
                      priority === p
                        ? "border-accent bg-accent-soft text-accent"
                        : "border-line-strong bg-graphite-deep text-tx-tertiary hover:border-line-strong"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              placeholder="Why is this override necessary?"
              className="mt-3 w-full rounded-sm border border-line bg-graphite-deep px-2.5 py-2 text-sm text-tx-primary placeholder:text-tx-tertiary focus:border-accent focus:outline-none"
            />
            {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={resetModal}
                disabled={busy}
                className="rounded-sm border border-line px-3 py-2 text-xs font-medium text-tx-secondary transition-colors hover:text-tx-primary disabled:opacity-40"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!reason.trim() || busy}
                onClick={handleOverride}
                className={`${buttonBase} border-violet-600 bg-violet-600 text-violet-50 hover:bg-violet-500`}
              >
                {busy ? "Overriding..." : "Override"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}