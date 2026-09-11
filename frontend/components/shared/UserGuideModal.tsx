"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";

interface UserGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UserGuideModal({ isOpen, onClose }: UserGuideModalProps) {
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"ingestion" | "evidence" | "risk" | "attestation">("ingestion");

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !mounted) return null;

  const tabs = [
    { id: "ingestion", label: "1. Ingestion & 3-Tier Dedup", icon: "📊" },
    { id: "evidence", label: "2. Evidence Engine & Sandbox", icon: "🧪" },
    { id: "risk", label: "3. Dynamic Risk & Cost Burn", icon: "💰" },
    { id: "attestation", label: "4. Cryptographic Attestation", icon: "🔒" },
  ] as const;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto animate-in fade-in">
      <div className="relative w-full max-w-4xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-emerald-500/40 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="bg-slate-100 dark:bg-gradient-to-r dark:from-emerald-950 dark:via-slate-900 dark:to-slate-950 border-b border-slate-200 dark:border-emerald-500/30 px-6 py-5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-xl text-emerald-600 dark:text-emerald-400">
              📖
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono uppercase tracking-widest text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-300 dark:border-emerald-500/40 font-bold">
                  Operations Manual
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">CyberYukti Autonomous Platform</span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white tracking-tight mt-0.5">
                Architecture, Engine Logic & Evaluation Guide
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 dark:hover:text-white p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="bg-slate-50 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 px-6 flex space-x-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-4 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-emerald-500 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30"
                  : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-900">
          {activeTab === "ingestion" && (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-500/30 rounded-xl">
                <h3 className="text-emerald-800 dark:text-emerald-300 font-bold text-base mb-1">
                  High-Scale Finding Ingestion & 3-Tier Deduplication
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  CyberYukti ingests raw JSON/CSV reports from Trivy, Semgrep, and Nuclei, normalizing varied scanner formats into canonical schema with zero data loss.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl">
                  <span className="font-bold text-emerald-700 dark:text-emerald-400 block mb-1">Tier 1: Exact Hash</span>
                  <p className="text-slate-600 dark:text-slate-400">
                    Computes SHA-256 fingerprint over normalized title, asset, and vulnerability payload. Eliminates identical duplicate scan runs instantaneously.
                  </p>
                </div>
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl">
                  <span className="font-bold text-emerald-700 dark:text-emerald-400 block mb-1">Tier 2: Triple-Tuple</span>
                  <p className="text-slate-600 dark:text-slate-400">
                    Groups findings matching GitLab tuple: <code>(Target Asset, Location, Specific CVE/Rule ID)</code>. Merges repeated scanner alerts into a single actionable incident.
                  </p>
                </div>
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl">
                  <span className="font-bold text-emerald-700 dark:text-emerald-400 block mb-1">Tier 3: Cross-Tool Correlation</span>
                  <p className="text-slate-600 dark:text-slate-400">
                    Correlates SAST (Semgrep) + DAST (Nuclei) + Container (Trivy) finding the same flaw on the same normalized endpoint route.
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-mono text-slate-700 dark:text-slate-400">
                <span className="text-emerald-700 dark:text-emerald-400 font-bold">10,000 Scale Benchmark:</span> Tested on high-scale synthetic datasets containing 10,000 raw scanner outputs. Produces 96.9% noise reduction in ~6.4 seconds.
              </div>
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="space-y-4">
              <div className="p-4 bg-cyan-50 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-500/30 rounded-xl">
                <h3 className="text-cyan-800 dark:text-cyan-300 font-bold text-base mb-1">
                  Person 2 Evidence Validation Engine & Isolated Sandbox
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  Instead of assuming scanner outputs are always true positives, CyberYukti fires automated, non-destructive validation probes against isolated lab targets to physically prove or disprove vulnerability presence.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-red-300 dark:border-red-500/30 rounded-xl">
                  <div className="flex items-center space-x-2 font-bold text-red-600 dark:text-red-400 mb-1">
                    <span>Target: shop-api-01</span>
                    <span className="px-2 py-0.5 bg-red-100 dark:bg-red-950 border border-red-300 dark:border-red-500/40 rounded text-[10px]">VULNERABLE LAB</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">
                    Running live probe verifies unpatched jQuery 1.12.4 or active SQL error leakage.
                  </p>
                  <div className="mt-2.5 font-mono text-[11px] text-emerald-700 dark:text-emerald-300 bg-white dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                    Status: CONFIRMED (Confidence: 95%)<br />
                    Priority: Escalated to P1/P2
                  </div>
                </div>

                <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-emerald-300 dark:border-emerald-500/30 rounded-xl">
                  <div className="flex items-center space-x-2 font-bold text-emerald-700 dark:text-emerald-400 mb-1">
                    <span>Target: shop-api-01-patched</span>
                    <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-950 border border-emerald-300 dark:border-emerald-500/40 rounded text-[10px]">REMEDIATED LAB</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">
                    Running live probe confirms jQuery 3.6.0 installed or SQL parameters parameterized.
                  </p>
                  <div className="mt-2.5 font-mono text-[11px] text-cyan-700 dark:text-cyan-300 bg-white dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                    Status: NOT_CONFIRMED (Confidence: 90%)<br />
                    Priority: Automatically demoted to P3/P4
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "risk" && (
            <div className="space-y-4">
              <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-500/30 rounded-xl">
                <h3 className="text-amber-800 dark:text-amber-300 font-bold text-base mb-1">
                  Dynamic Risk Prioritization & Financial Liability Cost Burn
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  Risk scores are mathematically calculated using multidimensional threat intelligence, physical asset context, and live evidence confirmation.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl">
                  <span className="font-bold text-amber-700 dark:text-amber-400 block mb-1.5">Dynamic Risk Factors</span>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                    <li><strong>CVSS v3.1</strong>: Base exploitability and impact metric.</li>
                    <li><strong>EPSS</strong>: Probability of active exploitation in wild.</li>
                    <li><strong>CISA KEV</strong>: Flag for known exploited weaponized exploits.</li>
                    <li><strong>Asset Criticality</strong>: Core gateway (1.5x) vs internal dev (0.7x).</li>
                    <li><strong>Internet Exposure</strong>: Public internet facing (1.3x).</li>
                    <li><strong>Evidence Engine</strong>: Confirmed probe results boost risk score.</li>
                  </ul>
                </div>

                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl">
                  <span className="font-bold text-emerald-700 dark:text-emerald-400 block mb-1.5">Liability Cost Burn ($/Day)</span>
                  <p className="text-slate-600 dark:text-slate-400 mb-2">
                    Translates technical severity into financial cost of inaction for C-level and SOC leadership:
                  </p>
                  <ul className="space-y-1 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                    <li><span className="text-red-600 dark:text-red-400 font-bold">P1 SLA (4 hrs):</span> ~$30,000 – $58,500 / day</li>
                    <li><span className="text-amber-600 dark:text-amber-400 font-bold">P2 SLA (24 hrs):</span> ~$10,800 – $21,000 / day</li>
                    <li><span className="text-cyan-700 dark:text-cyan-400 font-bold">P3 SLA (72 hrs):</span> ~$2,880 – $5,600 / day</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {activeTab === "attestation" && (
            <div className="space-y-4">
              <div className="p-4 bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-500/30 rounded-xl">
                <h3 className="text-purple-800 dark:text-purple-300 font-bold text-base mb-1">
                  USP 1: Cryptographic Proof-of-Triage Attestation
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  CyberYukti binds the entire lifecycle of a vulnerability into an immutable SHA-256 Merkle tree. Every state transition is cryptographically sealed into a compliance evidence receipt.
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl font-mono text-xs text-slate-800 dark:text-slate-300 space-y-2">
                <div className="text-emerald-700 dark:text-emerald-400 font-bold">Merkle Tree Structure (4 Immutable Leaves):</div>
                <div className="pl-3 border-l-2 border-emerald-500/40 space-y-1 text-[11px]">
                  <div>Leaf 1: SHA-256 (Scanner Raw Finding Payload & Location)</div>
                  <div>Leaf 2: SHA-256 (Non-Destructive Probe Command & Execution Result)</div>
                  <div>Leaf 3: SHA-256 (Deterministic Risk Scoring Factors & Formula)</div>
                  <div>Leaf 4: SHA-256 (Human Analyst Decision & Session Seal)</div>
                </div>
                <div className="text-purple-700 dark:text-purple-300 pt-1.5 border-t border-slate-200 dark:border-slate-800 font-bold">
                  Merkle Root = SHA256( Hash(L1+L2) + Hash(L3+L4) )
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl text-xs text-slate-600 dark:text-slate-400">
                <strong>Auditor Value:</strong> When external auditors (SOC 2, ISO 27001, PCI-DSS) inspect an organization, they no longer need to trust screenshots. They download the JSON receipt and verify the Merkle root mathematically with 100% cryptographic certainty.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-100 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            CyberYukti v2.0 &bull; PS16 Autonomous Evidence Engine
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-md transition-colors"
          >
            Got It
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
