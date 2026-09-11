import type { AIAnalysis } from "@/lib/api/types";

interface Props {
  analysis: AIAnalysis | null;
}

export function RemediationPanel({ analysis }: Props) {
  const steps = Array.isArray(analysis?.recommended_remediation)
    ? analysis?.recommended_remediation.filter(Boolean) ?? []
    : [];

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="border-b border-line px-4 py-3">
        <h2 className="hk-label">Remediation</h2>
        <p className="mt-0.5 text-[11px] text-tx-tertiary">
          Recommended actions in priority order
        </p>
      </header>
      {steps.length === 0 ? (
        <div className="px-4 py-8 text-center">
          <p className="text-xs text-tx-secondary">
            No remediation steps available yet. Run AI analysis to generate
            recommended remediation actions.
          </p>
        </div>
      ) : (
        <ol className="p-4">
          {steps.map((step, index) => (
            <li
              key={step}
              className="flex gap-3 border-b border-line-faint py-2 first:pt-0 last:border-b-0 last:pb-0"
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm border border-accent/40 bg-accent-soft font-mono text-[10px] font-semibold text-accent">
                {index + 1}
              </span>
              <span className="text-sm leading-relaxed text-tx-secondary">{step}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}