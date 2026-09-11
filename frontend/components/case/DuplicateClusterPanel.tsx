interface Props {
  sources: string[];
  findingCount: number;
  clusterId: string;
}

export function DuplicateClusterPanel({
  sources,
  findingCount,
  clusterId,
}: Props) {
  const sourceList = Array.isArray(sources) ? sources.filter(Boolean) : [];

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="border-b border-line px-4 py-3">
        <h2 className="hk-label">Duplicate Cluster</h2>
        <p className="mt-0.5 text-[11px] text-tx-tertiary">
          Findings normalized and deduplicated
        </p>
      </header>
      <div className="p-4">
        <ol className="flex flex-col items-center gap-1.5 sm:flex-row sm:justify-center sm:gap-3">
          <li className="flex flex-col items-center px-4 py-2 sm:py-0">
            <span className="text-3xl font-semibold tabular-nums text-tx-primary">
              {findingCount ?? 0}
            </span>
            <span className="hk-label mt-1">Findings</span>
          </li>
          <li className="flex items-center" aria-hidden="true">
            <span className="text-tx-tertiary">↓</span>
          </li>
          <li className="flex flex-col items-center px-4 py-2 sm:py-0">
            <span className="text-3xl font-semibold tabular-nums text-accent">
              1
            </span>
            <span className="hk-label mt-1">Cluster</span>
          </li>
          <li className="flex items-center" aria-hidden="true">
            <span className="text-tx-tertiary">↓</span>
          </li>
          <li className="flex flex-col items-center px-4 py-2 sm:py-0">
            <span className="text-3xl font-semibold tabular-nums text-accent">
              1
            </span>
            <span className="hk-label mt-1">Triage Case</span>
          </li>
        </ol>

        <div className="mt-4 border-t border-line pt-3">
          <p className="hk-label mb-2">Origins</p>
          <div className="flex flex-wrap items-center gap-1.5">
            {sourceList.length === 0 ? (
              <span className="text-xs text-tx-tertiary">No sources recorded</span>
            ) : (
              sourceList.map((source) => (
                <span
                  key={source}
                  className="rounded-sm border border-line-strong bg-graphite-deep px-2 py-0.5 font-mono text-[11px] text-tx-secondary"
                >
                  {source}
                </span>
              ))
            )}
          </div>
          {clusterId && (
            <p className="mt-2 font-mono text-[11px] text-tx-tertiary">
              Cluster {clusterId}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}