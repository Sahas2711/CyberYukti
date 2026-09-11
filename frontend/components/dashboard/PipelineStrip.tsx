import type { DashboardStats } from "@/lib/api/types";

interface PipelineStripProps {
  stats: DashboardStats;
  pending: number;
}

interface Stage {
  key: string;
  label: string;
  value: number;
  hint: string;
}

export function PipelineStrip({ stats, pending }: PipelineStripProps) {
  const validated = stats.confirmed + stats.not_confirmed + stats.inconclusive;
  const prioritized = stats.p1 + stats.p2 + stats.p3 + stats.p4;

  const stages: Stage[] = [
    { key: "findings", label: "Findings", value: stats.total_findings, hint: "scanner output normalized" },
    { key: "clusters", label: "Clusters", value: stats.unique_clusters, hint: "deduplication applied" },
    { key: "validated", label: "Validated", value: validated, hint: "evidence probed" },
    { key: "prioritized", label: "Prioritized", value: prioritized, hint: "deterministic formula" },
    { key: "decisions", label: "Decisions", value: pending, hint: "awaiting analyst" },
  ];

  return (
    <div className="overflow-hidden rounded-sm border border-line bg-graphite">
      <ol className="flex divide-x divide-line-strong">
        {stages.map((stage, index) => (
          <li key={stage.key} className="flex flex-1 flex-col px-4 py-3.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-tx-tertiary">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="hk-label">{stage.label}</span>
            </div>
            <p className="mt-1 text-xl font-semibold leading-none tabular-nums text-tx-primary">
              {stage.value}
            </p>
            <span className="mt-1.5 text-[11px] text-tx-tertiary">
              {stage.hint}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}