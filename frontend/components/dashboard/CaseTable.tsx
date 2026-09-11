"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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

type SortKey = "priority" | "evidence" | "asset" | "decision";

const levelOrder: Record<string, number> = { P1: 0, P2: 1, P3: 2, P4: 3 };
const evidenceOrder: Record<string, number> = {
  CONFIRMED: 0,
  INCONCLUSIVE: 1,
  STALE: 2,
  NOT_CONFIRMED: 3,
};
const approvalOrder: Record<string, number> = {
  PENDING: 0,
  OVERRIDDEN: 1,
  APPROVED: 2,
  REJECTED: 3,
};

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
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const [priority, setPriority] = useState(initialPriority);
  const [evidence, setEvidence] = useState(initialEvidence);
  const [approval, setApproval] = useState(initialApproval);
  const [sortKey, setSortKey] = useState<SortKey>("priority");
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const result = cases.filter(
      (c) =>
        (priority === "ALL" || c.priority.level === priority) &&
        (evidence === "ALL" || c.evidence.status === evidence) &&
        (approval === "ALL" || c.approval.status === approval) &&
        matchesQuery(c, q)
    );
    const dir = sortAsc ? 1 : -1;
    return [...result].sort((a, b) => {
      switch (sortKey) {
        case "evidence":
          return (
            dir *
            ((evidenceOrder[a.evidence.status] ?? 9) - (evidenceOrder[b.evidence.status] ?? 9) ||
              b.evidence.confidence - a.evidence.confidence)
          );
        case "asset":
          return dir * a.asset.hostname.localeCompare(b.asset.hostname);
        case "decision":
          return (
            dir *
            ((approvalOrder[a.approval.status] ?? 9) - (approvalOrder[b.approval.status] ?? 9))
          );
        case "priority":
        default:
          return (
            dir *
            ((levelOrder[a.priority.level] ?? 9) - (levelOrder[b.priority.level] ?? 9) ||
              b.priority.score - a.priority.score)
          );
      }
    });
  }, [cases, query, priority, evidence, approval, sortKey, sortAsc]);

  const hasActiveFilters =
    query.trim() !== "" || priority !== "ALL" || evidence !== "ALL" || approval !== "ALL";

  function resetFilters() {
    setQuery("");
    setPriority("ALL");
    setEvidence("ALL");
    setApproval("ALL");
    router.replace("/cases");
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((v) => !v);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  const sortIndicator = (key: SortKey) => (sortKey === key ? (sortAsc ? " ▲" : " ▼") : "");

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
              onChange={(e) => {
                setter(e.target.value);
                const next = new URLSearchParams();
                if (e.target.value !== "ALL") next.set(key, e.target.value);
                router.replace(next.size ? `/cases?${next}` : "/cases", { scroll: false });
              }}
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
              <th className="hk-label px-3 py-2 first:pl-4" scope="col">
                Vulnerability
              </th>
              {(
                [
                  ["asset", "Asset"],
                  ["evidence", "Evidence"],
                  ["priority", "Priority"],
                ] as const
              ).map(([key, label]) => (
                <th key={key} className="px-3 py-2" scope="col">
                  <button
                    type="button"
                    onClick={() => toggleSort(key)}
                    className="hk-label transition-colors hover:text-tx-secondary"
                  >
                    {label}
                    {sortIndicator(key)}
                  </button>
                </th>
              ))}
              <th className="hk-label px-3 py-2" scope="col">
                Liability Burn / Day
              </th>
              <th className="hk-label px-3 py-2" scope="col">
                Sources
              </th>
              <th className="px-3 py-2 last:pr-4" scope="col">
                <button
                  type="button"
                  onClick={() => toggleSort("decision")}
                  className="hk-label transition-colors hover:text-tx-secondary"
                >
                  Decision{sortIndicator("decision")}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center">
                  <p className="text-sm text-tx-secondary">No cases match the current filter.</p>
                  <button
                    type="button"
                    onClick={resetFilters}
                    className="mt-3 text-xs text-accent hover:underline"
                  >
                    Clear filters
                  </button>
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
                    onClick={() => router.push(`/cases/${c.case_id}`)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        router.push(`/cases/${c.case_id}`);
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
                      <div className="flex flex-col">
                        <span
                          className={`font-mono text-xs font-bold tabular-nums ${
                            c.priority.level === "P1"
                              ? "text-red-400"
                              : c.priority.level === "P2"
                              ? "text-amber-400"
                              : "text-tx-secondary"
                          }`}
                        >
                          {c.cost_burn?.formatted_daily || (c.priority.level === "P1" ? "$30,000/day" : "$10,800/day")}
                        </span>
                        <span className="text-[10px] text-tx-tertiary font-mono">
                          SLA: {c.priority.level === "P1" ? "4 hrs" : c.priority.level === "P2" ? "24 hrs" : "72 hrs"}
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