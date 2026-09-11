"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { fetchTop10Remediations } from "@/lib/api/uspServices";
import type { RemediationPlaybook } from "@/lib/api/types";

interface RemediationPlaybookModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RemediationPlaybookModal({ isOpen, onClose }: RemediationPlaybookModalProps) {
  const [mounted, setMounted] = useState(false);
  const [playbooks, setPlaybooks] = useState<RemediationPlaybook[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchTop10Remediations()
      .then((data) => {
        if (isMounted) {
          setPlaybooks(data);
          if (data.length > 0) {
            setSelectedCaseId((prev) => prev || data[0].case_id);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load remediation playbooks");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen || !mounted) return null;

  const activePlaybook = playbooks.find((p) => p.case_id === selectedCaseId) || playbooks[0];

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-slate-900 border border-emerald-500/40 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-950 via-slate-900 to-slate-950 border-b border-emerald-500/30 px-6 py-5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-xl text-red-400">
              🛠️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono uppercase tracking-widest text-red-400 bg-red-950 px-2 py-0.5 rounded-full border border-red-500/40">
                  Engineer Fix Playbooks
                </span>
                <span className="text-xs text-slate-400">Top Priority Vulnerabilities</span>
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight mt-0.5">
                Top P1 Remediation & Virtual Patch Knowledge Base
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Content Body (Split View) */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          {/* Left Sidebar: Vulnerability List */}
          <div className="w-full md:w-80 border-r border-slate-800 bg-slate-950/60 overflow-y-auto p-3 space-y-2">
            <div className="text-[11px] font-mono uppercase text-slate-400 px-2 py-1 flex items-center justify-between">
              <span>Actionable Queue</span>
              <span>{playbooks.length} Playbooks</span>
            </div>

            {loading && (
              <div className="p-4 text-center text-slate-400 text-xs font-mono">
                Loading P1 playbooks...
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-xl text-red-300 text-xs">
                {error}
              </div>
            )}

            {playbooks.map((p) => {
              const isSelected = p.case_id === activePlaybook?.case_id;
              return (
                <div
                  key={p.case_id}
                  onClick={() => setSelectedCaseId(p.case_id)}
                  className={`cursor-pointer p-3 rounded-xl border transition-all text-left ${
                    isSelected
                      ? "bg-slate-800 border-emerald-400 ring-1 ring-emerald-400/40"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        p.priority === "P1"
                          ? "bg-red-950 text-red-400 border border-red-500/40"
                          : "bg-amber-950 text-amber-400 border border-amber-500/40"
                      }`}
                    >
                      {p.priority}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                      +{p.formatted_savings} Saved
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-white truncate" title={p.title}>
                    {p.title}
                  </h4>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                    <span className="font-mono text-slate-500">{p.case_id}</span>
                    <span className="text-slate-400">{p.daily_burn}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Pane: Selected Playbook Detail */}
          <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-slate-900/90 text-slate-300 text-xs">
            {activePlaybook ? (
              <>
                {/* Title & Metadata Strip */}
                <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 bg-red-950 text-red-400 border border-red-500/40 rounded-full font-bold font-mono text-xs">
                        {activePlaybook.priority} Critical
                      </span>
                      <span className="text-xs font-mono text-slate-400">{activePlaybook.case_id}</span>
                    </div>
                    <div className="flex items-center space-x-3 text-xs">
                      <span className="text-red-400 font-semibold">
                        Liability: {activePlaybook.daily_burn}
                      </span>
                      <span className="text-emerald-400 font-semibold">
                        Potential Savings: {activePlaybook.formatted_savings}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-base font-bold text-white">{activePlaybook.title}</h3>
                  <div className="flex flex-wrap gap-4 mt-2 text-[11px] text-slate-400 font-mono">
                    <span>CVE: <strong className="text-slate-200">{activePlaybook.cve}</strong></span>
                    <span>CWE: <strong className="text-slate-200">{activePlaybook.cwe}</strong></span>
                    <span>Target: <strong className="text-slate-200">{activePlaybook.target_asset}</strong></span>
                    <span>Est. Fix Time: <strong className="text-emerald-300">{activePlaybook.estimated_hours} hrs</strong></span>
                  </div>
                </div>

                {/* Root Cause Diagnosis */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center space-x-2">
                    <span>🔍</span>
                    <span>Root Cause Diagnosis</span>
                  </h4>
                  <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl leading-relaxed text-slate-300">
                    {activePlaybook.root_cause}
                  </div>
                </div>

                {/* Immediate Virtual Patch (WAF Rule) */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center space-x-2">
                      <span>🛡️</span>
                      <span>Immediate Virtual Patch (Zero-Downtime WAF Rule)</span>
                    </h4>
                    <button
                      onClick={() => handleCopy(activePlaybook.virtual_patch_waf, "waf")}
                      className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded-md transition-colors text-[11px]"
                    >
                      {copiedKey === "waf" ? "✓ Copied" : "Copy WAF Rule"}
                    </button>
                  </div>
                  <pre className="p-3.5 bg-black/60 border border-amber-500/30 rounded-xl text-amber-300 font-mono text-xs overflow-x-auto whitespace-pre-wrap">
                    {activePlaybook.virtual_patch_waf}
                  </pre>
                </div>

                {/* Permanent Code Patch */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-2">
                      <span>💻</span>
                      <span>Permanent Code Diff & Dependency Upgrade</span>
                    </h4>
                    <button
                      onClick={() => handleCopy(activePlaybook.permanent_code_patch, "code")}
                      className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 rounded-md transition-colors text-[11px]"
                    >
                      {copiedKey === "code" ? "✓ Copied" : "Copy Code Diff"}
                    </button>
                  </div>
                  <pre className="p-3.5 bg-black/60 border border-emerald-500/30 rounded-xl text-emerald-300 font-mono text-xs overflow-x-auto whitespace-pre-wrap">
                    {activePlaybook.permanent_code_patch}
                  </pre>
                </div>

                {/* Post-Fix Verification Probe */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center space-x-2">
                      <span>🧪</span>
                      <span>Post-Fix Non-Destructive Verification Probe</span>
                    </h4>
                    <button
                      onClick={() => handleCopy(activePlaybook.verification_probe, "probe")}
                      className="px-2.5 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 rounded-md transition-colors text-[11px]"
                    >
                      {copiedKey === "probe" ? "✓ Copied" : "Copy Probe Command"}
                    </button>
                  </div>
                  <pre className="p-3 bg-black/60 border border-cyan-500/30 rounded-xl text-cyan-300 font-mono text-xs overflow-x-auto">
                    {activePlaybook.verification_probe}
                  </pre>
                  <p className="mt-1.5 text-[11px] text-slate-400">
                    Expected Verification Output: <strong className="text-slate-200">{activePlaybook.expected_verification}</strong>
                  </p>
                </div>
              </>
            ) : (
              <div className="text-center py-20 text-slate-500">
                Select a playbook from the left list to view engineer-ready fix instructions.
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-950 border-t border-slate-800 px-6 py-4 flex items-center justify-between">
          <span className="text-xs text-slate-400 font-mono">
            Directly actionable by DevSecOps / SRE teams for rapid MTTR reduction.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
