import { Badge } from "@/components/shared/Badge";
import type { PriorityResult } from "@/lib/api/types";

interface Props {
  priority: PriorityResult;
}

interface FactorRow {
  name: string;
  label: string;
  display: string;
  pct: number;
}

const priorityVariantMap: Record<string, "p1" | "p2" | "p3" | "p4"> = {
  P1: "p1",
  P2: "p2",
  P3: "p3",
  P4: "p4",
};

const CRITICALITY_SCORES: Record<string, number> = {
  critical: 100,
  high: 75,
  medium: 50,
  low: 25,
};

function buildFactors(priority: PriorityResult): FactorRow[] {
  const rows: FactorRow[] = [];
  const factors = priority?.factors ?? {};

  if (typeof factors.cvss === "number" && !Number.isNaN(factors.cvss)) {
    rows.push({
      name: "cvss",
      label: "CVSS",
      display: factors.cvss.toFixed(1),
      pct: Math.min(100, (factors.cvss / 10) * 100),
    });
  }

  if (typeof factors.epss === "number" && !Number.isNaN(factors.epss)) {
    rows.push({
      name: "epss",
      label: "EPSS",
      display: `${(factors.epss * 100).toFixed(1)}%`,
      pct: Math.min(100, factors.epss * 100),
    });
  }

  if (typeof factors.kev === "boolean") {
    rows.push({
      name: "kev",
      label: "KEV",
      display: factors.kev ? "Yes" : "No",
      pct: factors.kev ? 100 : 0,
    });
  }

  if (typeof factors.asset_criticality === "string") {
    const key = factors.asset_criticality.toLowerCase();
    rows.push({
      name: "asset_criticality",
      label: "Asset Criticality",
      display: factors.asset_criticality,
      pct: CRITICALITY_SCORES[key] ?? 50,
    });
  }

  if (typeof factors.internet_exposed === "boolean") {
    rows.push({
      name: "internet_exposed",
      label: "Internet Exposed",
      display: factors.internet_exposed ? "Yes" : "No",
      pct: factors.internet_exposed ? 100 : 0,
    });
  }

  if (
    typeof factors.evidence_confidence === "number" &&
    !Number.isNaN(factors.evidence_confidence)
  ) {
    const pct = Math.min(100, factors.evidence_confidence * 100);
    rows.push({
      name: "evidence_confidence",
      label: "Evidence Confidence",
      display: `${Math.round(pct)}%`,
      pct,
    });
  }

  return rows;
}

export function PriorityBreakdown({ priority }: Props) {
  if (!priority) return null;

  const rows = buildFactors(priority);
  const score = typeof priority.score === "number" ? priority.score : NaN;
  const scoreDisplay = Number.isNaN(score) ? "—" : score.toFixed(1);

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <h2 className="hk-label">Priority Decision</h2>
        <span className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
          Formula v{priority.formula_version ?? "unknown"}
        </span>
      </header>

      <div className="flex items-center gap-3 border-b border-line px-4 py-4">
        <span className="text-4xl font-semibold tabular-nums tracking-tight text-tx-primary">
          {scoreDisplay}
        </span>
        <span className="text-sm text-tx-tertiary">/ 100</span>
        {priority.level && (
          <Badge variant={priorityVariantMap[priority.level] ?? "p4"}>
            {priority.level}
          </Badge>
        )}
      </div>

      {rows.length === 0 ? (
        <p className="px-4 py-4 text-sm text-tx-secondary">
          No factor data available for this cluster.
        </p>
      ) : (
        <div className="space-y-3 p-4">
          {rows.map((row) => (
            <div key={row.name}>
              <div className="mb-1 flex items-baseline justify-between gap-3">
                <span className="text-xs text-tx-secondary">{row.label}</span>
                <span className="font-mono text-xs tabular-nums text-tx-primary">
                  {row.display}
                </span>
              </div>
              <div className="h-[6px] w-full overflow-hidden rounded-sm bg-graphite-deep">
                <div
                  className="h-full rounded-sm bg-accent-dim"
                  style={{ width: `${Math.max(0, Math.min(100, row.pct))}%` }}
                />
              </div>
            </div>
          ))}
          <p className="pt-1 text-[11px] text-tx-tertiary">
            Score is computed deterministically from the validated factors above.
          </p>
        </div>
      )}
    </section>
  );
}