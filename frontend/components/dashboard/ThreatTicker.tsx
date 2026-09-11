"use client";

import { useEffect, useState } from "react";

const TELEMETRY_FEED = [
  {
    tag: "INGESTION & DEDUP",
    color: "text-accent border-accent/40 bg-accent/10",
    text: "Trivy (25) + Semgrep (12) + Nuclei (5) collapsed: 42 raw findings → 4 actionable clusters (90.48% noise reduced)",
  },
  {
    tag: "CROSS-TOOL CORRELATION",
    color: "text-purple-400 border-purple-500/40 bg-purple-500/10",
    text: "Semgrep SAST in handlers/static.py correlated with Nuclei DAST route /api/static/download [CWE-22]",
  },
  {
    tag: "AUTONOMOUS PROOF ENGINE",
    color: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10",
    text: "CASE-001 exploit verification confirmed in secure sandbox container (Proof confidence: 94%)",
  },
  {
    tag: "RISK ENGINE (PERSON 3)",
    color: "text-rose-400 border-rose-500/40 bg-rose-500/10",
    text: "Dynamic risk score computed: P1 (91.8/100) — Internet exposed + CISA KEV Active + Exploit verified",
  },
];

export function ThreatTicker() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % TELEMETRY_FEED.length);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const current = TELEMETRY_FEED[currentIndex];

  return (
    <div className="relative overflow-hidden rounded-md border border-line bg-graphite px-4 py-2 shadow-sm transition-all duration-300">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 overflow-hidden">
          {/* Radar indicator */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
            <span className="font-mono text-[10px] font-bold tracking-widest text-tx-secondary uppercase">
              LIVE SOC STREAM
            </span>
          </div>

          <span className="h-3 w-px bg-line-strong shrink-0" aria-hidden="true" />

          {/* Current telemetry banner with keyframe fade */}
          <div key={currentIndex} className="flex items-center gap-2 overflow-hidden animate-fadeIn">
            <span className={`font-mono text-[9px] font-bold px-2 py-0.5 rounded border uppercase shrink-0 ${current.color}`}>
              {current.tag}
            </span>
            <span className="truncate text-xs text-tx-secondary font-mono">
              {current.text}
            </span>
          </div>
        </div>

        {/* Carousel controls indicator */}
        <div className="hidden sm:flex items-center gap-1 shrink-0">
          {TELEMETRY_FEED.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              className={`h-1.5 rounded-full transition-all ${
                idx === currentIndex ? "w-4 bg-accent" : "w-1.5 bg-line-strong hover:bg-tx-tertiary"
              }`}
              aria-label={`Slide ${idx + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
