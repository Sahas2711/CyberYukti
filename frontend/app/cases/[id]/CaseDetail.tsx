"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getProvider } from "@/lib/providers";
import type { TriageCase } from "@/lib/api/types";
import { Skeleton } from "@/components/shared/Skeleton";
import { CaseHeader } from "@/components/case/CaseHeader";
import { CasePipeline } from "@/components/case/CasePipeline";
import { EvidencePanel } from "@/components/case/EvidencePanel";
import { ThreatIntelPanel } from "@/components/case/ThreatIntelPanel";
import { DuplicateClusterPanel } from "@/components/case/DuplicateClusterPanel";
import { PriorityBreakdown } from "@/components/case/PriorityBreakdown";
import { AIAnalysisPanel } from "@/components/case/AIAnalysisPanel";
import { RemediationPanel } from "@/components/case/RemediationPanel";
import { ApprovalControls } from "@/components/case/ApprovalControls";
import { AuditTimeline } from "@/components/case/AuditTimeline";

function CaseDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40" />
      <Skeleton className="h-16" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Skeleton className="h-72" />
          <Skeleton className="h-56" />
          <Skeleton className="h-80" />
        </div>
        <div className="space-y-6">
          <Skeleton className="h-40" />
          <Skeleton className="h-64" />
        </div>
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

export function CaseDetail() {
  const params = useParams<{ id: string }>();
  const id = typeof params?.id === "string" ? params.id : "";

  const [caseData, setCaseData] = useState<TriageCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCase = useCallback(async () => {
    if (!id) {
      setLoading(false);
      setNotFound(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await getProvider().getCase(id);
      setCaseData(result);
      setNotFound(false);
    } catch (err) {
      if (err instanceof Error && /not found/i.test(err.message)) {
        setNotFound(true);
      } else {
        setError(err instanceof Error ? err.message : "Failed to load case");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void fetchCase();
  }, [fetchCase]);

  async function handleAnalyze() {
    if (!id) return;
    setAnalyzing(true);
    setError(null);
    try {
      await getProvider().analyzeCase(id);
      await fetchCase();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis");
    } finally {
      setAnalyzing(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-8 lg:px-8">
        <CaseDetailSkeleton />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="rounded-sm border border-line bg-graphite py-16 text-center">
          <h2 className="hk-label">Case not found</h2>
          <p className="mt-2 text-sm text-tx-secondary">
            The case you are looking for does not exist or is no longer available.
          </p>
          <Link
            href="/cases"
            className="mt-5 inline-block rounded-sm border border-accent/50 bg-accent-soft px-4 py-2 text-xs font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/15"
          >
            Back to cases
          </Link>
        </div>
      </div>
    );
  }

  if (error && !caseData) {
    return (
      <div className="mx-auto max-w-[1400px] px-5 py-6 lg:px-8">
        <div className="rounded-sm border border-line bg-graphite py-16 text-center">
          <h2 className="hk-label">Data source unavailable</h2>
          <p className="mt-2 text-sm text-tx-secondary">{error}</p>
          <button
            type="button"
            onClick={() => void fetchCase()}
            className="mt-5 rounded-sm border border-accent/50 bg-accent-soft px-4 py-2 text-xs font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/15"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!caseData) return null;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-5 py-8 lg:px-8">
      <CaseHeader case={caseData} />
      <CasePipeline case={caseData} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <EvidencePanel evidence={caseData.evidence} />
          <PriorityBreakdown priority={caseData.priority} />
          <AIAnalysisPanel
            analysis={caseData.ai_analysis}
            onAnalyze={() => void handleAnalyze()}
            loading={analyzing}
          />
          <RemediationPanel analysis={caseData.ai_analysis} />
        </div>

        <div className="space-y-6 lg:self-start lg:sticky lg:top-20">
          <ThreatIntelPanel threatIntel={caseData.threat_intelligence} />
          {caseData.finding_count > 1 && (
            <DuplicateClusterPanel
              sources={caseData.sources}
              findingCount={caseData.finding_count}
              clusterId={caseData.cluster_id}
            />
          )}
          <ApprovalControls
            caseId={caseData.case_id}
            approval={caseData.approval}
            audit={caseData.audit}
            onAction={() => void fetchCase()}
          />
        </div>
      </div>

      <AuditTimeline events={caseData.audit} />
    </div>
  );
}