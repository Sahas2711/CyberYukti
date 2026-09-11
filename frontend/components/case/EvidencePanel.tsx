"use client";

import { useState } from "react";
import type { ValidationResult } from "@/lib/api/types";
import { ValidationBadge } from "./ValidationBadge";
import { Tooltip } from "@/components/shared/Tooltip";

interface Props {
  evidence: ValidationResult;
  onValidate?: (targetOverride?: string) => Promise<void>;
  validating?: boolean;
}

const TRUNCATE_AT = 200;
const CONFIDENCE_TOOLTIP =
  "Confidence reflects validator agreement across multiple probes. 0.9+ = high confidence.";

const OBSERVATION_TYPES: Record<string, string> = {
  package_version: "Package Version",
  file_exists: "File Exists",
  endpoint_status: "Endpoint Status",
  config_value: "Config Value",
};

function isSuspicious(value: string): boolean {
  if (typeof value !== "string") return false;
  return /IGNORE ALL PREVIOUS|DISREGARD INSTRUCTIONS|>>?\s*system prompt|(^|\s)DAN(\s|\.|$)|rm\s+-\s*rf|alert\s*\(|<script|<img|<\/?UNTRUSTED|onerror\s*=|onload\s*=|javascript:|\\x1b|\\u001b|[<>]/.test(
    value
  );
}

function ExpandableText({ text, mono = false }: { text: string; mono?: boolean }) {
  const [expanded, setExpanded] = useState(false);

  const value = typeof text === "string" ? text : "—";

  if (typeof text !== "string" || text.length <= TRUNCATE_AT) {
    return (
      <span className={mono ? "break-all font-mono text-xs leading-relaxed" : ""}>
        {value}
      </span>
    );
  }

  return (
    <span className={mono ? "break-all font-mono text-xs leading-relaxed" : ""}>
      {expanded ? value : `${value.slice(0, TRUNCATE_AT)}\u2026`}{" "}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="shrink-0 text-[11px] text-accent underline underline-offset-2 hover:text-accent-dim"
      >
        {expanded ? "show less" : "show more"}
      </button>
    </span>
  );
}

function EvidenceValue({ text }: { text: string }) {
  if (typeof text !== "string" || text.length === 0) {
    return <span className="text-tx-tertiary">—</span>;
  }

  if (!isSuspicious(text)) {
    return <ExpandableText text={text} mono />;
  }

  return (
    <div className="rounded-sm border border-red-900/50 bg-black/40 px-2 py-1.5">
      <span className="hk-label text-red-400">Untrusted observation</span>
      <div className="mt-1">
        <ExpandableText text={text} mono />
      </div>
    </div>
  );
}

function inconclusiveReasons(evidence: ValidationResult): string[] {
  const reasons: string[] = [];
  const observations = evidence?.observations ?? [];
  if (observations.length === 0) {
    reasons.push(
      "No observations were submitted by the validator — there is no data to confirm or deny the scanner claim."
    );
    return reasons;
  }
  for (const obs of observations) {
    const observed =
      typeof obs.observed_value === "string" ? obs.observed_value.trim() : "";
    if (!observed) {
      reasons.push(
        `No observed value was returned for ${obs.target} — the probe could not be executed or produced no result.`
      );
    } else if (/timed?\s*out|timeout|unable to confirm/i.test(observed)) {
      reasons.push(
        `Probe for ${obs.target} did not complete ("${observed.slice(0, 120)}") — not enough signal to confirm or deny.`
      );
    } else {
      reasons.push(
        `Observation for ${obs.target} is ambiguous — it neither matches nor clearly contradicts the scanner claim.`
      );
    }
  }
  return reasons;
}

export function EvidencePanel({ evidence, onValidate, validating = false }: Props) {
  const [selectedTarget, setSelectedTarget] = useState<string>("");

  if (!evidence) return null;

  const observations = evidence.observations ?? [];
  const confidencePct = Math.round(
    (typeof evidence.confidence === "number" ? evidence.confidence : 0) * 100
  );

  const validatedAtMs = evidence.validated_at
    ? new Date(evidence.validated_at).getTime()
    : NaN;
  const ageDays = Number.isFinite(validatedAtMs)
    ? Math.max(0, Math.floor((Date.now() - validatedAtMs) / 86_400_000))
    : null;

  return (
    <section className="rounded-sm border border-line bg-graphite-panel">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="hk-label">Evidence Validation</h2>
          {confidencePct >= 90 && evidence.status === "CONFIRMED" && (
            <span className="font-mono text-[10px] uppercase tracking-wider text-evidence-confirmed">
              high confidence · multi-probe agreement
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {onValidate && (
            <div className="flex items-center gap-1.5">
              <select
                aria-label="Validation probe target"
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                disabled={validating}
                className="rounded-sm border border-line bg-black/50 px-2 py-1 font-mono text-[11px] text-tx-secondary focus:border-accent focus:outline-none"
              >
                <option value="">Current Asset Target</option>
                <option value="shop-api-01">Lab: shop-api-01 (Vulnerable)</option>
                <option value="shop-api-01-patched">Lab: shop-api-01-patched (Patched)</option>
                <option value="db-cluster-01">Lab: db-cluster-01 (Hardened)</option>
              </select>
              <button
                type="button"
                onClick={() => void onValidate(selectedTarget || undefined)}
                disabled={validating}
                className="flex items-center gap-1.5 rounded-sm border border-accent/60 bg-accent-soft px-2.5 py-1 font-mono text-[11px] font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {validating ? (
                  <>
                    <svg
                      className="h-3 w-3 animate-spin text-accent"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8H4z"
                      />
                    </svg>
                    <span>Probing...</span>
                  </>
                ) : (
                  <>
                    <span>⚡ Run Live Probe</span>
                  </>
                )}
              </button>

              {/* Quick Sandbox Target Shortcuts */}
              <div className="hidden lg:flex items-center gap-1 border-l border-line pl-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedTarget("shop-api-01");
                    void onValidate("shop-api-01");
                  }}
                  disabled={validating}
                  className="inline-flex items-center gap-1 rounded-sm border border-red-500/40 bg-red-950/40 px-2 py-1 font-mono text-[10px] font-medium text-red-300 hover:bg-red-900/60 transition-colors disabled:opacity-50"
                  title="Run live probe against vulnerable lab target (proves exploitability)"
                >
                  <span>🔴</span>
                  <span>Vulnerable (shop-api-01)</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedTarget("shop-api-01-patched");
                    void onValidate("shop-api-01-patched");
                  }}
                  disabled={validating}
                  className="inline-flex items-center gap-1 rounded-sm border border-emerald-500/40 bg-emerald-950/40 px-2 py-1 font-mono text-[10px] font-medium text-emerald-300 hover:bg-emerald-900/60 transition-colors disabled:opacity-50"
                  title="Run live probe against patched lab target (verifies fix & demotes priority)"
                >
                  <span>🟢</span>
                  <span>Patched (shop-api-01-patched)</span>
                </button>
              </div>
            </div>
          )}
          <Tooltip content={CONFIDENCE_TOOLTIP}>
            <ValidationBadge
              status={evidence.status}
              confidence={evidence.confidence}
            />
          </Tooltip>
        </div>
      </header>

      <dl className="grid grid-cols-1 gap-x-8 gap-y-3 border-b border-line px-4 py-3 sm:grid-cols-3">
        <div>
          <dt className="hk-label">Validated</dt>
          <dd className="mt-0.5 font-mono text-xs text-tx-secondary">
            {evidence.validated_at
              ? new Date(evidence.validated_at).toLocaleString()
              : "—"}
          </dd>
        </div>
        <div>
          <dt className="hk-label">Validator</dt>
          <dd className="mt-0.5 font-mono text-xs text-tx-secondary">
            {evidence.validator_version ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="hk-label">Cluster</dt>
          <dd className="mt-0.5 font-mono text-xs text-tx-secondary">
            {evidence.cluster_id ?? "—"}
          </dd>
        </div>
      </dl>

      <div className="px-4 py-3">
        <p className="hk-label mb-2">
          Observations · {observations.length}
        </p>
        {observations.length === 0 ? (
          <p className="py-2 text-sm text-tx-secondary">
            No observations recorded for this cluster.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-sm border border-line">
            <table className="w-full min-w-[760px] text-left">
              <thead>
                <tr className="border-b border-line">
                  <th className="hk-label px-3 py-2" scope="col">
                    Type
                  </th>
                  <th className="hk-label px-3 py-2" scope="col">
                    Target
                  </th>
                  <th className="hk-label px-3 py-2" scope="col">
                    Observed
                  </th>
                  <th className="hk-label px-3 py-2" scope="col">
                    Expected
                  </th>
                  <th className="hk-label px-3 py-2" scope="col">
                    Method
                  </th>
                </tr>
              </thead>
              <tbody>
                {observations.map((obs) => (
                  <tr
                    key={obs.observation_id}
                    className="border-b border-line-faint align-top last:border-b-0"
                  >
                    <td className="whitespace-nowrap px-3 py-2.5 text-xs text-tx-secondary">
                      {OBSERVATION_TYPES[obs.type] ?? obs.type}
                    </td>
                    <td className="max-w-[200px] px-3 py-2.5">
                      <ExpandableText text={obs.target} mono />
                    </td>
                    <td className="min-w-[240px] px-3 py-2.5">
                      <EvidenceValue text={obs.observed_value} />
                    </td>
                    <td className="px-3 py-2.5">
                      {obs.expected_value ? (
                        <ExpandableText text={obs.expected_value} mono />
                      ) : (
                        <span className="text-tx-tertiary">—</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 font-mono text-[11px] text-tx-secondary">
                      {obs.method}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {evidence.status === "NOT_CONFIRMED" && (
        <div className="mx-4 mb-4 rounded-sm border-l-2 border-evidence-not-confirmed bg-red-950/25 px-4 py-3.5">
          <h3 className="hk-label text-red-400">
            Contradiction detected — scanner claim not confirmed
          </h3>
          <div className="mt-3 space-y-3">
            {(evidence.observations ?? []).map((obs) => (
              <div key={obs.observation_id} className="text-xs">
                <p className="font-mono text-xs text-tx-secondary">
                  {obs.target}
                </p>
                <div className="mt-1 grid grid-cols-1 gap-2 sm:grid-cols-2">
                  <div className="flex items-start gap-2 border border-line bg-black/30 px-2.5 py-1.5">
                    <span className="hk-label shrink-0 text-red-400">
                      Scanner claim
                    </span>
                    <ExpandableText
                      text={obs.expected_value ?? "the vulnerable state"}
                      mono
                    />
                  </div>
                  <div className="flex items-start gap-2 border border-line bg-black/30 px-2.5 py-1.5">
                    <span className="hk-label shrink-0 text-emerald-400">
                      Observed
                    </span>
                    <ExpandableText text={obs.observed_value} mono />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-tx-secondary">
            Result: <span className="font-mono text-evidence-not-confirmed">NOT CONFIRMED</span> —{" "}
            verifying evidence contradicts the scanner finding. No analyst action required.
          </p>
        </div>
      )}

      {evidence.status === "INCONCLUSIVE" && (
        <div className="mx-4 mb-4 rounded-sm border-l-2 border-amber-400/60 bg-amber-950/20 px-4 py-3.5">
          <h3 className="hk-label text-amber-400">Why inconclusive</h3>
          <ul className="mt-2 list-inside list-disc space-y-1.5 text-xs text-tx-secondary">
            {inconclusiveReasons(evidence).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {evidence.status === "STALE" && ageDays !== null && (
        <div className="mx-4 mb-4 rounded-sm border-l-2 border-amber-400/60 bg-amber-950/20 px-4 py-3.5">
          <h3 className="hk-label text-amber-400">Evidence is stale</h3>
          <p className="mt-1.5 text-xs text-tx-secondary">
            Last validated {ageDays} day{ageDays === 1 ? "" : "s"} ago.
            Infrastructure may have changed since. Revalidation recommended
            before acting on this finding.
          </p>
        </div>
      )}

      <footer className="flex flex-wrap items-center gap-x-6 gap-y-1 border-t border-line px-4 py-2.5 text-[11px] text-tx-tertiary">
        <span>
          Validated at{" "}
          <span className="font-mono">
            {evidence.validated_at
              ? new Date(evidence.validated_at).toLocaleString()
              : "—"}
          </span>
        </span>
        <span>
          Validator <span className="font-mono">{evidence.validator_version ?? "—"}</span>
        </span>
      </footer>
    </section>
  );
}