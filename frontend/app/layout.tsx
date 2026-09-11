import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import { Sidebar } from "@/components/shared/Sidebar";
import { TopHeader } from "@/components/shared/TopHeader";

export const metadata: Metadata = {
  title: "CyberYukti - Vulnerability Triage",
  description: "Turn noisy vulnerability findings into verified, prioritized, auditable cases.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Suspense fallback={null}>
            <Sidebar />
          </Suspense>
          <div className="flex min-h-screen flex-1 flex-col lg:ml-[232px]">
            <Suspense fallback={null}>
              <TopHeader />
            </Suspense>
            <main className="flex-1">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}