import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0A0C10",
        graphite: {
          deep: "#08090C",
          DEFAULT: "#0F1216",
          raised: "#12161C",
          panel: "#11151A",
        },
        line: {
          faint: "#1A1E25",
          DEFAULT: "#1F242C",
          strong: "#2A303A",
        },
        tx: {
          primary: "#E6E9ED",
          secondary: "#98A0AA",
          tertiary: "#5D6673",
        },
        accent: {
          DEFAULT: "#2DD4BF",
          dim: "#14B8A6",
          soft: "rgba(45, 212, 191, 0.09)",
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
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;