"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { TriageCase } from "@/lib/api/types";
import { Badge } from "@/components/shared/Badge";

interface CaseTableProps {
  cases: TriageCase[];
  initialQuery?: string;
  initialPriority?: string;
  initialEvidence?: string;
  initialApproval?: string;
}

const evidenceVariant: Record<string, "confirmed" | "not-confirmed" | "inconclusive" | "stale"> = {
  CONFIRMED: "confirmed",
  NOT_CONFIRMED: "not-confirmed",
  INCONCLUSIVE: "inconclusive",
  STALE: "stale",
};

const approvalVariant: Record<string, "pending" | "approved" | "rejected" | "overridden"> = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
  OVERRIDDEN: "overridden",
};

const PRIORITY_OPTIONS = ["ALL", "P1", "P2", "P3", "P4"];
const EVIDENCE_OPTIONS = ["ALL", "CONFIRMED", "NOT_CONFIRMED", "INCONCLUSIVE", "STALE"];
const APPROVAL_OPTIONS = ["ALL", "PENDING", "APPROVED", "REJECTED", "OVERRIDDEN"];

const levelOrder: Record<string, number> = { P1: 0, P2: 1, P3: 2, P4: 3 };

function vulnRefs(c: TriageCase): string {
  const refs = [c.vulnerability?.cve, c.vulnerability?.cwe]
    .filter((r): r is string => Boolean(r));
  return refs.length > 0 ? refs.join(" · ") : "no CVE/CWE recorded";
}

function matchesQuery(c: TriageCase, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const haystack = [
    c.case_id,
    c.cluster_id,
    c.title,
    c.asset.hostname,
    c.asset.environment,
    c.asset.criticality,
    ...(c.sources ?? []),
    c.vulnerability?.cve ?? "",
    c.vulnerability?.cwe ?? "",
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(q);
}

export function CaseTable({
  cases,
  initialQuery = "",
  initialPriority = "ALL",
  initialEvidence = "ALL",
  initialApproval = "ALL",
}: CaseTableProps) {
  const [query, setQuery] = useState(initialQuery);
  const [priority, setPriority] = useState(initialPriority);
  const [evidence, setEvidence] = useState(initialEvidence);
  const [approval, setApproval] = useState(initialApproval);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const result = cases.filter(
      (c) =>
        (priority === "ALL" || c.priority.level === priority) &&
        (evidence === "ALL" || c.evidence.status === evidence) &&
        (approval === "ALL" || c.approval.status === approval) &&
        matchesQuery(c, q)
    );
    return [...result].sort(
      (a, b) =>
        (levelOrder[a.priority.level] ?? 9) - (levelOrder[b.priority.level] ?? 9) ||
        b.priority.score - a.priority.score
    );
  }, [cases, query, priority, evidence, approval]);

  const hasActiveFilters =
    query.trim() !== "" || priority !== "ALL" || evidence !== "ALL" || approval !== "ALL";

  function resetFilters() {
    setQuery("");
    setPriority("ALL");
    setEvidence("ALL");
    setApproval("ALL");
  }

  if (cases.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-line-strong bg-graphite py-16 text-center">
        <p className="hk-label">No cases yet</p>
        <p className="mt-2 text-sm text-tx-secondary">
          Cases will appear here once scanners report findings.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-sm border border-line bg-graphite">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line px-3 py-2.5">
        <label className="relative min-w-[220px] flex-1">
          <span className="sr-only">Search cases</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title, hostname, CVE, source…"
            className="w-full rounded-sm border border-line bg-graphite-deep px-2.5 py-1.5 text-xs text-tx-primary placeholder:text-tx-tertiary focus:border-accent focus:outline-none"
          />
        </label>

        {(
          [
            ["priority", "Priority", priority, setPriority, PRIORITY_OPTIONS],
            ["evidence", "Evidence", evidence, setEvidence, EVIDENCE_OPTIONS],
            ["approval", "Decision", approval, setApproval, APPROVAL_OPTIONS],
          ] as const
        ).map(([key, labelText, value, setter, options]) => (
          <label key={key} className="flex items-center gap-1.5">
            <span className="hk-label">{labelText}</span>
            <select
              aria-label={`Filter by ${labelText.toLowerCase()}`}
              value={value}
              onChange={(e) => setter(e.target.value)}
              className="rounded-sm border border-line bg-graphite-deep px-2 py-1.5 font-mono text-[11px] uppercase tracking-wide text-tx-secondary focus:border-accent focus:outline-none"
            >
              {options.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ))}

        {hasActiveFilters && (
          <button
            type="button"
            onClick={resetFilters}
            className="rounded-sm border border-line px-2 py-1.5 font-mono text-[10px] uppercase tracking-wider text-tx-secondary transition-colors hover:border-accent hover:text-accent"
          >
            Reset
          </button>
        )}
      </div>

      {/* Result count */}
      <div className="flex items-center justify-between px-3 py-1.5">
        <p className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
          {filtered.length} of {cases.length} cases
        </p>
        {hasActiveFilters && (
          <Link href="/cases" className="text-[11px] text-accent hover:underline">
            view all
          </Link>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto border-t border-line">
        <table className="w-full min-w-[880px] text-left">
          <thead>
            <tr className="border-b border-line">
              {["Vulnerability", "Asset", "Evidence", "Priority", "Sources", "Decision"].map(
                (heading) => (
                  <th
                    key={heading}
                    className="hk-label px-3 py-2 first:pl-4 last:pr-4"
                    scope="col"
                  >
                    {heading}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center">
                  <p className="text-sm text-tx-secondary">
                    No cases match the current filter.
                  </p>
                </td>
              </tr>
            ) : (
              filtered.map((c) => {
                const evidenceConfidence = Math.round(
                  (typeof c.evidence.confidence === "number"
                    ? c.evidence.confidence
                    : 0) * 100
                );
                return (
                  <tr
                    key={c.case_id}
                    tabIndex={0}
                    aria-label={`Open case ${c.case_id}: ${c.title}`}
                    onClick={() => {
                      window.location.href = `/cases/${c.case_id}`;
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        window.location.href = `/cases/${c.case_id}`;
                      }
                    }}
                    className="group cursor-pointer border-b border-line-faint transition-colors last:border-b-0 hover:bg-graphite-deep focus-visible:bg-graphite-deep"
                  >
                    <td className="px-3 py-3 first:pl-4">
                      <p className="text-[13px] font-medium text-tx-primary">
                        {c.title}
                      </p>
                      <p className="mt-0.5 font-mono text-[11px] text-tx-tertiary">
                        {c.case_id} · {vulnRefs(c)}
                      </p>
                    </td>
                    <td className="px-3 py-3">
                      <p className="font-mono text-xs text-tx-secondary">
                        {c.asset.hostname}
                      </p>
                      <p className="mt-0.5 text-[10px] uppercase tracking-wider text-tx-tertiary">
                        {c.asset.environment} ·{" "}
                        {c.asset.internet_exposed ? "internet exposed" : "internal"} ·{" "}
                        {c.asset.criticality}
                      </p>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-1.5">
                        <Badge variant={evidenceVariant[c.evidence.status]}>
                          {c.evidence.status}
                        </Badge>
                        <span className="font-mono text-[11px] tabular-nums text-tx-secondary">
                          {evidenceConfidence}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            (c.priority.level.toLowerCase() as "p1" | "p2" | "p3" | "p4")
                          }
                        >
                          {c.priority.level}
                        </Badge>
                        <span className="font-mono text-sm font-semibold tabular-nums text-tx-primary">
                          {typeof c.priority.score === "number"
                            ? c.priority.score.toFixed(1)
                            : "—"}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className="block max-w-[180px] truncate font-mono text-[11px] text-tx-secondary"
                        title={(c.sources ?? []).join(", ")}
                      >
                        {(c.sources ?? []).join(", ")}
                      </span>
                    </td>
                    <td className="px-3 py-3 last:pr-4">
                      <Badge variant={approvalVariant[c.approval.status]}>
                        {c.approval.status}
                      </Badge>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}