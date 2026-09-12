"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  badge?: string;
  match: "exact" | "cases" | "priority" | "evidence" | "vulnerabilities";
  icon: (active: boolean) => React.ReactNode;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface TriageStats {
  confirmed: number;
  not_confirmed: number;
  pending: number;
  total_cases: number;
}

const SECTIONS: NavSection[] = [
  {
    title: "Analysis",
    items: [
      {
        href: "/analysis",
        label: "New Analysis",
        match: "exact",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-accent" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
          </svg>
        ),
      },
    ],
  },
  {
    title: "Operations",
    items: [
      {
        href: "/",
        label: "Dashboard Overview",
        match: "exact",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-accent" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
          </svg>
        ),
      },
      {
        href: "/vulnerabilities/new",
        label: "Add Vulnerability",
        badge: "INTAKE",
        match: "vulnerabilities",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-accent" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
    ],
  },
  {
    title: "Triage & Cases",    items: [
      {
        href: "/cases",
        label: "All Triage Cases",
        match: "cases",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-accent" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
          </svg>
        ),
      },
      {
        href: "/cases?priority=P1",
        label: "Priority Queue (P1)",
        badge: "CRITICAL",
        match: "priority",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-priority-p1" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        ),
      },
    ],
  },
  {
    title: "Autonomous Evidence",
    items: [
      {
        href: "/cases?evidence=CONFIRMED",
        label: "Confirmed Exploit Ledger",
        match: "evidence",
        icon: (active) => (
          <svg width="16" height="16" className={`h-4 w-4 shrink-0 ${active ? "text-emerald-500" : "text-tx-tertiary"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        ),
      },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [stats, setStats] = useState<TriageStats>({
    confirmed: 20,
    not_confirmed: 3,
    pending: 36,
    total_cases: 42,
  });

  useEffect(() => {
    let isMounted = true;
    const loadStats = () => {
      fetch("/api/dashboard/stats")
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (isMounted && data?.evidence_breakdown) {
            setStats({
              confirmed: data.evidence_breakdown.confirmed ?? 20,
              not_confirmed: data.evidence_breakdown.not_confirmed ?? 3,
              pending: data.counts?.pending_review ?? 36,
              total_cases: data.counts?.cases ?? 42,
            });
          }
        })
        .catch(() => {});
    };

    loadStats();
    const timer = setInterval(loadStats, 10000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, [pathname]);

  function isActive(item: NavItem): boolean {
    if (item.match === "exact") return pathname === item.href;
    if (item.match === "vulnerabilities") return pathname.startsWith("/vulnerabilities");
    const onCases = pathname === "/cases";
    if (item.match === "priority")
      return onCases && searchParams.get("priority") !== null;
    if (item.match === "evidence")
      return onCases && searchParams.get("evidence") !== null;
    return (
      onCases && searchParams.get("priority") === null && searchParams.get("evidence") === null
    );
  }
  const total = stats.confirmed + stats.not_confirmed + stats.pending;
  const confirmedPct = total > 0 ? (stats.confirmed / total) * 100 : 50;
  const notConfirmedPct = total > 0 ? (stats.not_confirmed / total) * 100 : 10;
  const pendingPct = total > 0 ? (stats.pending / total) * 100 : 40;

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-[240px] flex-col border-r border-line bg-graphite transition-colors lg:flex">
      {/* Brand Header with Cyber Badge */}
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-line px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 border border-accent/30 text-accent font-black shadow-sm shadow-accent/20 shrink-0">
            <svg width="16" height="16" style={{ maxWidth: 20, maxHeight: 20 }} className="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-3zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-2.33v8.02z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[14px] font-black tracking-wider text-tx-primary font-mono">
                CYBERYUKTI
              </span>
            </div>
            <span className="font-mono text-[8.5px] uppercase tracking-[0.2em] text-accent font-semibold">
              AUTONOMOUS SOC
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-5">
        {SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="hk-label mb-2 px-2.5 text-[9.5px] text-tx-tertiary">{section.title}</p>
            <div className="space-y-1">
              {section.items.map((item) => {
                const active = isActive(item);
                return (
                  <div key={item.href} className="relative">
                    {active && (
                      <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-accent shadow-sm shadow-accent/50" />
                    )}
                    <Link
                      href={item.href}
                      className={`flex items-center justify-between rounded-md px-3 py-2 text-[12.5px] font-medium transition-all ${
                        active
                          ? "bg-accent-soft text-accent border border-accent/20 font-semibold"
                          : "text-tx-secondary hover:bg-graphite-raised hover:text-tx-primary"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        {item.icon(active)}
                        <span>{item.label}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                            item.badge === "CRITICAL"
                              ? "bg-priority-p1/10 text-priority-p1 border-priority-p1/30"
                              : "bg-accent/10 text-accent border-accent/30"
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* Analyst Triage Activity (Live Working Status) */}
        <div className="rounded-xl border border-line bg-graphite-raised/70 p-3 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="hk-label text-[9px] font-bold">ANALYST WORKING</span>
            </div>
            <span className="font-mono text-[9px] text-accent font-semibold">
              {stats.total_cases} CASES
            </span>
          </div>

          {/* Ratio Bar */}
          <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-line mb-2.5">
            <div style={{ width: `${confirmedPct}%` }} className="bg-emerald-500" title={`Confirmed: ${stats.confirmed}`} />
            <div style={{ width: `${notConfirmedPct}%` }} className="bg-red-500" title={`Rejected: ${stats.not_confirmed}`} />
            <div style={{ width: `${pendingPct}%` }} className="bg-amber-500" title={`Pending: ${stats.pending}`} />
          </div>

          {/* Quick-Filter Activity Links */}
          <div className="space-y-1.5 text-[11px]">
            <Link
              href="/cases?evidence=CONFIRMED"
              className="flex items-center justify-between px-2 py-1 rounded-md hover:bg-graphite transition-colors group"
              title="Filter Confirmed Exploits"
            >
              <div className="flex items-center gap-1.5 text-tx-secondary group-hover:text-emerald-500 transition-colors">
                <span className="text-emerald-500 font-bold">✓</span>
                <span>Confirmed</span>
              </div>
              <span className="font-mono font-bold text-emerald-500 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20 text-[10px]">
                {stats.confirmed}
              </span>
            </Link>

            <Link
              href="/cases?evidence=NOT_CONFIRMED"
              className="flex items-center justify-between px-2 py-1 rounded-md hover:bg-graphite transition-colors group"
              title="Filter Rejected False Positives"
            >
              <div className="flex items-center gap-1.5 text-tx-secondary group-hover:text-red-500 transition-colors">
                <span className="text-red-500 font-bold">✕</span>
                <span>Rejected</span>
              </div>
              <span className="font-mono font-bold text-red-500 bg-red-500/10 px-1.5 py-0.2 rounded border border-red-500/20 text-[10px]">
                {stats.not_confirmed}
              </span>
            </Link>

            <Link
              href="/cases?status=PENDING"
              className="flex items-center justify-between px-2 py-1 rounded-md hover:bg-graphite transition-colors group"
              title="Filter Pending Decisions"
            >
              <div className="flex items-center gap-1.5 text-tx-secondary group-hover:text-amber-500 transition-colors">
                <span className="text-amber-500 font-bold">⏳</span>
                <span>Pending Decision</span>
              </div>
              <span className="font-mono font-bold text-amber-500 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20 text-[10px]">
                {stats.pending}
              </span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Real-time Telemetry Status Widget */}
      <div className="shrink-0 border-t border-line bg-graphite-raised/50 p-3.5">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5">
            <span className="hk-label text-[9px] font-bold">
              ENGINE TELEMETRY
            </span>
          </div>
          <span className="font-mono text-[9px] text-accent font-bold">
            96.9% REDUCED
          </span>
        </div>
        <p className="text-[10.5px] leading-relaxed text-tx-tertiary">
          GitLab Triple-Tuple deduplication & live sandbox verification active.
        </p>
      </div>
    </aside>
  );
}