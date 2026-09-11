import { LoadingState } from "@/components/shared/LoadingState";
import type { AIAnalysis } from "@/lib/api/types";

interface Props {
  analysis: AIAnalysis | null;
  onAnalyze: () => void;
  loading: boolean;
}

function SectionList({
  title,
  items,
  emptyText = "None available.",
}: {
  title: string;
  items?: string[];
  emptyText?: string;
}) {
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  return (
    <section>
      <h3 className="hk-label mb-1.5">{title}</h3>
      {list.length === 0 ? (
        <p className="text-xs text-tx-tertiary">{emptyText}</p>
      ) : (
        <ul className="space-y-1 text-sm text-tx-secondary">
          {list.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-line-strong" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function AIAnalysisPanel({ analysis, onAnalyze, loading }: Props) {
  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <div>
          <h2 className="hk-label">Analyst Assist</h2>
          <p className="mt-0.5 text-[11px] text-tx-tertiary">
            AI-generated explanation — supports, never replaces, the analyst decision
          </p>
        </div>
        <div className="flex items-center gap-2">
          {analysis && (
            <button
              type="button"
              onClick={onAnalyze}
              disabled={loading}
              className="rounded-sm border border-accent/40 bg-accent-soft px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-accent transition-colors hover:bg-accent/20 disabled:opacity-50"
            >
              {loading ? "Re-analyzing..." : "Re-run analysis"}
            </button>
          )}
          <span className="rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-[3px] text-[10px] font-semibold uppercase tracking-wider text-amber-400">
            AI-generated
          </span>
        </div>
      </header>

      {loading ? (
        <div className="px-4 py-3">
          <LoadingState message="Running AI analysis..." />
        </div>
      ) : !analysis ? (
        <div className="px-4 py-8 text-center">
          <p className="hk-label">Not analysed</p>
          <p className="mx-auto mt-2 max-w-sm text-xs text-tx-secondary">
            No AI explanation exists for this case yet. Run analysis to generate a
            grounded explanation from the validated case data.
          </p>
          <button
            type="button"
            onClick={onAnalyze}
            className="mt-5 rounded-sm border border-accent/50 bg-accent-soft px-4 py-2 text-xs font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/15"
          >
            Run analysis
          </button>
        </div>
      ) : (
        <div className="space-y-5 p-4">
          <section>
            <h3 className="hk-label mb-1.5">Summary</h3>
            <p className="border-l-2 border-accent-dim pl-3 text-sm leading-relaxed text-tx-primary">
              {analysis.summary}
            </p>
          </section>

          <SectionList title="Why this matters" items={[analysis.why_it_matters]} />
          <SectionList
            title="Evidence interpretation"
            items={[analysis.evidence_summary]}
          />
          <SectionList
            title="Priority explanation"
            items={[analysis.priority_explanation]}
          />

          <SectionList
            title="Investigation questions"
            items={analysis.investigation_questions}
          />
          <SectionList
            title="Recommended remediation"
            items={analysis.recommended_remediation}
          />
          <SectionList title="Confidence notes" items={analysis.confidence_notes} />
          <SectionList title="Limitations" items={analysis.limitations} />

          <section>
            <h3 className="hk-label mb-1.5">Grounded on</h3>
            {Array.isArray(analysis.grounded_on) && analysis.grounded_on.length > 0 ? (
              <ul className="grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
                {analysis.grounded_on.map((g) => (
                  <li
                    key={g}
                    className="flex items-center gap-1.5 font-mono text-[11px] text-tx-secondary"
                  >
                    <span className="text-tx-tertiary" aria-hidden="true">
                      →
                    </span>
                    {g}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-tx-tertiary">None available.</p>
            )}
          </section>

          <footer className="flex flex-wrap items-center gap-x-6 gap-y-1 border-t border-line pt-3 text-[11px] text-tx-tertiary">
            <span>
              Model: <span className="font-mono">{analysis.model ?? "—"}</span>
            </span>
            <span>
              Generated:{" "}
              <span className="font-mono">
                {analysis.generated_at
                  ? new Date(analysis.generated_at).toLocaleString()
                  : "—"}
              </span>
            </span>
            <span className="text-amber-400/90">
              AI-generated — verify before acting.
            </span>
          </footer>
        </div>
      )}
    </section>
  );
}