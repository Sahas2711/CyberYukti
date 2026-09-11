"use client";

import type { IngestionCluster } from "@/lib/api/types";

interface ClustersPanelProps {
  clusters: IngestionCluster[];
}

export function ClustersPanel({ clusters }: ClustersPanelProps) {
  if (clusters.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-line-strong bg-graphite p-5">
        <p className="hk-label">Dedup clusters</p>
        <p className="mt-2 text-sm text-tx-secondary">
          No clusters available yet — ingestion has not produced output.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-sm border border-line bg-graphite">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <p className="hk-label">Deduplicated clusters — 3-tier correlation</p>
        <span className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
          {clusters.length} clusters
        </span>
      </div>

      <ul className="divide-y divide-line-faint">
        {clusters.map((cluster) => (
          <li key={cluster.cluster_id} className="px-4 py-3.5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-[13px] font-medium text-tx-primary">{cluster.title}</p>
              <span className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
                {cluster.cluster_id}
              </span>
            </div>

            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-tx-tertiary">
              <span className="font-mono text-tx-secondary">
                {cluster.primary_cve ?? cluster.root_cause_cwe ?? "no CVE/CWE"}
              </span>
              <span>·</span>
              <span>{cluster.affected_component}</span>
              <span>·</span>
              <span>
                {cluster.raw_findings_count} findings from{" "}
                {cluster.participating_tools.join(" + ")}
              </span>
              {cluster.normalized_route && (
                <>
                  <span>·</span>
                  <span className="font-mono">{cluster.normalized_route}</span>
                </>
              )}
            </div>

            {cluster.representative_finding?.fixed_version && (
              <p className="mt-1.5 text-[11px] text-tx-tertiary">
                fix: {cluster.representative_finding.package_name}{" "}
                <span className="font-mono text-accent">
                  {cluster.representative_finding.installed_version} →{" "}
                  {cluster.representative_finding.fixed_version}
                </span>
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
