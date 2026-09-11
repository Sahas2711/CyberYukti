import type { IngestionSummary } from "@/lib/api/types";

interface IngestionPanelProps {
  summary: IngestionSummary | null;
}

const TOOL_COLORS: Record<string, string> = {
  trivy: "bg-sky-500",
  semgrep: "bg-violet-500",
  nuclei: "bg-amber-500",
};

export function IngestionPanel({ summary }: IngestionPanelProps) {
  if (!summary) {
    return (
      <div className="rounded-sm border border-dashed border-line-strong bg-graphite p-5">
        <p className="hk-label">Ingestion</p>
        <p className="mt-2 text-sm text-tx-secondary">
          No ingestion run yet. POST <code className="font-mono text-xs text-accent">/api/v1/scan/demo-ingest</code>{" "}
          or start the backend (it auto-runs ingestion on boot).
        </p>
      </div>
    );
  }

  const tools = Object.entries(summary.breakdown_by_tool ?? {});
  const total = tools.reduce((s, [, count]) => s + count, 0) || 1;

  return (
    <div className="rounded-sm border border-line bg-graphite">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <p className="hk-label">Ingestion — real dedup engine output</p>
        <span className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
          {summary.total_raw_findings} raw → {summary.total_clusters} clusters
        </span>
      </div>

      <div className="px-4 py-4">
        <div className="flex items-baseline justify-between">
          <p className="text-2xl font-semibold tabular-nums text-tx-primary">
            {summary.noise_reduction_percentage.toFixed(1)}%
          </p>
          <span className="hk-label">noise reduced</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-graphite-deep">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${Math.min(100, summary.noise_reduction_percentage)}%` }}
          />
        </div>

        <div className="mt-4 space-y-2">
          {tools.map(([tool, count]) => (
            <div key={tool} className="flex items-center gap-3">
              <span className="w-20 font-mono text-[11px] uppercase text-tx-secondary">
                {tool}
              </span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-graphite-deep">
                <div
                  className={`h-full rounded-full ${TOOL_COLORS[tool] ?? "bg-accent"}`}
                  style={{ width: `${Math.round((count / total) * 100)}%` }}
                />
              </div>
              <span className="w-8 text-right font-mono text-[11px] tabular-nums text-tx-tertiary">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
