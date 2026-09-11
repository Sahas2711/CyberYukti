"use client";

import { useEffect, useState } from "react";
import { getProvider } from "@/lib/providers";
import type { DashboardStats, TriageCase } from "@/lib/api/types";
import { KpiStrip } from "@/components/dashboard/KpiStrip";
import { PipelineStrip } from "@/components/dashboard/PipelineStrip";
import { PriorityQueue } from "@/components/dashboard/PriorityQueue";
import { CaseTable } from "@/components/dashboard/CaseTable";
import { Skeleton } from "@/components/shared/Skeleton";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-6 w-[560px] max-w-full" />
      </div>
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-line bg-line-strong sm:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="bg-graphite px-4 py-3.5">
            <Skeleton className="h-6 w-10" />
            <Skeleton className="mt-2 h-3 w-20" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
      <Skeleton className="h-72" />
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [cases, setCases] = useState<TriageCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const provider = getProvider();
      const [statsResult, casesResult] = await Promise.all([
        provider.getDashboardStats(),
        provider.listCases(),
      ]);
      setStats(statsResult);
      setCases(casesResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <DashboardSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="rounded-sm border border-line bg-graphite py-16 text-center">
          <h2 className="hk-label">Data source unavailable</h2>
          <p className="mt-2 text-sm text-tx-secondary">{error}</p>
          <button
            type="button"
            onClick={() => void fetchData()}
            className="mt-5 rounded-sm border border-accent/50 bg-accent-soft px-4 py-2 text-xs font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/15"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="py-16 text-center">
          <p className="hk-label">No data available</p>
        </div>
      </div>
    );
  }

  const pending = cases.filter((c) => c.approval.status === "PENDING").length;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-5 py-6 lg:px-8">
      <section className="space-y-2">
        <h2 className="hk-label">CyberYukti / Triage Overview</h2>
        <p className="text-xl font-semibold tracking-tight text-tx-primary sm:text-2xl">
          {stats.total_findings} findings reduced to {stats.unique_clusters}{" "}
          actionable vulnerability case{stats.unique_clusters === 1 ? "" : "s"}.
        </p>
      </section>

      <KpiStrip stats={stats} pending={pending} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PriorityQueue stats={stats} cases={cases} />
        <PipelineStrip stats={stats} pending={pending} />
      </div>

      <section>
        <div className="mb-3">
          <h2 className="hk-label">Triage Queue</h2>
        </div>
        <CaseTable cases={cases} />
      </section>
    </div>
  );
}