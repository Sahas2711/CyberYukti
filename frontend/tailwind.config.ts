import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--color-canvas)",
        graphite: {
          deep: "var(--color-graphite-deep)",
          DEFAULT: "var(--color-graphite)",
          raised: "var(--color-graphite-raised)",
          panel: "var(--color-graphite-panel)",
        },
        line: {
          faint: "var(--color-line-faint)",
          DEFAULT: "var(--color-line)",
          strong: "var(--color-line-strong)",
        },
        tx: {
          primary: "var(--color-tx-primary)",
          secondary: "var(--color-tx-secondary)",
          tertiary: "var(--color-tx-tertiary)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          dim: "var(--color-accent-dim)",
          soft: "var(--color-accent-soft)",
          glow: "var(--color-accent-glow)",
        },
        cyber: {
          cyan: "#06b6d4",
          teal: "#14b8a6",
          emerald: "#10b981",
          crimson: "#f43f5e",
          amber: "#f59e0b",
          blue: "#3b82f6",
          purple: "#a855f7",
          darkbg: "#06080d",
          cardbg: "#0c1017",
        },
        priority: {
          p1: "#ef4444",
          p2: "#f97316",
          p3: "#eab308",
          p4: "#22c55e",
        },
        evidence: {
          confirmed: "#22c55e",
          "not-confirmed": "#ef4444",
          inconclusive: "#6b7280",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
      animation: {
        "radar-sweep": "radarSweep 4s linear infinite",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "ticker-scroll": "ticker 25s linear infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        radarSweep: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "1", filter: "drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))" },
          "50%": { opacity: "0.6", filter: "drop-shadow(0 0 2px rgba(6, 182, 212, 0.2))" },
        },
        ticker: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;