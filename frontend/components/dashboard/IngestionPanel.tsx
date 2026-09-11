"use client";

import type { IngestionSummary } from "@/lib/api/types";

interface IngestionPanelProps {
  summary: IngestionSummary | null;
}

const TOOL_CONFIG: Record<
  string,
  { label: string; color: string; ringColor: string; textColor: string }
> = {
  trivy: {
    label: "Trivy (SCA/Container)",
    color: "bg-sky-500",
    ringColor: "border-sky-500/40 text-sky-400 bg-sky-500/10",
    textColor: "text-sky-400",
  },
  semgrep: {
    label: "Semgrep (SAST)",
    color: "bg-purple-500",
    ringColor: "border-purple-500/40 text-purple-400 bg-purple-500/10",
    textColor: "text-purple-400",
  },
  nuclei: {
    label: "Nuclei (DAST)",
    color: "bg-amber-500",
    ringColor: "border-amber-500/40 text-amber-400 bg-amber-500/10",
    textColor: "text-amber-400",
  },
};

export function IngestionPanel({ summary }: IngestionPanelProps) {
  if (!summary) {
    return (
      <div className="rounded-md border border-dashed border-line-strong bg-graphite p-6">
        <p className="hk-label">Ingestion Engine</p>
        <p className="mt-2 text-sm text-tx-secondary">
          No ingestion run yet. POST <code className="font-mono text-xs text-accent">/api/v1/scan/demo-ingest</code>{" "}
          or start the backend (it auto-runs ingestion on boot).
        </p>
      </div>
    );
  }

  const tools = Object.entries(summary.breakdown_by_tool ?? {});
  const total = tools.reduce((s, [, count]) => s + count, 0) || 1;
  const reductionRate = summary.noise_reduction_percentage;

  // SVG Gauge calculations
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, reductionRate)) / 100) * circumference;

  return (
    <div className="rounded-md border border-line bg-graphite shadow-sm transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
          <p className="hk-label">Person 1: Ingestion & Dedup Engine</p>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-wider rounded border border-line-strong bg-graphite-deep px-2 py-0.5 text-tx-tertiary">
          GitLab Triple-Tuple Dedup
        </span>
      </div>

      <div className="p-5">
        {/* Top visual metrics: Radial Gauge + Noise Stats */}
        <div className="flex flex-col sm:flex-row items-center gap-6 pb-5 border-b border-line-strong/60">
          {/* Circular SVG Gauge */}
          <div className="relative flex items-center justify-center shrink-0">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="stroke-line-strong"
                strokeWidth="7"
                fill="transparent"
              />
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="stroke-accent transition-all duration-1000 ease-out"
                strokeWidth="7"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-xl font-bold font-mono tracking-tight text-tx-primary">
                {reductionRate.toFixed(1)}%
              </span>
              <span className="text-[9px] font-mono uppercase tracking-widest text-tx-tertiary">
                REDUCED
              </span>
            </div>
          </div>

          {/* Metric Explanation */}
          <div className="space-y-1.5 flex-1 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <span className="font-mono text-xs font-semibold text-accent uppercase tracking-wider">
                Autonomous Noise Reduction
              </span>
            </div>
            <p className="text-sm text-tx-secondary leading-relaxed">
              Collapsed <span className="font-bold text-tx-primary font-mono">{summary.total_raw_findings}</span> multi-scanner findings into{" "}
              <span className="font-bold text-accent font-mono">{summary.total_clusters}</span> actionable clusters, eliminating alert fatigue.
            </p>
            <div className="flex items-center justify-center sm:justify-start gap-3 pt-1 text-xs text-tx-tertiary font-mono">
              <span>Fingerprint: <span className="text-tx-secondary">Asset + Path + Rule</span></span>
              <span>•</span>
              <span>CWE Excluded</span>
            </div>
          </div>
        </div>

        {/* Multi-Scanner Breakdown */}
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between text-[11px] font-mono text-tx-tertiary uppercase">
            <span>Scanner Source</span>
            <span>Raw Hits / Share</span>
          </div>

          {tools.map(([tool, count]) => {
            const config = TOOL_CONFIG[tool] ?? {
              label: tool.toUpperCase(),
              color: "bg-accent",
              ringColor: "border-line-strong text-tx-secondary bg-graphite-deep",
              textColor: "text-tx-secondary",
            };
            const percentage = Math.round((count / total) * 100);

            return (
              <div key={tool} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold border ${config.ringColor}`}>
                      {tool.toUpperCase()}
                    </span>
                    <span className="font-medium text-tx-secondary">
                      {config.label}
                    </span>
                  </div>
                  <span className="font-mono tabular-nums text-tx-primary font-semibold">
                    {count} <span className="text-tx-tertiary font-normal">({percentage}%)</span>
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-graphite-deep">
                  <div
                    className={`h-full rounded-full ${config.color} transition-all duration-700 ease-out`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
