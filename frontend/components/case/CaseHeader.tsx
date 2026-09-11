"use client";

import { useState } from "react";
import { Badge } from "@/components/shared/Badge";
import type { TriageCase } from "@/lib/api/types";
import { AttestationModal } from "@/components/case/AttestationModal";

interface Props {
  case: TriageCase;
}

const priorityVariantMap: Record<string, "p1" | "p2" | "p3" | "p4"> = {
  P1: "p1",
  P2: "p2",
  P3: "p3",
  P4: "p4",
};

const environmentColors: Record<string, string> = {
  production: "text-red-400",
  staging: "text-amber-400",
  dev: "text-sky-400",
};

const criticalityColors: Record<string, string> = {
  critical: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-green-400",
};

export function CaseHeader({ case: caseData }: Props) {
  const [isAttestationOpen, setIsAttestationOpen] = useState(false);

  if (!caseData) return null;

  const priorityLevel = caseData.priority?.level;
  const evidenceStatus = caseData.evidence?.status;
  const evidenceConfidence = Math.round(
    (typeof caseData.evidence?.confidence === "number"
      ? caseData.evidence.confidence
      : 0) * 100
  );
  const score =
    typeof caseData.priority?.score === "number" ? caseData.priority.score : null;
  const vulnRefs = [caseData.vulnerability?.cve, caseData.vulnerability?.cwe].filter(
    (r): r is string => Boolean(r)
  );

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <div className="flex flex-col gap-5 p-5 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <p className="font-mono text-xs text-tx-secondary">
              {caseData.case_id ?? "UNKNOWN"}
            </p>
            {caseData.cluster_id && (
              <>
                <span className="text-tx-tertiary" aria-hidden="true">
                  ·
                </span>
                <p className="font-mono text-[11px] text-tx-tertiary">
                  {caseData.cluster_id}
                </p>
              </>
            )}
          </div>
          <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-tx-primary">
            {caseData.title ?? "Untitled case"}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {priorityLevel && (
              <Badge variant={priorityVariantMap[priorityLevel] ?? "p4"}>
                {priorityLevel}
              </Badge>
            )}
            {score !== null && (
              <span className="font-mono text-sm font-semibold tabular-nums text-tx-primary">
                {score.toFixed(1)}
                <span className="text-tx-tertiary">/100</span>
              </span>
            )}
            {evidenceStatus && (
              <span className="font-mono text-xs tabular-nums text-tx-secondary">
                {evidenceStatus} · {evidenceConfidence}%
              </span>
            )}
            {vulnRefs.map((ref) => (
              <span
                key={ref}
                className="rounded-sm border border-line-strong bg-graphite-deep px-1.5 py-[3px] font-mono text-[11px] text-tx-secondary"
              >
                {ref}
              </span>
            ))}
          </div>
        </div>

        {/* Right side: Cost Burn Telemetry & Export Attestation */}
        <div className="flex flex-col items-start md:items-end gap-2.5 shrink-0">
          <div className="flex items-center gap-3 bg-graphite-deep/80 border border-line rounded-lg px-3 py-1.5 shadow-sm">
            <div className="text-left md:text-right">
              <span className="text-[10px] uppercase font-mono tracking-wider text-tx-tertiary block">
                Liability Burn
              </span>
              <span
                className={`font-mono text-xs font-bold ${
                  priorityLevel === "P1"
                    ? "text-red-400"
                    : priorityLevel === "P2"
                    ? "text-amber-400"
                    : "text-tx-secondary"
                }`}
              >
                {caseData.cost_burn?.formatted_daily || (priorityLevel === "P1" ? "$30,000/day" : "$10,800/day")}
              </span>
            </div>
            <span className="h-6 w-px bg-line" />
            <div className="text-left md:text-right">
              <span className="text-[10px] uppercase font-mono tracking-wider text-tx-tertiary block">
                Accrued Liability
              </span>
              <span className="font-mono text-xs font-semibold text-tx-secondary">
                {caseData.cost_burn?.formatted_accrued || "$45,000"}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsAttestationOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-400 border border-emerald-500/50 hover:border-emerald-400 rounded-lg font-semibold text-xs shadow-md shadow-emerald-950/30 transition-all active:scale-95"
          >
            <span>🛡️</span>
            <span>Export Audit Attestation</span>
            <span className="text-[10px] font-mono bg-emerald-900 px-1.5 py-0.5 rounded border border-emerald-500/30">
              SHA-256 Merkle
            </span>
          </button>
        </div>
      </div>

      <AttestationModal
        caseId={caseData.case_id}
        isOpen={isAttestationOpen}
        onClose={() => setIsAttestationOpen(false)}
      />

      <div className="border-t border-line px-5 py-3.5">
        <dl className="grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-4">
          <div>
            <dt className="hk-label">Hostname</dt>
            <dd className="mt-0.5 break-all font-mono text-xs text-tx-primary">
              {caseData.asset?.hostname ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="hk-label">Environment</dt>
            <dd
              className={`mt-0.5 text-xs font-medium uppercase tracking-wide ${
                environmentColors[caseData.asset?.environment ?? ""] ?? "text-tx-secondary"
              }`}
            >
              {caseData.asset?.environment ?? "unknown"}
            </dd>
          </div>
          <div>
            <dt className="hk-label">Exposure</dt>
            <dd className="mt-0.5 text-xs font-medium uppercase tracking-wide text-tx-primary">
              {caseData.asset?.internet_exposed ? "Internet exposed" : "Internal"}
            </dd>
          </div>
          <div>
            <dt className="hk-label">Asset criticality</dt>
            <dd
              className={`mt-0.5 text-xs font-medium uppercase tracking-wide ${
                criticalityColors[caseData.asset?.criticality ?? ""] ?? "text-tx-secondary"
              }`}
            >
              {caseData.asset?.criticality ?? "unknown"}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}