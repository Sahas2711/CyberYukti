"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { fetchCaseAttestation, verifyAttestationReceipt } from "@/lib/api/uspServices";
import type { AttestationReceipt, AttestationVerificationResult } from "@/lib/api/types";

interface AttestationModalProps {
  caseId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function AttestationModal({ caseId, isOpen, onClose }: AttestationModalProps) {
  const [mounted, setMounted] = useState<boolean>(false);
  const [receipt, setReceipt] = useState<AttestationReceipt | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [verification, setVerification] = useState<AttestationVerificationResult | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [activeLeaf, setActiveLeaf] = useState<number | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      setReceipt(null);
      setVerification(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchCaseAttestation(caseId)
      .then((data) => {
        if (isMounted) {
          setReceipt(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load cryptographic attestation receipt");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [caseId, isOpen]);

  if (!isOpen || !mounted) return null;

  const copyMerkleRoot = () => {
    if (receipt?.merkle_root) {
      navigator.clipboard.writeText(receipt.merkle_root);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleVerify = async () => {
    if (!receipt) return;
    setVerifying(true);
    try {
      const res = await verifyAttestationReceipt(receipt as unknown as Record<string, unknown>);
      setVerification(res);
    } catch (err: unknown) {
      setVerification({
        valid: false,
        status: "VERIFICATION_FAILED",
        reason: err instanceof Error ? err.message : "Verification request failed",
      });
    } finally {
      setVerifying(false);
    }
  };

  const downloadJson = () => {
    if (!receipt) return;
    const blob = new Blob([JSON.stringify(receipt, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `CyberYukti_Attestation_${caseId}_${receipt.merkle_root.slice(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto print:p-0 print:bg-white animate-in fade-in">
      <div className="relative w-full max-w-4xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-emerald-500/40 rounded-2xl shadow-2xl overflow-hidden print:border-none print:shadow-none print:bg-white print:text-black">
        {/* Certificate Header Banner */}
        <div className="bg-slate-100 dark:bg-gradient-to-r dark:from-emerald-950 dark:via-slate-900 dark:to-cyan-950 border-b border-slate-200 dark:border-emerald-500/30 px-6 py-5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-400/40 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold text-xl shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              🛡️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono tracking-widest uppercase text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-300 dark:border-emerald-500/40 font-bold">
                  Proof-of-Fix Attestation
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">ISO 27001 / SOC 2 Ready</span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white tracking-tight mt-0.5 print:text-black">
                Cryptographic Evidence Receipt &mdash; {caseId}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 print:hidden"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Certificate Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto print:max-h-none print:overflow-visible bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-xs sm:text-sm">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <div className="w-10 h-10 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-slate-600 dark:text-slate-300 font-mono">Generating SHA-256 Merkle Evidence Receipt...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-500/50 rounded-xl text-red-700 dark:text-red-200 text-sm">
              <p className="font-semibold">Error Loading Attestation</p>
              <p className="text-xs text-red-600 dark:text-red-300 mt-1">{error}</p>
            </div>
          )}

          {receipt && (
            <>
              {/* Certificate Metadata Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl p-4 text-xs font-mono">
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Certificate ID:</span>
                  <span className="text-emerald-700 dark:text-emerald-400 font-semibold truncate block" title={receipt.certificate_id}>
                    {receipt.certificate_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Issuer Authority:</span>
                  <span className="text-slate-800 dark:text-slate-200 truncate block font-semibold">{receipt.issuer}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Issued Timestamp:</span>
                  <span className="text-slate-800 dark:text-slate-200 block">{new Date(receipt.issued_at).toUTCString()}</span>
                </div>
              </div>

              {/* SHA-256 Merkle Root Badge */}
              <div className="bg-slate-50 dark:bg-gradient-to-r dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 border border-emerald-300 dark:border-emerald-500/50 rounded-xl p-4 relative shadow-inner">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                      SHA-256 Merkle Root Digest (Immutable Fingerprint)
                    </span>
                  </div>
                  <button
                    onClick={copyMerkleRoot}
                    className="text-xs px-2.5 py-1 bg-emerald-100 dark:bg-emerald-500/20 hover:bg-emerald-200 dark:hover:bg-emerald-500/30 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded-md transition-colors print:hidden font-medium"
                  >
                    {copied ? "✓ Copied Hash" : "Copy Merkle Root"}
                  </button>
                </div>
                <div className="font-mono text-xs sm:text-sm text-emerald-800 dark:text-emerald-400 break-all bg-white dark:bg-black/40 p-3 rounded-lg border border-slate-200 dark:border-emerald-500/20 select-all font-semibold">
                  {receipt.merkle_root}
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                  Mathematically links Scanner Evidence &rarr; Probe Execution &rarr; Risk Score &rarr; Analyst Signature.
                  External auditors can independently verify that zero post-triage tampering occurred.
                </p>
              </div>

              {/* 4-Node Cryptographic Ledger Tree */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-300 mb-3 flex items-center justify-between">
                  <span>Cryptographic Ledger State Transitions (4 Merkle Leaves)</span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-normal">Click any node to view canonical payload</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {receipt.state_transitions.map((st) => {
                    const isSelected = activeLeaf === st.step;
                    return (
                      <div
                        key={st.step}
                        onClick={() => setActiveLeaf(isSelected ? null : st.step)}
                        className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                          isSelected
                            ? "bg-emerald-50 dark:bg-slate-800 border-emerald-500 dark:border-emerald-400 shadow-md ring-1 ring-emerald-500/40"
                            : "bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700/60 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800/70"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center space-x-1.5">
                            <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 border border-emerald-300 dark:border-emerald-500/40 flex items-center justify-center text-[10px] font-bold text-emerald-700 dark:text-emerald-400">
                              {st.step}
                            </span>
                            <span>{st.name}</span>
                          </span>
                          <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                            Leaf {st.step}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mb-2">{st.summary}</p>
                        <div className="font-mono text-[10px] text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-950 p-1.5 rounded border border-slate-200 dark:border-slate-800 truncate" title={st.hash}>
                          hash: {st.hash}
                        </div>

                        {isSelected && (
                          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700/60 text-left">
                            <span className="text-[10px] uppercase font-mono text-slate-500 dark:text-slate-400 block mb-1">
                              Canonical JSON Data:
                            </span>
                            <pre className="text-[11px] font-mono text-emerald-700 dark:text-emerald-300/90 bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800 overflow-x-auto max-h-36">
                              {JSON.stringify(st.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Independent Verification Banner */}
              {verification && (
                <div
                  className={`p-4 rounded-xl border text-xs ${
                    verification.valid
                      ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-500/60 text-emerald-800 dark:text-emerald-200"
                      : "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-500/60 text-red-800 dark:text-red-200"
                  }`}
                >
                  <div className="flex items-center space-x-2 font-bold text-sm">
                    <span>{verification.valid ? "🛡️ CRYPTOGRAPHIC INTEGRITY VERIFIED" : "⚠️ TAMPER DETECTED"}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/60 dark:bg-black/40 border border-emerald-500/40">
                      Status: {verification.status}
                    </span>
                  </div>
                  <p className="mt-1 text-slate-700 dark:text-slate-300 leading-relaxed">
                    {verification.valid
                      ? "Merkle root recalculated across all 4 leaves matches certificate authority signature exactly. Zero tampering detected."
                      : `Verification failed: ${verification.reason || "Hash mismatch"}`}
                  </p>
                  <div className="mt-2 font-mono text-[10px] text-slate-500 dark:text-slate-400">
                    Verified at: {verification.verified_at || new Date().toISOString()}
                  </div>
                </div>
              )}

              {/* Compliance & Audit Notes */}
              <div className="bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 text-xs text-slate-600 dark:text-slate-400 space-y-1.5">
                <div className="text-slate-800 dark:text-slate-300 font-semibold mb-1">Audit Compliance Statements:</div>
                {receipt.compliance_notes.map((note, i) => (
                  <div key={i} className="flex items-start space-x-2">
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">✓</span>
                    <span>{note}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="bg-slate-100 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 px-6 py-4 flex flex-wrap items-center justify-between gap-3 print:hidden">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleVerify}
              disabled={verifying || !receipt}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-md transition-all flex items-center space-x-2"
            >
              <span>{verifying ? "Verifying..." : "⚡ Verify Tamper Integrity"}</span>
            </button>
            <button
              onClick={downloadJson}
              disabled={!receipt}
              className="px-3.5 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs rounded-xl border border-slate-200 dark:border-slate-700 transition-colors font-medium shadow-xs"
            >
              📥 Export Receipt (JSON)
            </button>
            <button
              onClick={handlePrint}
              disabled={!receipt}
              className="px-3.5 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs rounded-xl border border-slate-200 dark:border-slate-700 transition-colors font-medium shadow-xs"
            >
              🖨️ Printable Certificate
            </button>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-300 text-xs rounded-xl transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
