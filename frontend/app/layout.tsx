import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import { Sidebar } from "@/components/shared/Sidebar";
import { TopHeader } from "@/components/shared/TopHeader";
import { ThemeProvider } from "@/lib/ThemeContext";

export const metadata: Metadata = {
  title: "CyberYukti — Autonomous Vulnerability Triage & Evidence Engine",
  description: "Enterprise SOC Platform: Ingest multi-scanner findings, deduplicate alerts, and verify exploitability with automated evidence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="cyber-grid-bg transition-colors duration-200">
        <ThemeProvider>
          <div className="flex min-h-screen">
            <Suspense fallback={null}>
              <Sidebar />
            </Suspense>
            <div className="flex min-h-screen flex-1 flex-col lg:ml-[240px]">
              <Suspense fallback={null}>
                <TopHeader />
              </Suspense>
              <main className="flex-1">{children}</main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}