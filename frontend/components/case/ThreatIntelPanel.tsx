import { Tooltip } from "@/components/shared/Tooltip";
import type { TriageCase } from "@/lib/api/types";

interface Props {
  threatIntel: TriageCase["threat_intelligence"];
}

const CVSS_TOOLTIP =
  "Common Vulnerability Scoring System v3 score (0-10). Higher scores indicate more severe vulnerabilities.";
const EPSS_TOOLTIP =
  "Exploit Prediction Scoring System probability (0-1) that the vulnerability will be exploited in the next 30 days. Higher means more likely to be exploited.";
const KEV_TOOLTIP =
  "CISA Known Exploited Vulnerabilities catalog. Yes means the vulnerability is being actively exploited in the wild.";

function cvssColor(score?: number): string {
  if (typeof score !== "number" || Number.isNaN(score)) return "text-tx-tertiary";
  if (score >= 9) return "text-red-400";
  if (score >= 7) return "text-orange-400";
  if (score >= 4) return "text-yellow-400";
  return "text-green-400";
}

function formatEpss(epss?: number): string {
  if (typeof epss !== "number" || Number.isNaN(epss)) return "—";
  return `${(epss * 100).toFixed(1)}%`;
}

function KevBadge({ kev }: { kev?: boolean }) {
  if (kev === undefined) {
    return (
      <span className="inline-flex items-center rounded-sm border border-line-strong bg-graphite-deep px-1.5 py-[3px] text-[10px] font-semibold uppercase tracking-wider text-tx-tertiary">
        Unknown
      </span>
    );
  }
  return kev ? (
    <span className="inline-flex items-center rounded-sm border border-red-500/40 bg-red-500/10 px-1.5 py-[3px] text-[10px] font-semibold uppercase tracking-wider text-red-400">
      Yes
    </span>
  ) : (
    <span className="inline-flex items-center rounded-sm border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-[3px] text-[10px] font-semibold uppercase tracking-wider text-emerald-400">
      No
    </span>
  );
}

export function ThreatIntelPanel({ threatIntel }: Props) {
  if (!threatIntel) return null;

  return (
    <section className="rounded-sm border border-line bg-graphite">
      <header className="border-b border-line px-4 py-3">
        <h2 className="hk-label">Threat Context</h2>
        <p className="mt-0.5 text-[11px] text-tx-tertiary">
          External severity and exploitation signals
        </p>
      </header>
      <div className="grid grid-cols-3 gap-4 p-4">
        <div>
          <Tooltip content={CVSS_TOOLTIP}>
            <p className="hk-label cursor-help">CVSS</p>
          </Tooltip>
          <p
            className={`mt-1.5 text-2xl font-semibold tabular-nums ${cvssColor(
              threatIntel.cvss
            )}`}
          >
            {typeof threatIntel.cvss === "number" ? threatIntel.cvss.toFixed(1) : "—"}
          </p>
          <p className="mt-1 text-[10px] text-tx-tertiary">technical severity</p>
        </div>
        <div>
          <Tooltip content={EPSS_TOOLTIP}>
            <p className="hk-label cursor-help">EPSS</p>
          </Tooltip>
          <p className="mt-1.5 text-2xl font-semibold tabular-nums text-tx-primary">
            {formatEpss(threatIntel.epss)}
          </p>
          <p className="mt-1 text-[10px] text-tx-tertiary">exploit probability</p>
        </div>
        <div>
          <Tooltip content={KEV_TOOLTIP}>
            <p className="hk-label cursor-help">KEV</p>
          </Tooltip>
          <div className="mt-2">
            <KevBadge kev={threatIntel.kev} />
          </div>
          <p className="mt-1 text-[10px] text-tx-tertiary">known exploited</p>
        </div>
      </div>
    </section>
  );
}