"use client";

import React from "react";

interface RichMarkdownTextProps {
  content: string;
  className?: string;
}

/**
 * Robust markdown formatter that parses **bold**, *italic*, `code`,
 * bullet points, and numbered lists into semantic React elements.
 * Cleans any stray double asterisks so raw `**` never leaks into UI.
 */
export function RichMarkdownText({ content, className = "" }: RichMarkdownTextProps) {
  if (!content) return null;

  // Split into lines for list and paragraph processing
  const lines = content.split("\n");

  const formatInlineText = (text: string): React.ReactNode[] => {
    // Regex tokens for:
    // 1. **bold**
    // 2. `code`
    // 3. *italic* or _italic_
    const parts: React.ReactNode[] = [];
    const tokenRegex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|_[^_]+_)/g;

    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = tokenRegex.exec(text)) !== null) {
      // Text before match
      if (match.index > lastIndex) {
        const preceding = text.substring(lastIndex, match.index);
        // Clean any stray asterisks
        parts.push(preceding.replace(/\*\*/g, ""));
      }

      const raw = match[0];
      const matchIndex = match.index;

      if (raw.startsWith("**") && raw.endsWith("**")) {
        const inner = raw.slice(2, -2);
        parts.push(
          <strong
            key={`bold-${matchIndex}`}
            className="font-semibold text-tx-primary dark:text-white"
          >
            {inner}
          </strong>
        );
      } else if (raw.startsWith("`") && raw.endsWith("`")) {
        const inner = raw.slice(1, -1);
        parts.push(
          <code
            key={`code-${matchIndex}`}
            className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-accent/10 text-accent border border-accent/25 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-500/30"
          >
            {inner}
          </code>
        );
      } else if ((raw.startsWith("*") && raw.endsWith("*")) || (raw.startsWith("_") && raw.endsWith("_"))) {
        const inner = raw.slice(1, -1);
        parts.push(
          <em key={`italic-${matchIndex}`} className="italic text-tx-secondary">
            {inner}
          </em>
        );
      } else {
        parts.push(raw);
      }

      lastIndex = tokenRegex.lastIndex;
    }

    // Trailing text
    if (lastIndex < text.length) {
      const remaining = text.substring(lastIndex);
      // Clean any stray asterisks
      parts.push(remaining.replace(/\*\*/g, ""));
    }

    return parts;
  };

  return (
    <div className={`space-y-1.5 leading-relaxed ${className}`}>
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        // Empty line -> spacing
        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }

        // Bullet point: "- ..." or "* ..."
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const bulletText = trimmed.slice(2);
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 text-[12px] sm:text-[13px]">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent dark:bg-emerald-400" />
              <span className="flex-1 text-tx-secondary dark:text-slate-200">
                {formatInlineText(bulletText)}
              </span>
            </div>
          );
        }

        // Numbered list: "1. ..."
        const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numberedMatch) {
          const num = numberedMatch[1];
          const numText = numberedMatch[2];
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 text-[12px] sm:text-[13px]">
              <span className="font-mono text-[11px] font-bold text-accent dark:text-emerald-400 shrink-0 mt-0.5">
                {num}.
              </span>
              <span className="flex-1 text-tx-secondary dark:text-slate-200">
                {formatInlineText(numText)}
              </span>
            </div>
          );
        }

        // Section header inside chat (e.g. starts and ends with **)
        if (trimmed.startsWith("**") && trimmed.endsWith("**") && trimmed.length > 4) {
          const headerTitle = trimmed.slice(2, -2);
          return (
            <div
              key={idx}
              className="font-bold text-[12.5px] sm:text-[13.5px] text-tx-primary dark:text-white pt-1"
            >
              {headerTitle}
            </div>
          );
        }

        // Standard paragraph line
        return (
          <p key={idx} className="text-[12px] sm:text-[13px] text-tx-secondary dark:text-slate-200">
            {formatInlineText(line)}
          </p>
        );
      })}
    </div>
  );
}
