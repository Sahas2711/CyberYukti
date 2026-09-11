"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "true";

interface NavItem {
  href: string;
  label: string;
  match: "exact" | "cases" | "priority" | "evidence";
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [{ href: "/", label: "Dashboard", match: "exact" }],
  },
  {
    title: "Analysis",
    items: [{ href: "/analysis", label: "New Analysis", match: "exact" }],
  },
  {
    title: "Triage",
    items: [
      { href: "/cases", label: "Cases", match: "cases" },
      { href: "/cases?priority=P1", label: "Priority Queue", match: "priority" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { href: "/cases?evidence=CONFIRMED", label: "Evidence Queue", match: "evidence" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

function isActive(item: NavItem): boolean {
  if (item.match === "exact") return pathname === item.href;
  const onCases = pathname === "/cases";
  if (item.match === "priority")
    return onCases && searchParams.get("priority") !== null;
  if (item.match === "evidence")
    return onCases && searchParams.get("evidence") !== null;
  return (
    onCases && searchParams.get("priority") === null && searchParams.get("evidence") === null
  );
}

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-[232px] flex-col border-r border-line bg-graphite lg:flex">
      <div className="flex h-14 shrink-0 items-center border-b border-line px-5">
        <div className="flex items-baseline gap-2">
          <span className="text-[15px] font-bold tracking-tight text-white">
            CYBERYUKTI
          </span>
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-tx-tertiary">
            SOC
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {SECTIONS.map((section) => (
          <div key={section.title} className="mb-5">
            <p className="hk-label mb-2 px-2">{section.title}</p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item);
                return (
                  <div key={item.href} className="relative">
                    {active && (
                      <span className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-full bg-accent" />
                    )}
                    <Link
                      href={item.href}
                      className={`block rounded-sm px-3 py-[7px] text-[13px] transition-colors ${
                        active
                          ? "bg-graphite-deep font-medium text-tx-primary"
                          : "text-tx-secondary hover:bg-graphite-deep/60 hover:text-tx-primary"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="shrink-0 border-t border-line px-5 py-4">
        <div className="flex items-center gap-2">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isMock ? "bg-amber-400" : "bg-emerald-400"
            }`}
            aria-hidden="true"
          />
          <span className="hk-label">
            {isMock ? "Demo environment" : "Live API"}
          </span>
        </div>
        <p className="mt-1 text-[11px] leading-relaxed text-tx-tertiary">
          {isMock
            ? "Mock data enabled. Set NEXT_PUBLIC_USE_MOCK=false to connect to a real API."
            : "Connected to the CyberYukti backend."}
        </p>
      </div>
    </aside>
  );
}