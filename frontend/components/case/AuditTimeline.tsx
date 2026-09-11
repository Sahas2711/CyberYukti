import type { AuditEvent } from "@/lib/api/types";

interface Props {
  events: AuditEvent[];
}

const actorColors: Record<string, string> = {
  system: "text-sky-400",
  analyst: "text-accent",
  ai: "text-violet-400",
};

const actorBg: Record<string, string> = {
  system: "border-sky-500/40 bg-sky-500/10",
  analyst: "border-accent/40 bg-accent-soft",
  ai: "border-violet-500/40 bg-violet-500/10",
};

function actorLabel(actor?: string): string {
  const label = actor ?? "unknown";
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return "—";
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString();
}

function reasonFor(event: AuditEvent): string | null {
  const reason = event?.new_state?.reason;
  return typeof reason === "string" && reason.trim() ? reason : null;
}

function statusOf(state: Record<string, unknown> | undefined): string {
  const status = state?.status;
  return typeof status === "string" ? status : "—";
}

function priorityTransition(event: AuditEvent): { from?: string; to?: string } | null {
  if (event.action !== "override") return null;
  const metadata = event.metadata as { old_priority?: string; new_priority?: string };
  return metadata?.old_priority || metadata?.new_priority
    ? { from: metadata.old_priority, to: metadata.new_priority }
    : null;
}

export function AuditTimeline({ events }: Props) {
  const list = Array.isArray(events) ? events : [];

  if (list.length === 0) {
    return (
      <section className="rounded-sm border border-dashed border-line-strong bg-graphite py-12 text-center">
        <h2 className="hk-label">Audit Trail</h2>
        <p className="mt-2 text-xs text-tx-secondary">No audit events recorded.</p>
      </section>
    );
  }

  const sorted = [...list].sort(
    (a, b) =>
      new Date(b.timestamp ?? 0).getTime() - new Date(a.timestamp ?? 0).getTime()
  );
  const chained = sorted.some((e) => typeof e.prev_hash === "string");

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <div>
          <h2 className="hk-label">Audit Trail</h2>
          <p className="mt-0.5 text-[11px] text-tx-tertiary">
            Append-only event log · newest first
          </p>
        </div>
        {chained && (
          <span className="rounded-sm border border-line-strong bg-graphite-deep px-1.5 py-[3px] font-mono text-[10px] uppercase tracking-wider text-tx-secondary">
            Linked events · prev_hash
          </span>
        )}
      </header>

      <ol className="mx-4 my-4 space-y-5 border-l border-line pl-5">
        {sorted.map((event) => {
          const reason = reasonFor(event);
          const transition = priorityTransition(event);
          const label = actorLabel(event.actor);
          const metaKey = event.metadata && Object.keys(event.metadata).length > 0;
          return (
            <li key={event.event_id} className="relative">
              <span
                className="absolute -left-[26px] top-1 h-2 w-2 rounded-full border border-line-strong bg-graphite-deep"
                aria-hidden="true"
              />
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <time
                  className="font-mono text-[11px] text-tx-tertiary"
                  dateTime={event.timestamp}
                >
                  {formatTimestamp(event.timestamp)}
                </time>
                <span
                  className={`rounded-sm border px-1.5 py-[2px] text-[9px] font-semibold uppercase tracking-[0.12em] ${
                    actorBg[event.actor ?? ""] ?? "border-line-strong bg-graphite-deep"
                  } ${actorColors[event.actor ?? ""] ?? "text-tx-secondary"}`}
                >
                  {label}
                </span>
                {event.actor_id && (
                  <span className="font-mono text-[11px] text-tx-tertiary">
                    {event.actor_id}
                  </span>
                )}
              </div>

              <p className="mt-1 text-sm text-tx-primary">
                {event.action ?? "acted"}
              </p>

              {transition && (
                <p className="mt-0.5 font-mono text-[11px] text-violet-300">
                  {transition.from || "—"}
                  <span className="mx-1.5 text-tx-tertiary" aria-hidden="true">
                    →
                  </span>
                  {transition.to || "—"}
                </p>
              )}

              <div className="mt-1.5 text-xs text-tx-secondary">
                State:{" "}
                <span className="font-mono text-tx-primary">
                  {statusOf(event.previous_state)}
                </span>{" "}
                <span className="text-tx-tertiary" aria-hidden="true">
                  →
                </span>{" "}
                <span className="font-mono text-tx-primary">
                  {statusOf(event.new_state)}
                </span>
              </div>

              {reason && (
                <p className="mt-1 text-xs text-tx-secondary">
                  <span className="hk-label">Reason</span> {reason}
                </p>
              )}

              {metaKey && (
                <p className="mt-0.5 font-mono text-[10px] text-tx-tertiary">
                  {Object.entries(event.metadata as Record<string, unknown>)
                    .map(([key, value]) => `${key}: ${String(value)}`)
                    .join(" · ")}
                </p>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}