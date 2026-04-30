import { useState } from "react";
import type { ReviewJob, ReviewLineItem, FxConversionState } from "@/types/extraction";

interface SummaryBarProps {
  job: ReviewJob;
  lineItems: ReviewLineItem[];
  onJumpToFlags?: () => void;
  onJumpToNextUnresolved?: () => void;
  fx: FxConversionState;
  onFxCurrencyChange: (currency: string | null) => void;
  onFxRateChange: (spotRate: number, avgRate: number) => void;
  displayUnit?: string;
  onDisplayUnitChange?: (unit: string) => void;
}

const CURRENCIES = [
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "AUD", symbol: "A$", name: "Australian Dollar" },
  { code: "EUR", symbol: "\u20ac", name: "Euro" },
  { code: "GBP", symbol: "\u00a3", name: "British Pound" },
  { code: "HKD", symbol: "HK$", name: "Hong Kong Dollar" },
  { code: "SGD", symbol: "S$", name: "Singapore Dollar" },
  { code: "JPY", symbol: "\u00a5", name: "Japanese Yen" },
];

const DISPLAY_UNITS = [
  { code: "ones", label: "Ones (as reported)" },
  { code: "thousands", label: "Thousands" },
  { code: "millions", label: "Millions" },
  { code: "billions", label: "Billions" },
];

export function SummaryBar({ job, lineItems, onJumpToFlags, onJumpToNextUnresolved, fx, onFxCurrencyChange, onFxRateChange, displayUnit, onDisplayUnitChange }: SummaryBarProps) {
  const [editingSpotRate, setEditingSpotRate] = useState(false);
  const [editingAvgRate, setEditingAvgRate] = useState(false);
  const [tempSpotRate, setTempSpotRate] = useState("");
  const [tempAvgRate, setTempAvgRate] = useState("");

  const totalItems = lineItems.length;

  // A flagged item is one that was originally flagged OR has low confidence
  const flaggedItems = lineItems.filter(
    (i) => i.reviewStatus === "Flagged" || (i.aiConfidence !== null && i.aiConfidence < 0.7)
  );
  const totalFlagged = flaggedItems.length;

  // Resolved = items that were flagged but now corrected or accepted
  const resolvedCount = flaggedItems.filter(
    (i) => i.reviewStatus === "Corrected"
  ).length;

  // Still-unresolved flagged count (for the old display)
  const unresolvedCount = totalFlagged - resolvedCount;

  // Breakdown of flag reasons
  const lowConfidenceCount = lineItems.filter(
    (i) => i.aiConfidence !== null && i.aiConfidence < 0.7 && i.reviewStatus !== "Corrected"
  ).length;

  const correctedCount = lineItems.filter((i) => i.reviewStatus === "Corrected").length;
  const itemsWithConf = lineItems.filter((i) => i.aiConfidence !== null);
  const avgConf = itemsWithConf.length > 0
    ? itemsWithConf.reduce((sum, i) => sum + i.aiConfidence!, 0) / itemsWithConf.length
    : 0;
  const confPct = Math.round(avgConf * 100);
  const confColor = confPct >= 85 ? "#22c55e" : confPct >= 60 ? "#f59e0b" : "#dc2626";

  const allResolved = totalFlagged > 0 && resolvedCount >= totalFlagged;

  // Don't show source currency in the dropdown
  const availableCurrencies = CURRENCIES.filter((c) => c.code !== job.currency);

  function handleSpotRateSave() {
    const val = parseFloat(tempSpotRate);
    if (!isNaN(val) && val > 0) {
      onFxRateChange(val, fx.avgRate || val);
    }
    setEditingSpotRate(false);
  }

  function handleAvgRateSave() {
    const val = parseFloat(tempAvgRate);
    if (!isNaN(val) && val > 0) {
      onFxRateChange(fx.spotRate || val, val);
    }
    setEditingAvgRate(false);
  }

  // Build progress bar string (visual block representation)
  function renderProgressBlocks() {
    const totalBlocks = 10;
    const filledBlocks = Math.round((resolvedCount / Math.max(totalFlagged, 1)) * totalBlocks);
    const filled = "\u2588".repeat(filledBlocks);
    const empty = "\u2591".repeat(totalBlocks - filledBlocks);
    return `${filled}${empty}`;
  }

  return (
    <div className="border-b border-[#e5e2f0] bg-white">
      {/* Main header row */}
      <div className="px-4 py-3 flex items-center gap-5">
        {/* Company + periods */}
        <div className="flex flex-col min-w-0">
          <span className="font-semibold text-sm text-[#1a1a2e] truncate">{job.companyName}</span>
          <span className="text-xs text-[#64748b]">
            Periods: {job.periods} &middot; Statements: {job.statementsFound}
            {job.currency && <> &middot; {job.currency} {job.currencyUnit && `(${job.currencyUnit})`}</>}
          </span>
        </div>

        {/* Confidence bar */}
        <div className="flex items-center gap-2 ml-auto">
          <div className="w-24 h-2 bg-[#e5e2f0] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${confPct}%`, backgroundColor: confColor }}
            />
          </div>
          <span className="text-xs font-medium" style={{ color: confColor }}>
            {confPct}%
          </span>
        </div>

        {/* Counts */}
        <div className="flex items-center gap-3 text-xs text-[#64748b]">
          <span>{totalItems} items</span>
          <span>&middot;</span>
          <button
            onClick={onJumpToFlags}
            className={`${unresolvedCount > 0 ? "text-amber-600 font-medium hover:underline cursor-pointer" : "text-[#22c55e]"}`}
          >
            {unresolvedCount} flagged
          </button>
          <span>&middot;</span>
          <span>{correctedCount} corrected</span>
        </div>

        {/* Status badge */}
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          job.status === "Approved" ? "bg-emerald-100 text-emerald-700" :
          job.status === "PendingReview" ? "bg-amber-100 text-amber-700" :
          "bg-gray-100 text-gray-600"
        }`}>
          {job.status}
        </span>
      </div>

      {/* Unit + FX Conversion bar */}
      <div className="px-4 pb-3 flex items-center gap-4 text-xs">
        {/* Display unit selector */}
        <span className="text-[#64748b] font-medium">Unit:</span>
        <select
          value={displayUnit || "ones"}
          onChange={(e) => onDisplayUnitChange?.(e.target.value)}
          className="border border-[#d1d5db] rounded px-2 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-[#6B4EE6]"
        >
          {DISPLAY_UNITS.map((u) => (
            <option key={u.code} value={u.code}>{u.label}</option>
          ))}
        </select>

        <span className="text-[#d1d5db]">|</span>

        <span className="text-[#64748b] font-medium">FX Conversion:</span>

        {/* Currency selector */}
        <select
          value={fx.targetCurrency || ""}
          onChange={(e) => onFxCurrencyChange(e.target.value || null)}
          className="border border-[#d1d5db] rounded px-2 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-[#6B4EE6]"
        >
          <option value="">No conversion (original {job.currency})</option>
          {availableCurrencies.map((c) => (
            <option key={c.code} value={c.code}>
              {c.code} ({c.symbol}) — {c.name}
            </option>
          ))}
        </select>

        {/* Rates (shown only when conversion active) */}
        {fx.targetCurrency && (
          <>
            {fx.isLoading ? (
              <span className="text-[#64748b] animate-pulse">Fetching rates...</span>
            ) : (
              <>
                {/* Spot rate (BS) */}
                <div className="flex items-center gap-1">
                  <span className="text-[#64748b]">Spot (BS):</span>
                  {editingSpotRate ? (
                    <input
                      type="number"
                      step="0.0001"
                      value={tempSpotRate}
                      onChange={(e) => setTempSpotRate(e.target.value)}
                      onBlur={handleSpotRateSave}
                      onKeyDown={(e) => e.key === "Enter" && handleSpotRateSave()}
                      autoFocus
                      className="w-20 border border-[#6B4EE6] rounded px-1 py-0.5 text-xs focus:outline-none"
                    />
                  ) : (
                    <button
                      onClick={() => { setTempSpotRate(String(fx.spotRate || "")); setEditingSpotRate(true); }}
                      className="font-mono font-medium text-[#1a1a2e] hover:text-[#6B4EE6] hover:underline"
                    >
                      {fx.spotRate?.toFixed(4) || "\u2014"}
                    </button>
                  )}
                </div>

                {/* Average rate (IS/CF) */}
                <div className="flex items-center gap-1">
                  <span className="text-[#64748b]">Avg (IS/CF):</span>
                  {editingAvgRate ? (
                    <input
                      type="number"
                      step="0.0001"
                      value={tempAvgRate}
                      onChange={(e) => setTempAvgRate(e.target.value)}
                      onBlur={handleAvgRateSave}
                      onKeyDown={(e) => e.key === "Enter" && handleAvgRateSave()}
                      autoFocus
                      className="w-20 border border-[#6B4EE6] rounded px-1 py-0.5 text-xs focus:outline-none"
                    />
                  ) : (
                    <button
                      onClick={() => { setTempAvgRate(String(fx.avgRate || "")); setEditingAvgRate(true); }}
                      className="font-mono font-medium text-[#1a1a2e] hover:text-[#6B4EE6] hover:underline"
                    >
                      {fx.avgRate?.toFixed(4) || "\u2014"}
                    </button>
                  )}
                </div>

                <span className="text-[#94a3b8]">
                  as at {fx.rateDate} · {fx.rateSource}
                </span>
              </>
            )}
          </>
        )}
      </div>

      {/* Alert / Progress banner */}
      {totalFlagged > 0 && (
        <div className={`mx-4 mb-3 px-3 py-2 rounded-md border text-xs ${
          allResolved
            ? "bg-emerald-50 border-emerald-200 text-emerald-800"
            : "bg-amber-50 border-amber-200 text-amber-800"
        }`}>
          {allResolved ? (
            <div className="flex items-center gap-2">
              <span className="font-medium">{"\u2713"} All items reviewed</span>
              <span className="text-emerald-600">Ready to approve.</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {/* Progress bar */}
              <span className="font-mono text-[11px] tracking-tight" style={{ color: unresolvedCount > 0 ? "#d97706" : "#059669" }}>
                {renderProgressBlocks()} {resolvedCount}/{totalFlagged}
              </span>
              <span className="font-medium">
                Review Progress: {resolvedCount} of {totalFlagged} resolved
              </span>
              {/* Breakdown */}
              {lowConfidenceCount > 0 && (
                <>
                  <span className="text-amber-400">&middot;</span>
                  <span className="text-amber-600">{lowConfidenceCount} low confidence</span>
                </>
              )}
              {/* Jump to next unresolved */}
              <button
                onClick={onJumpToNextUnresolved || onJumpToFlags}
                className="ml-auto text-amber-700 font-medium hover:underline"
              >
                Jump to next unresolved &darr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
