import { useState, useRef, useEffect } from "react";

interface EditableCellProps {
  value: string | null;
  correctedValue: string | null;
  confidence: number | null;
  flagReason?: string;
  onSave: (newValue: string) => void;
}

export function EditableCell({ value, correctedValue, confidence, flagReason, onSave }: EditableCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(correctedValue || value || "");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  // Reset draft when props change (e.g., unit switch)
  useEffect(() => {
    if (!editing) setDraft(correctedValue || value || "");
  }, [correctedValue, value]);

  const displayValue = correctedValue || value || "";
  const isCorrected = correctedValue !== null && correctedValue !== value;

  let bgClass = "";
  if (confidence !== null) {
    if (confidence < 0.5) bgClass = "bg-red-50";
    else if (confidence < 0.7) bgClass = "bg-orange-50";
    else if (confidence < 0.85) bgClass = "bg-yellow-50";
  }

  if (editing) {
    return (
      <input
        ref={inputRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          setEditing(false);
          if (draft !== (correctedValue || value || "")) {
            onSave(draft);
          }
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            setEditing(false);
            if (draft !== (correctedValue || value || "")) {
              onSave(draft);
            }
          }
          if (e.key === "Escape") {
            setEditing(false);
            setDraft(correctedValue || value || "");
          }
        }}
        className="w-full px-1.5 py-0.5 text-sm border border-[#6B4EE6] rounded outline-none bg-white"
      />
    );
  }

  // Determine flag badge text and color
  let badgeText: string | null = null;
  let badgeColor = "#d97706"; // amber-600 default

  if (isCorrected) {
    badgeText = "\u2713 Resolved";
    badgeColor = "#059669"; // emerald-600
  } else if (flagReason) {
    badgeText = flagReason;
  }

  return (
    <div
      onClick={() => setEditing(true)}
      className={`px-1.5 py-0.5 text-sm cursor-pointer rounded ${bgClass} ${
        isCorrected ? "text-[#6B4EE6] font-medium" : "text-[#1a1a2e]"
      } hover:ring-1 hover:ring-[#6B4EE6]`}
      title={confidence !== null ? `Confidence: ${(confidence * 100).toFixed(0)}%` : undefined}
    >
      {displayValue || "\u2014"}
      {badgeText && (
        <div
          style={{ fontSize: "10px", lineHeight: "14px", color: badgeColor }}
          className="truncate"
        >
          {badgeText}
        </div>
      )}
    </div>
  );
}
