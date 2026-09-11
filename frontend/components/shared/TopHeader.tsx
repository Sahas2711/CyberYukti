"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const isMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

function crumbPath(pathname: string): string[] {
  if (pathname === "/") return ["CyberYukti", "Triage Overview"];
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return ["CyberYukti", "Triage Overview"];
  if (segments[0] === "cases") {
    if (segments.length >= 2) return ["CyberYukti", "Case", segments[1]];
    return ["CyberYukti", "Triage Queue"];
  }
  return ["CyberYukti", segments.join(" / ").toUpperCase()];
}

export function TopHeader() {
  const pathname = usePathname();
  const crumbs = crumbPath(pathname);

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-line bg-graphite-raised px-5 lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        {/* Mobile brand + quick links (sidebar hidden below lg) */}
        <div className="flex items-center gap-3 overflow-hidden lg:hidden">
          <span className="shrink-0 text-sm font-bold tracking-tight text-white">
            CYBERYUKTI
          </span>
          <nav className="flex shrink-0 items-center gap-1">
            <Link
              href="/"
              className="px-2 py-1 text-xs font-medium text-tx-secondary hover:text-tx-primary"
            >
              Dashboard
            </Link>
            <Link
              href="/cases"
              className="px-2 py-1 text-xs font-medium text-tx-secondary hover:text-tx-primary"
            >
              Cases
            </Link>
          </nav>
        </div>

        {/* Breadcrumb context */}
        <nav className="hidden items-center gap-2 text-xs lg:flex" aria-label="Context">
          {crumbs.map((crumb, index) => (
            <span key={`${crumb}-${index}`} className="flex items-center gap-2">
              {index > 0 && (
                <span className="text-tx-tertiary" aria-hidden="true">
                  /
                </span>
              )}
              <span
                className={
                  index === crumbs.length - 1
                    ? "font-medium text-tx-primary"
                    : "text-tx-tertiary"
                }
              >
                {crumb}
              </span>
            </span>
          ))}
        </nav>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div
          className="flex items-center gap-2"
          title={
            isMock
              ? "Mock data enabled. Set NEXT_PUBLIC_USE_MOCK=false to connect to a real API."
              : "Connected to the live CyberYukti API."
          }
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isMock ? "bg-amber-400" : "bg-emerald-400"
            }`}
            aria-hidden="true"
          />
          <span className="hk-label">
            {isMock ? "Demo data" : "Live API"}
          </span>
        </div>
        <span className="hidden h-4 w-px bg-line-strong sm:block" aria-hidden="true" />
        <span className="hidden items-center gap-1.5 sm:flex">
          <span className="hk-label">Analyst</span>
          <span className="font-mono text-xs font-medium text-tx-secondary">
            analyst-1
          </span>
        </span>
      </div>
    </header>
  );
}