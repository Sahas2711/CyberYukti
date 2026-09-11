import type { TriageCase } from "@/lib/api/types";

interface Props {
  case: TriageCase;
}

const decisionColors: Record<string, string> = {
  PENDING: "bg-amber-400",
  APPROVED: "bg-emerald-400",
  REJECTED: "bg-red-400",
  OVERRIDDEN: "bg-violet-400",
};

export function CasePipeline({ case: caseData }: Props) {
  if (!caseData) return null;

  const findingCount = caseData.finding_count ?? 1;
  const evidenceStatus = caseData.evidence?.status ?? "—";
  const approval = caseData.approval?.status ?? "—";

  const stages = [
    {
      key: "detected",
      label: "Detected",
      value: `${findingCount} finding${findingCount === 1 ? "" : "s"} ingested`,
      done: true,
    },
    {
      key: "clustered",
      label: "Clustered",
      value: caseData.cluster_id
        ? `deduplicated into ${caseData.cluster_id}`
        : "not clustered",
      done: Boolean(caseData.cluster_id),
    },
    {
      key: "validated",
      label: "Validated",
      value: caseData.evidence?.validated_at
        ? evidenceStatus
        : "evidence pending",
      done: Boolean(caseData.evidence?.validated_at),
      accent:
        evidenceStatus === "CONFIRMED"
          ? "bg-evidence-confirmed"
          : evidenceStatus === "NOT_CONFIRMED"
          ? "bg-evidence-not-confirmed"
          : evidenceStatus === "INCONCLUSIVE"
          ? "bg-amber-400"
          : "bg-amber-300",
    },
    {
      key: "prioritized",
      label: "Prioritized",
      value:
        typeof caseData.priority?.score === "number"
          ? `${caseData.priority.level} · ${caseData.priority.score.toFixed(1)}/100`
          : "not scored",
      done: typeof caseData.priority?.score === "number",
    },
    {
      key: "decision",
      label: "Decision",
      value: approval,
      done: approval !== "PENDING",
      accent: decisionColors[approval] ?? "bg-amber-400",
    },
  ];

  return (
    <section className="overflow-hidden rounded-sm border border-line bg-graphite">
      <ol className="flex flex-col gap-0 sm:flex-row sm:divide-x sm:divide-line-strong">
        {stages.map((stage, index) => (
          <li key={stage.key} className="flex flex-1 flex-col gap-1 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-tx-tertiary">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="hk-label">{stage.label}</span>
              <span
                className={`ml-auto h-1.5 w-1.5 rounded-full ${
                  stage.done ? (stage.accent ?? "bg-accent") : "bg-line-strong"
                }`}
                aria-hidden="true"
              />
            </div>
            <p className="font-mono text-xs text-tx-secondary">{stage.value}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}