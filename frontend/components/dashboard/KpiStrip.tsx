import type { DashboardStats } from "@/lib/api/types";

interface KpiStripProps {
  stats: DashboardStats;
  pending: number;
}

interface KpiCell {
  label: string;
  value: number;
  hint: string;
  valueClass?: string;
}

export function KpiStrip({ stats, pending }: KpiStripProps) {
  const cells: KpiCell[] = [
    {
      label: "Total Findings",
      value: stats.total_findings,
      hint: "raw scanner hits",
    },
    {
      label: "Unique Clusters",
      value: stats.unique_clusters,
      hint: "deduplicated",
    },
    {
      label: "Confirmed",
      value: stats.confirmed,
      hint: "verified issues",
      valueClass: "text-evidence-confirmed",
    },
    {
      label: "Not Confirmed",
      value: stats.not_confirmed,
      hint: "likely false positives",
      valueClass: "text-evidence-not-confirmed",
    },
    {
      label: "Inconclusive",
      value: stats.inconclusive,
      hint: "needs follow-up",
      valueClass: "text-amber-400",
    },
    {
      label: "Pending Review",
      value: pending,
      hint: "awaiting analyst decision",
      valueClass: "text-amber-300",
    },
  ];

  return (
    <div className="grid grid-cols-2 divide-line-strong overflow-hidden rounded-sm border border-line bg-graphite sm:grid-cols-3 xl:grid-cols-6 xl:divide-x">
      {cells.map((cell) => (
        <div key={cell.label} className="flex flex-col px-4 py-3.5">
          <p className="text-[22px] font-semibold leading-none tabular-nums">
            <span className={cell.valueClass ?? "text-tx-primary"}>
              {cell.value}
            </span>
          </p>
          <div className="mt-2 flex flex-col">
            <span className="hk-label">{cell.label}</span>
            <span className="mt-0.5 text-[11px] text-tx-tertiary">
              {cell.hint}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}