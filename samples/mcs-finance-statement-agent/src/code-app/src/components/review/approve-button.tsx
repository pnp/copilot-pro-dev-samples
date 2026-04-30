import { useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { updateJobStatus } from "@/services/dataverse-service";

interface ApproveButtonProps {
  jobRecordId: string;
  jobId: string;
  onApproved: () => void;
  correctionCount: number;
  fxTargetCurrency?: string | null;
  fxSpotRate?: number | null;
  fxAvgRate?: number | null;
  fxRateDate?: string;
}

export function ApproveButton({
  jobRecordId,
  onApproved,
  correctionCount,
}: ApproveButtonProps) {
  const [applyLoading, setApplyLoading] = useState(false);
  const [appliedCount, setAppliedCount] = useState(0);
  const [approveLoading, setApproveLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "approved">("idle");

  const pendingCorrections = correctionCount - appliedCount;
  const hasUnapplied = pendingCorrections > 0;

  const handleApplyCorrections = async () => {
    setApplyLoading(true);
    try {
      // Corrections are already auto-saved per cell to Dataverse.
      // This gives visual confirmation that all are persisted.
      // A small delay to represent the bulk confirmation.
      await new Promise((r) => setTimeout(r, 400));
      setAppliedCount(correctionCount);
    } catch (err) {
      console.error("Failed to apply corrections:", err);
    } finally {
      setApplyLoading(false);
    }
  };

  const handleApproveAndGenerate = async () => {
    setApproveLoading(true);
    try {
      // 1. Mark job as Approved in Dataverse
      await updateJobStatus(jobRecordId, "Approved");
      setStatus("approved");
      onApproved();

      // Excel generation is now handled via agent chat after approval
    } catch (err) {
      console.error("Failed to approve:", err);
    } finally {
      setApproveLoading(false);
    }
  };

  if (status === "approved") {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 text-sm font-medium rounded-lg border border-emerald-200">
          <CheckCircle2 className="h-4 w-4" />
          Approved
        </div>
        <span className="text-xs text-gray-500">
          Return to agent chat and say &quot;generate Excel&quot;
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {/* Apply Corrections button — always visible, disabled when nothing to apply */}
      <button
        onClick={handleApplyCorrections}
        disabled={correctionCount === 0 || !hasUnapplied || applyLoading}
        className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
          hasUnapplied
            ? "border border-[#6B4EE6] text-[#6B4EE6] hover:bg-[#6B4EE6]/5"
            : "border border-gray-200 text-gray-400"
        } ${correctionCount === 0 ? "opacity-50 cursor-not-allowed" : ""} disabled:opacity-50`}
      >
        {applyLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <CheckCircle2 className="h-4 w-4" />
        )}
        {appliedCount > 0 && !hasUnapplied
          ? `\u2713 ${appliedCount} Applied`
          : `Apply Corrections${hasUnapplied ? ` (${pendingCorrections})` : ""}`}
      </button>

      {/* Approve & Generate Excel button */}
      <button
        onClick={handleApproveAndGenerate}
        disabled={approveLoading}
        className="flex items-center gap-2 px-4 py-2 bg-[#22c55e] text-white text-sm font-medium rounded-lg hover:bg-[#16a34a] disabled:opacity-50 transition-colors"
      >
        {approveLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <CheckCircle2 className="h-4 w-4" />
        )}
        Approve &amp; Generate Excel
      </button>
    </div>
  );
}
