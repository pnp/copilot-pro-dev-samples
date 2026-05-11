import { useState, useEffect, useMemo, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, AlertTriangle } from "lucide-react";
import { useAppStore } from "@/store/app-store";
import { useReviewData } from "@/hooks/use-review-data";
import { SummaryBar } from "@/components/review/summary-bar";
import { StatementTabs } from "@/components/review/statement-tabs";
import { LineItemTable } from "@/components/review/line-item-table";
import { ApproveButton } from "@/components/review/approve-button";
import type { FxConversionState } from "@/types/extraction";

export default function ReviewPage() {
  const [searchParams] = useSearchParams();

  const jobId = useAppStore((s) => s.jobId);
  const setJobId = useAppStore((s) => s.setJobId);
  const lineItems = useAppStore((s) => s.lineItems);
  const setLineItems = useAppStore((s) => s.setLineItems);
  const activeTab = useAppStore((s) => s.activeTab);
  const setActiveTab = useAppStore((s) => s.setActiveTab);

  const [fx, setFx] = useState<FxConversionState>({
    targetCurrency: null,
    spotRate: null,
    avgRate: null,
    rateDate: "",
    rateSource: "",
    isLoading: false,
  });

  const [displayUnit, setDisplayUnit] = useState<string>("ones");

  // Read jobId from multiple sources
  useEffect(() => {
    async function resolveJobId() {
      let resolved: string | null = null;
      try {
        const { getContext } = await import("@microsoft/power-apps/app");
        const ctx = await getContext();
        resolved = ctx.app?.queryParams?.jobId || null;
      } catch {
        // Not running in Power Apps
      }
      if (!resolved) {
        resolved = searchParams.get("jobId");
      }
      if (resolved && resolved !== jobId) {
        setJobId(resolved);
      }
    }
    resolveJobId();
  }, [searchParams, jobId, setJobId]);

  const { job, statements, lineItems: fetchedLineItems, isLoading, error } = useReviewData(jobId);

  // Sync fetched line items into Zustand store
  useEffect(() => {
    if (fetchedLineItems.length > 0 && lineItems.length === 0) {
      setLineItems(fetchedLineItems);
    }
  }, [fetchedLineItems, lineItems.length, setLineItems]);

  const activeLineItems = lineItems.length > 0 ? lineItems : fetchedLineItems;

  // displayUnit defaults to "ones" — user always sees original extracted values first.
  // sourceUnit (from job.currencyUnit) tells us what Dataverse actually stores,
  // so the scale factor converts correctly regardless of display choice.

  // Map statement recordIds to types
  const statementRecordIds = useMemo(() => {
    const map: Record<string, string> = {};
    statements.forEach((s) => {
      map[s.recordId] = s.statementType;
    });
    return map;
  }, [statements]);

  // Filter line items for active tab
  const filteredItems = useMemo(() => {
    return activeLineItems.filter((item) => {
      const stmtType = statementRecordIds[item.statementRecordId];
      return stmtType === activeTab;
    });
  }, [activeLineItems, activeTab, statementRecordIds]);

  // Item counts per tab
  const itemCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    activeLineItems.forEach((item) => {
      const stmtType = statementRecordIds[item.statementRecordId];
      if (stmtType) counts[stmtType] = (counts[stmtType] || 0) + 1;
    });
    return counts;
  }, [activeLineItems, statementRecordIds]);

  // Flag counts per tab
  const flagCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    activeLineItems.forEach((item) => {
      const stmtType = statementRecordIds[item.statementRecordId];
      if (stmtType && (item.reviewStatus === "Flagged" || (item.aiConfidence !== null && item.aiConfidence < 0.7))) {
        counts[stmtType] = (counts[stmtType] || 0) + 1;
      }
    });
    return counts;
  }, [activeLineItems, statementRecordIds]);

  // Correction count: items with reviewStatus "Corrected"
  const correctionCount = useMemo(() => {
    return activeLineItems.filter((i) => i.reviewStatus === "Corrected").length;
  }, [activeLineItems]);

  // Set initial active tab
  useEffect(() => {
    if (statements.length > 0 && !statements.find((s) => s.statementType === activeTab)) {
      setActiveTab(statements[0].statementType);
    }
  }, [statements, activeTab, setActiveTab]);

  // Jump to first flagged row
  const handleJumpToFlags = useCallback(() => {
    const el = document.querySelector("[data-flagged]");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, []);

  // Jump to next unresolved flagged row (one that hasn't been corrected yet)
  const handleJumpToNextUnresolved = useCallback(() => {
    const rows = document.querySelectorAll("[data-flagged]");
    // Find the first flagged row that is still visible in the amber style
    // Since corrected rows lose the data-flagged attribute in the next render cycle,
    // just scroll to the first one found
    if (rows.length > 0) {
      rows[0].scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, []);

  // Parse pre-fetched FX rates from dedicated cree1_fxrates column
  const preFetchedRates = useMemo(() => {
    if (!job?.fxRatesJson) return null;
    try {
      const parsed = JSON.parse(job.fxRatesJson);
      console.log("FX: loaded pre-fetched rates from Dataverse:", parsed);
      return parsed?.rates || null;
    } catch {
      console.warn("FX: failed to parse fxRatesJson");
      return null;
    }
  }, [job?.fxRatesJson]);

  const handleFxCurrencyChange = useCallback((currency: string | null) => {
    // Save to Dataverse so generate-excel can read it
    if (job?.recordId) {
      import("@/services/dataverse-service").then(({ updateFxTargetCurrency }) => {
        updateFxTargetCurrency(job.recordId, currency).catch((e) =>
          console.warn("FX: failed to save target currency to Dataverse", e)
        );
      });
    }

    if (!currency) {
      setFx((prev) => ({ ...prev, targetCurrency: null, spotRate: null, avgRate: null }));
      return;
    }

    // Look up pre-fetched rates from Dataverse (no external API call)
    const rates = preFetchedRates?.[currency];
    if (rates) {
      console.log(`FX: using pre-fetched rate for ${currency}:`, rates);
      setFx((prev) => ({
        ...prev,
        targetCurrency: currency,
        spotRate: rates.spot_rate,
        avgRate: rates.average_rate,
        rateDate: "",
        rateSource: "pre-fetched",
        isLoading: false,
      }));
    } else {
      console.warn(`FX: no pre-fetched rate for ${currency}, analyst must enter manually`);
      setFx((prev) => ({
        ...prev,
        targetCurrency: currency,
        spotRate: null,
        avgRate: null,
        rateDate: "",
        rateSource: "manual",
        isLoading: false,
      }));
    }
  }, [preFetchedRates]);

  const handleFxRateChange = useCallback((spotRate: number, avgRate: number) => {
    setFx((prev) => ({ ...prev, spotRate, avgRate, rateSource: "manual" }));
  }, []);

  const UNIT_CODE_MAP: Record<string, number> = {
    ones: 833060000, thousands: 833060001, millions: 833060002, billions: 833060003,
  };

  const handleDisplayUnitChange = useCallback((unit: string) => {
    setDisplayUnit(unit);
    // Save to Dataverse so generate-excel can read it
    if (job?.recordId) {
      import("@/services/dataverse-service").then(({ updateDisplayUnit }) => {
        updateDisplayUnit(job.recordId, UNIT_CODE_MAP[unit] ?? 833060000).catch((e) =>
          console.warn("Unit: failed to save display unit to Dataverse", e)
        );
      });
    }
  }, [job?.recordId]);

  const fxRateForTab = fx.targetCurrency
    ? activeTab === "BalanceSheet" ? fx.spotRate : fx.avgRate
    : null;

  // --- Render ---

  if (!jobId) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#64748b] text-sm">
        No job ID provided. Open this page from the agent&apos;s review link.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-[#64748b] text-sm">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading review data...
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-[#dc2626] text-sm">
        <AlertTriangle className="h-5 w-5" /> Failed to load job data. Please try again.
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <SummaryBar
        job={job}
        lineItems={activeLineItems}
        onJumpToFlags={handleJumpToFlags}
        onJumpToNextUnresolved={handleJumpToNextUnresolved}
        fx={fx}
        onFxCurrencyChange={handleFxCurrencyChange}
        onFxRateChange={handleFxRateChange}
        displayUnit={displayUnit}
        onDisplayUnitChange={handleDisplayUnitChange}
      />
      <div className="flex items-center justify-between pr-4">
        <StatementTabs
          statements={statements}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          itemCounts={itemCounts}
          flagCounts={flagCounts}
        />
        <ApproveButton
          jobRecordId={job.recordId}
          jobId={job.jobId}
          onApproved={() => {}}
          correctionCount={correctionCount}
          fxTargetCurrency={fx.targetCurrency}
          fxSpotRate={fx.spotRate}
          fxAvgRate={fx.avgRate}
          fxRateDate={fx.rateDate}
        />
      </div>
      <LineItemTable
        items={filteredItems}
        fxRate={fxRateForTab}
        fxTargetCurrency={fx.targetCurrency}
        displayUnit={displayUnit}
        sourceUnit={job.currencyUnit || "ones"}
      />
    </div>
  );
}
