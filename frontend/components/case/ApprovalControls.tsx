"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
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
  "inline-flex items-center justify-center gap-2 rounded-md border px-3.5 py-2 text-[11px] font-semibold uppercase tracking-wider transition-all disabled:cursor-not-allowed disabled:opacity-40 shadow-xs";

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
  const [modal, setModal] = useState<null | "approve" | "reject" | "override">(null);
  const [reason, setReason] = useState("");
  const [priority, setPriority] = useState<"P1" | "P2" | "P3" | "P4">("P2");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const decided = approval ? approval.status !== "PENDING" : true;
  const transition = approval?.status === "OVERRIDDEN" ? overrideTransition(audit) : null;

  function resetModal() {
    setModal(null);
    setReason("");
    setPriority("P2");
    setError(null);
  }

  async function run(action: () => Promise<unknown>, successMsg: string) {
    setBusy(true);
    setError(null);
    try {
      await action();
      onAction();
      setSuccessToast(successMsg);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  function handleApprove() {
    const trimmed = reason.trim() || "Verified exploitability in controlled environment. Approved for priority remediation.";
    resetModal();
    void run(() => getProvider().approveCase(caseId, trimmed), `Case ${caseId} successfully APPROVED`);
  }

  function handleReject() {
    const trimmed = reason.trim();
    if (!trimmed) return;
    resetModal();
    void run(() => getProvider().rejectCase(caseId, trimmed), `Case ${caseId} marked as FALSE POSITIVE / REJECTED`);
  }

  function handleOverride() {
    const trimmed = reason.trim();
    if (!trimmed) return;
    resetModal();
    void run(() => getProvider().overrideCase(caseId, priority, trimmed), `Case ${caseId} priority overridden to ${priority}`);
  }

  function openModal(kind: "approve" | "reject" | "override") {
    setError(null);
    if (kind === "approve") {
      setReason("Verified exploitability in controlled environment. Approved for priority remediation.");
    } else {
      setReason("");
    }
    setModal(kind);
  }

  return (
    <section className="rounded-xl border border-line bg-graphite transition-colors shadow-xs">
      <header className="flex items-center justify-between gap-2 border-b border-line px-5 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-sm">⚖️</span>
          <h2 className="hk-label font-bold">Analyst Decision</h2>
        </div>
        {approval && (
          <Badge variant={approvalVariantMap[approval.status]}>
            {approval.status}
          </Badge>
        )}
      </header>

      <div className="p-5">
        {successToast && (
          <div className="mb-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-3 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
            <span className="text-sm">✓</span>
            <span className="font-semibold">{successToast}</span>
          </div>
        )}

        {!decided && (
          <p className="text-xs leading-relaxed text-tx-secondary">
            This case is currently awaiting an analyst decision. Review the evidence findings, then approve for remediation, reject as a false positive, or override priority.
          </p>
        )}

        {decided && approval && (
          <div className="space-y-2.5 text-xs">
            <p className="text-tx-secondary">
              Decided by{" "}
              <span className="font-mono font-semibold text-tx-primary">
                {approval.decided_by ?? "analyst-1"}
              </span>{" "}
              at{" "}
              <span className="font-mono text-tx-secondary">
                {approval.decided_at
                  ? new Date(approval.decided_at).toLocaleString()
                  : "Just now"}
              </span>
            </p>

            {transition && (
              <div className="rounded-lg border border-violet-500/30 bg-violet-500/10 px-3.5 py-2.5">
                <p className="hk-label text-violet-600 dark:text-violet-400 font-bold">Priority override</p>
                <p className="mt-1 font-mono text-xs text-tx-primary">
                  System {transition.from || "?"}
                  <span className="mx-2 text-tx-tertiary" aria-hidden="true">
                    →
                  </span>
                  Analyst {transition.to || "?"}
                </p>
              </div>
            )}

            {approval.reason && (
              <div className="rounded-lg border border-line bg-graphite-raised p-3">
                <p className="hk-label text-[9.5px] mb-1">Analyst Rationale</p>
                <p className="italic text-tx-primary">“{approval.reason}”</p>
              </div>
            )}
            <p className="pt-1 text-[11px] text-tx-tertiary font-mono">
              Immutable audit receipt recorded in platform ledger.
            </p>
          </div>
        )}

        <div className="mt-5 flex flex-wrap gap-2.5">
          <button
            type="button"
            disabled={decided || busy}
            onClick={() => openModal("approve")}
            className={`${buttonBase} border-emerald-600 bg-emerald-600 text-white hover:bg-emerald-500 active:scale-98`}
          >
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span>Approve Case</span>
          </button>
          <button
            type="button"
            disabled={decided || busy}
            onClick={() => openModal("reject")}
            className={`${buttonBase} border-red-700/80 bg-red-700/80 text-white hover:bg-red-600 active:scale-98`}
          >
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>Reject (False Positive)</span>
          </button>
          <button
            type="button"
            disabled={decided || busy}
            onClick={() => openModal("override")}
            className={`${buttonBase} border-line-strong bg-graphite-raised text-tx-secondary hover:border-violet-500/60 hover:text-violet-500 dark:hover:text-violet-300 active:scale-98`}
          >
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
            </svg>
            <span>Override Priority</span>
          </button>
        </div>

        {error && !modal && (
          <p className="mt-3 text-xs text-red-500 font-medium">{error}</p>
        )}
      </div>

      {/* APPROVE MODAL */}
      {modal === "approve" && mounted && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in">
          <div
            role="dialog"
            aria-modal="true"
            className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-emerald-500/40 bg-white dark:bg-slate-900 p-6 shadow-2xl"
          >
            <div className="flex items-center space-x-2.5 text-emerald-600 dark:text-emerald-400 mb-2">
              <span className="text-xl">🛡️</span>
              <h3 className="text-sm font-bold tracking-wide uppercase">
                Approve Case for Remediation
              </h3>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Case <strong className="font-mono text-slate-900 dark:text-white">{caseId}</strong> will be marked as <strong className="text-emerald-600 dark:text-emerald-400">APPROVED</strong>. An immutable cryptographic audit record will be signed with your analyst session.
            </p>
            <div className="mt-4">
              <label className="block text-[11px] font-mono uppercase text-slate-500 dark:text-slate-400 mb-1">
                Approval Rationale / Notes (Optional)
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                placeholder="Verified exploitability in production sandbox, proceeding with remediation."
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 px-3 py-2 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none transition-colors"
              />
            </div>
            {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
            <div className="mt-5 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={resetModal}
                disabled={busy}
                className="rounded-xl border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={handleApprove}
                className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-md transition-all flex items-center gap-1.5"
              >
                {busy ? "Approving..." : "Confirm Approval"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* REJECT MODAL */}
      {modal === "reject" && mounted && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="reject-title"
            className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-red-500/40 bg-white dark:bg-slate-900 p-6 shadow-2xl"
          >
            <div className="flex items-center space-x-2.5 text-red-600 dark:text-red-400 mb-2">
              <span className="text-xl">⚠️</span>
              <h3 id="reject-title" className="text-sm font-bold tracking-wide uppercase">
                Reject Case (False Positive)
              </h3>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Reason is required. Rejection records the case as a false positive in the cryptographic audit trail.
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              placeholder="False positive — patched version installed or compensating control active."
              className="mt-3.5 w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 px-3 py-2 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-red-500 focus:outline-none transition-colors"
            />
            {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
            <div className="mt-5 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={resetModal}
                disabled={busy}
                className="rounded-xl border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!reason.trim() || busy}
                onClick={handleReject}
                className="rounded-xl bg-red-600 hover:bg-red-500 px-4 py-2 text-xs font-semibold text-white shadow-md transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {busy ? "Rejecting..." : "Confirm Rejection"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* OVERRIDE MODAL */}
      {modal === "override" && mounted && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="override-title"
            className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-violet-500/40 bg-white dark:bg-slate-900 p-6 shadow-2xl"
          >
            <div className="flex items-center space-x-2.5 text-violet-600 dark:text-violet-400 mb-2">
              <span className="text-xl">🎛️</span>
              <h3 id="override-title" className="text-sm font-bold tracking-wide uppercase">
                Override Case Priority
              </h3>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Select a new priority level and provide justification. Both are recorded permanently in the tamper-evident audit trail.
            </p>
            <div className="mt-4">
              <span className="hk-label mb-2 block font-bold">New Priority Target</span>
              <div className="flex gap-2">
                {PRIORITIES.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    aria-pressed={priority === p}
                    className={`flex-1 rounded-lg border py-2 font-mono text-xs font-bold transition-all ${
                      priority === p
                        ? "border-violet-500 bg-violet-500/15 text-violet-600 dark:text-violet-300 ring-2 ring-violet-500/30"
                        : "border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 hover:border-violet-400"
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
              rows={3}
              placeholder="Why is this override necessary? (e.g. Compensating WAF rule deployed)"
              className="mt-3.5 w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 px-3 py-2 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-violet-500 focus:outline-none transition-colors"
            />
            {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
            <div className="mt-5 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={resetModal}
                disabled={busy}
                className="rounded-xl border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!reason.trim() || busy}
                onClick={handleOverride}
                className="rounded-xl bg-violet-600 hover:bg-violet-500 px-4 py-2 text-xs font-semibold text-white shadow-md transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {busy ? "Overriding..." : "Confirm Override"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </section>
  );
}