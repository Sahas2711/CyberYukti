"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getProvider } from "@/lib/providers";
import type { TriageCase } from "@/lib/api/types";
import { CaseTable } from "@/components/dashboard/CaseTable";
import { Skeleton } from "@/components/shared/Skeleton";

function CasesListSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-3 w-32" />
      <Skeleton className="h-6 w-64" />
      <Skeleton className="h-16" />
      <Skeleton className="h-72" />
    </div>
  );
}

function CasesPageInner() {
  const searchParams = useSearchParams();
  const [cases, setCases] = useState<TriageCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initialPriority = searchParams.get("priority") ?? "ALL";
  const initialEvidence = searchParams.get("evidence") ?? "ALL";
  const initialApproval = searchParams.get("approval") ?? "ALL";
  const initialQuery = searchParams.get("q") ?? "";

  async function fetchCases() {
    setLoading(true);
    setError(null);
    try {
      const result = await getProvider().listCases();
      setCases(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cases");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchCases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-8 lg:px-8">
        <CasesListSkeleton />
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
            onClick={() => void fetchCases()}
            className="mt-5 rounded-sm border border-accent/50 bg-accent-soft px-4 py-2 text-xs font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/15"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-5 py-8 lg:px-8">
      <section>
        <h2 className="hk-label">Triage</h2>
        <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-tx-primary">
          Vulnerability Work Queue
        </h1>
        <p className="mt-1 text-sm text-tx-secondary">
          Verified, prioritized cases awaiting analyst decision. Click any row to open the
          investigation workspace.
        </p>
      </section>

      <CaseTable
        cases={cases}
        initialQuery={initialQuery}
        initialPriority={initialPriority}
        initialEvidence={initialEvidence}
        initialApproval={initialApproval}
      />
    </div>
  );
}

export default function CasesPage() {
  return (
    <Suspense fallback={null}>
      <CasesPageInner />
    </Suspense>
  );
}