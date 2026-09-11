import type { DashboardStats, TriageCase } from "@/lib/api/types";

interface PriorityQueueProps {
  stats: DashboardStats;
  cases: TriageCase[];
}

const LEVELS = [
  { key: "p1", label: "P1", color: "#ef4444", tag: "investigate first" },
  { key: "p2", label: "P2", color: "#f97316", tag: "review promptly" },
  { key: "p3", label: "P3", color: "#eab308", tag: "scheduled review" },
  { key: "p4", label: "P4", color: "#22c55e", tag: "monitor" },
] as const;

type LevelKey = (typeof LEVELS)[number]["key"];

const levelOrder: Record<LevelKey, number> = { p1: 0, p2: 1, p3: 2, p4: 3 };

export function PriorityQueue({ stats, cases }: PriorityQueueProps) {
  const maxCount = Math.max(stats.p1, stats.p2, stats.p3, stats.p4, 1);

  const pendingByLevel = new Map<LevelKey, number>();
  for (const c of cases) {
    const key = c.priority.level.toLowerCase() as LevelKey;
    if (c.approval.status === "PENDING") {
      pendingByLevel.set(key, (pendingByLevel.get(key) ?? 0) + 1);
    }
  }

  const sorted = [...LEVELS].sort(
    (a, b) => levelOrder[a.key] - levelOrder[b.key]
  );

  return (
    <div className="flex h-full flex-col rounded-sm border border-line bg-graphite">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="hk-label">Priority Queue</h2>
        <span className="font-mono text-[10px] uppercase tracking-wider text-tx-tertiary">
          analyst guidance
        </span>
      </div>
      <div className="flex flex-1 flex-col justify-center gap-4 p-4">
        {sorted.map(({ key, label, color, tag }) => {
          const count = stats[key];
          const pending = pendingByLevel.get(key) ?? 0;
          const widthPercent = (count / maxCount) * 100;
          return (
            <div key={key} className="flex items-center gap-3">
              <span
                className="w-8 shrink-0 text-sm font-semibold tracking-wide"
                style={{ color }}
              >
                {label}
              </span>
              <div className="min-w-0 flex-1">
                <div className="h-[6px] w-full overflow-hidden rounded-sm bg-graphite-deep">
                  <div
                    className="h-full rounded-sm transition-all duration-300"
                    style={{
                      width: `${Math.max(2, widthPercent)}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>
              </div>
              <div className="w-28 shrink-0 text-right">
                <p className="text-sm font-semibold tabular-nums text-tx-primary">
                  {count}
                  <span className="ml-1 text-[11px] font-normal text-tx-tertiary">
                    case{count === 1 ? "" : "s"}
                  </span>
                </p>
                <p className="text-[10px] text-tx-tertiary">
                  {tag}
                  {pending > 0 && (
                    <span className="ml-1 font-mono text-amber-400">
                      · {pending} pending
                    </span>
                  )}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}