"use client";

import React, { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import { sendAiChatMessage, type ChatMessagePayload } from "@/lib/api/uspServices";

interface ChatBotWidgetProps {
  currentCaseId?: string;
}

export function ChatBotWidget({ currentCaseId }: ChatBotWidgetProps) {
  const pathname = usePathname();
  const pathCaseId = pathname?.startsWith("/cases/") ? pathname.split("/cases/")[1]?.split("/")[0] : undefined;
  const activeCaseId = currentCaseId || pathCaseId;

  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessagePayload[]>([
    {
      role: "assistant",
      content:
        "👋 **Welcome to the CyberYukti Autonomous SOC Copilot.**\n\n" +
        "I am connected to your live triage telemetry, 3-tier dedup engine, and cryptographic proof-of-fix ledger.\n\n" +
        "How can I assist your investigation today?",
    },
  ]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: ChatMessagePayload = { role: "user", content: query };
    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setInput("");
    setLoading(true);

    try {
      const response = await sendAiChatMessage(query, activeCaseId, updatedHistory);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.reply,
        },
      ]);
    } catch (err: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Failed to reach SOC Copilot: ${err instanceof Error ? err.message : "Network error"}. Check backend server connection.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const starterChips = [
    { label: "⚡ Explain P1 Score Factors", query: `Why is this vulnerability classified with its current priority score and SLA?` },
    { label: "🛡️ Generate Fix Playbook", query: `Provide concrete virtual patch WAF rules and permanent code diffs for this case.` },
    { label: "🔒 Explain Merkle Attestation", query: `How does CyberYukti's SHA-256 Merkle root prove zero post-triage tampering?` },
    { label: "💰 Calculate Cost Burn", query: `What is the financial liability burn rate per day for unresolved P1 findings?` },
  ];

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center space-x-2.5 px-4 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm rounded-full shadow-2xl shadow-emerald-500/30 border border-emerald-400/40 transition-all transform hover:scale-105 active:scale-95"
          aria-label="Open CyberYukti SOC Copilot"
        >
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-400"></span>
          </span>
          <span className="text-base">🤖</span>
          <span>AI SOC Copilot</span>
          {activeCaseId && (
            <span className="text-[10px] font-mono bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-400/30">
              {activeCaseId}
            </span>
          )}
        </button>
      )}

      {/* Slide-Up Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-96 sm:w-[440px] h-[580px] max-h-[90vh] bg-slate-900 border border-emerald-500/40 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl animate-in fade-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="bg-gradient-to-r from-emerald-950 via-slate-900 to-slate-950 border-b border-emerald-500/30 p-4 flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
                🤖
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-white tracking-tight">CyberYukti SOC Copilot</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-500/40 rounded-full">
                    Grounded AI
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {activeCaseId ? `Context: ${activeCaseId}` : "Autonomous Triage & Attestation Assistant"}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
              aria-label="Minimize Copilot"
            >
              ✕
            </button>
          </div>

          {/* Quick Starter Chips */}
          <div className="bg-slate-950/70 border-b border-slate-800 px-3 py-2 flex items-center space-x-1.5 overflow-x-auto text-[11px] scrollbar-none">
            {starterChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip.query)}
                className="whitespace-nowrap px-2.5 py-1 bg-slate-800/80 hover:bg-emerald-900/40 hover:text-emerald-300 hover:border-emerald-500/50 text-slate-300 border border-slate-700/60 rounded-full transition-all"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 shadow-sm leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-emerald-600 text-white rounded-br-none"
                      : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none font-sans"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center space-x-2 text-slate-400 bg-slate-800/50 border border-slate-700/40 px-3 py-2 rounded-xl w-fit">
                <span className="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-[11px] font-mono">Analyzing telemetry & formulating response...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-slate-950 border-t border-slate-800">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about vulnerabilities, WAF fixes, or Merkle roots..."
                disabled={loading}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400 transition-colors"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-md transition-all flex items-center justify-center"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
