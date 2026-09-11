"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/ThemeContext";
import { UserGuideModal } from "@/components/shared/UserGuideModal";
import { RemediationPlaybookModal } from "@/components/dashboard/RemediationPlaybookModal";

const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "true";

function crumbPath(pathname: string): string[] {
  if (pathname === "/") return ["CyberYukti", "Triage Overview"];
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return ["CyberYukti", "Triage Overview"];
  if (segments[0] === "cases") {
    if (segments.length >= 2) return ["CyberYukti", "Case", segments[1]];
    return ["CyberYukti", "Triage Queue"];
  }
  if (segments[0] === "vulnerabilities") {
    return ["CyberYukti", "Intake Console", "New Finding"];
  }
  return ["CyberYukti", segments.join(" / ").toUpperCase()];
}

export function TopHeader() {
  const pathname = usePathname();
  const crumbs = crumbPath(pathname);
  const { theme, toggleTheme } = useTheme();
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [isPlaybookOpen, setIsPlaybookOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-line bg-graphite-raised/95 backdrop-blur-md px-5 lg:px-6 transition-colors">
      <div className="flex min-w-0 items-center gap-3">
        {/* Mobile brand + quick links */}
        <div className="flex items-center gap-3 overflow-hidden lg:hidden">
          <span className="shrink-0 text-sm font-bold tracking-tight text-tx-primary flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
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
            <Link
              href="/vulnerabilities/new"
              className="px-2 py-1 text-xs font-semibold text-accent"
            >
              + Ingest
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

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        {/* P1 Playbook Action Button */}
        <button
          type="button"
          onClick={() => setIsPlaybookOpen(true)}
          className="hidden md:inline-flex items-center gap-1.5 rounded-md bg-red-950/40 px-2.5 py-1.5 text-xs font-semibold text-red-400 border border-red-500/40 hover:bg-red-900/50 hover:border-red-400 transition-all shadow-sm"
        >
          <span>🛠️</span>
          <span>P1 Playbooks</span>
        </button>

        {/* User Guide Action Button */}
        <button
          type="button"
          onClick={() => setIsGuideOpen(true)}
          className="hidden sm:inline-flex items-center gap-1.5 rounded-md bg-emerald-950/40 px-2.5 py-1.5 text-xs font-semibold text-emerald-400 border border-emerald-500/40 hover:bg-emerald-900/50 hover:border-emerald-400 transition-all shadow-sm"
        >
          <span>📖</span>
          <span>User Guide</span>
        </button>

        {/* Quick Report Vulnerability Action */}
        <Link
          href="/vulnerabilities/new"
          className="hidden sm:inline-flex items-center gap-1.5 rounded-md bg-accent/15 px-2.5 py-1.5 text-xs font-semibold text-accent border border-accent/30 hover:bg-accent/25 hover:border-accent/60 transition-all shadow-sm shadow-accent/10"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span>Report Vulnerability</span>
        </Link>

        {/* Theme Toggle Button (Light / Dark) */}
        <button
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          title={`Currently on ${theme} mode. Click to switch to ${theme === "dark" ? "light" : "dark"} mode.`}
          className="relative flex h-8 w-8 items-center justify-center rounded-md border border-line bg-graphite text-tx-secondary hover:border-line-strong hover:text-tx-primary transition-all focus:outline-none"
        >
          {theme === "dark" ? (
            /* Sun Icon for Dark mode -> switches to Light */
            <svg
              className="h-4 w-4 text-amber-400 transition-transform duration-300 hover:rotate-45"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"
              />
            </svg>
          ) : (
            /* Moon Icon for Light mode -> switches to Dark */
            <svg
              className="h-4 w-4 text-indigo-600 transition-transform duration-300 hover:-rotate-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
              />
            </svg>
          )}
        </button>

        {/* Live API / Demo Radar Dot */}
        <div
          className="flex items-center gap-2 rounded border border-line bg-graphite px-2 py-1"
          title={
            isMock
              ? "Mock data enabled. Set NEXT_PUBLIC_USE_MOCK=false to connect to a real API."
              : "Connected to the live CyberYukti API."
          }
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                isMock ? "bg-amber-400" : "bg-emerald-400"
              }`}
            />
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                isMock ? "bg-amber-500" : "bg-emerald-500"
              }`}
            />
          </span>
          <span className="hk-label text-[9px]">
            {isMock ? "Demo data" : "Live API"}
          </span>
        </div>

        <span className="hidden h-4 w-px bg-line-strong sm:block" aria-hidden="true" />
        
        {/* User Profile Avatar with Popover */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setUserMenuOpen((prev) => !prev)}
            onBlur={() => setTimeout(() => setUserMenuOpen(false), 200)}
            className="group flex items-center gap-2 rounded-full border border-line bg-graphite p-1 pr-2.5 hover:border-accent/50 hover:bg-accent-soft transition-all focus:outline-none"
            aria-label="User Profile"
            title="Active Analyst: analyst-1 (Lead SOC Triage)"
          >
            <div className="relative flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 border border-accent/30 text-accent group-hover:border-accent transition-colors">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-graphite" />
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-[11px] font-bold text-tx-primary leading-none">
                analyst-1
              </span>
              <span className="text-[9px] font-mono uppercase text-accent font-semibold leading-none mt-0.5">
                SOC Lead
              </span>
            </div>
            <svg className="hidden sm:block h-3 w-3 text-tx-tertiary group-hover:text-tx-primary transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>

          {/* User Popover Menu */}
          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-line bg-graphite p-3.5 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center gap-3 pb-3 border-b border-line">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/20 border border-accent/40 text-accent font-bold">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-tx-primary">Alex Mercer</h4>
                  <p className="text-[10.5px] font-mono text-accent">@analyst-1 (Lead)</p>
                </div>
              </div>
              <div className="py-2.5 space-y-1.5 text-[11px] text-tx-secondary">
                <div className="flex justify-between">
                  <span className="hk-label text-[9.5px]">Clearance</span>
                  <span className="font-semibold text-emerald-500 dark:text-emerald-400">Level 3 (Commander)</span>
                </div>
                <div className="flex justify-between">
                  <span className="hk-label text-[9.5px]">Attestation Seal</span>
                  <span className="font-mono text-[10px] text-tx-primary">HMAC-SHA256 Ready</span>
                </div>
                <div className="flex justify-between">
                  <span className="hk-label text-[9.5px]">Active Session</span>
                  <span className="flex items-center gap-1 text-emerald-500 text-[10px]">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Online (Verified)
                  </span>
                </div>
              </div>
              <div className="pt-2 border-t border-line">
                <span className="text-[9.5px] font-mono uppercase tracking-wider text-tx-tertiary block text-center">
                  ISO-27001 / SOC-2 Audited Role
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Modals */}
      <UserGuideModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />
      <RemediationPlaybookModal isOpen={isPlaybookOpen} onClose={() => setIsPlaybookOpen(false)} />
    </header>
  );
}