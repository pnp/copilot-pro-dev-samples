import { useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from "@tanstack/react-table";
import { AlertTriangle } from "lucide-react";
import { EditableCell } from "./editable-cell";
import { useAppStore } from "@/store/app-store";
import { updateLineItemCorrection } from "@/services/dataverse-service";
import type { ReviewLineItem } from "@/types/extraction";

interface PivotedRow {
  row: ReviewLineItem;
  values: Map<number, ReviewLineItem>;
  isFlagged: boolean;
}

const columnHelper = createColumnHelper<PivotedRow>();

const UNIT_DIVISORS: Record<string, number> = {
  ones: 1, thousands: 1_000, millions: 1_000_000, billions: 1_000_000_000,
};

interface LineItemTableProps {
  items: ReviewLineItem[];
  fxRate: number | null;          // The rate to apply (spot for BS, avg for IS/CF)
  fxTargetCurrency: string | null;
  displayUnit?: string;           // "ones" | "thousands" | "millions" | "billions"
}

/** Format period header: "Quarterly Q4 2025" / "Annual FY 2025" / raw label */
function formatPeriodHeader(label: string, periodType: string): string {
  if (!periodType || !label) return label;
  const pt = periodType.toLowerCase();
  if (pt === "quarterly" || pt === "quarter") {
    return label.match(/Q\d/i) ? `Quarterly ${label}` : `Quarterly ${label}`;
  }
  if (pt === "annual" || pt === "year") {
    return `Annual FY ${label}`;
  }
  return label;
}

/** Compute delta percentage between two numeric values */
function computeDelta(current: number | null, prior: number | null): string | null {
  if (current === null || prior === null || prior === 0) return null;
  const pct = ((current - prior) / Math.abs(prior)) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

interface LineItemTablePropsWithSource extends LineItemTableProps {
  sourceUnit?: string;  // The unit Dataverse values are actually stored in (from job.currencyUnit)
}

export function LineItemTable({ items, fxRate, fxTargetCurrency, displayUnit = "ones", sourceUnit = "ones" }: LineItemTablePropsWithSource) {
  // Dataverse values are in sourceUnit. To display in targetUnit:
  // displayValue = dataverseValue × (sourceDivisor / targetDivisor)
  const sourceDivisor = UNIT_DIVISORS[sourceUnit] || 1;
  const targetDivisor = UNIT_DIVISORS[displayUnit] || 1;
  const unitScaleFactor = sourceDivisor / targetDivisor;
  const updateLineItem = useAppStore((s) => s.updateLineItem);

  // Get unique periods — deduplicate by period label (not columnIndex)
  const periods = useMemo(() => {
    const seen = new Map<string, { colIdx: number; label: string; periodType: string }>();
    items.forEach((item) => {
      const key = `${item.periodType}|${item.period}`;
      if (!seen.has(key)) {
        seen.set(key, { colIdx: item.columnIndex, label: item.period, periodType: item.periodType });
      }
    });
    return Array.from(seen.values()).sort((a, b) => a.colIdx - b.colIdx);
  }, [items]);

  // Delta columns disabled — shown only in Excel if needed
  const deltaPairs: { currentIdx: number; priorIdx: number; label: string }[] = [];

  // Pivot: group by rowIndex, spread periods as columns
  const pivotedRows = useMemo(() => {
    const grouped = new Map<number, PivotedRow>();
    items.forEach((item) => {
      if (!grouped.has(item.rowIndex)) {
        const isFlagged = item.reviewStatus === "Flagged" || (item.aiConfidence !== null && item.aiConfidence < 0.7);
        grouped.set(item.rowIndex, { row: item, values: new Map(), isFlagged });
      }
      const entry = grouped.get(item.rowIndex)!;
      entry.values.set(item.columnIndex, item);
      // A row is flagged if ANY cell in it is flagged
      if (item.reviewStatus === "Flagged" || (item.aiConfidence !== null && item.aiConfidence < 0.7)) {
        entry.isFlagged = true;
      }
    });
    return Array.from(grouped.values()).sort((a, b) => a.row.rowIndex - b.row.rowIndex);
  }, [items]);

  const columns = useMemo(() => {
    const cols: any[] = [
      columnHelper.display({
        id: "label",
        header: "Line Item",
        cell: ({ row }) => {
          const item = row.original.row;
          const indent = item.indentLevel * 16;
          const isHeader = item.rowType === "SectionHeader";
          const isTotal = item.rowType === "Total" || item.rowType === "Subtotal";
          const isFlagged = row.original.isFlagged;
          return (
            <div
              style={{ paddingLeft: indent }}
              className={`text-sm flex items-center gap-1 ${isHeader ? "font-semibold text-[#1a1a2e]" : ""} ${isTotal ? "font-medium text-[#1a1a2e]" : ""}`}
            >
              {isFlagged && !isHeader && (
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
              )}
              {item.lineItemName || item.labelRaw}
            </div>
          );
        },
        size: 300,
      }),
    ];

    // Add period columns with delta columns interleaved
    let deltaIdx = 0;
    periods.forEach((p) => {
      // Period value column
      cols.push(
        columnHelper.display({
          id: `period_${p.colIdx}`,
          header: fxTargetCurrency
            ? `${formatPeriodHeader(p.label, p.periodType)} (${fxTargetCurrency})`
            : formatPeriodHeader(p.label, p.periodType),
          cell: ({ row }) => {
            const valueItem = row.original.values.get(p.colIdx);
            if (!valueItem) return <div className="text-sm text-[#94a3b8]">{"\u2014"}</div>;

            // For display: use valueRaw (full precision) when showing in original unit,
            // use valueNormalized × scaleFactor when user changes unit
            const rawNumeric = valueItem.valueRaw ? parseFloat(valueItem.valueRaw.replace(/,/g, "")) : null;
            const scaledValue = displayUnit === "ones" && rawNumeric !== null && !isNaN(rawNumeric)
              ? rawNumeric  // Full precision from original extraction
              : valueItem.valueNormalized !== null
                ? valueItem.valueNormalized * unitScaleFactor
                : null;
            const showConverted = fxRate && fxTargetCurrency && scaledValue !== null;
            const convertedValue = showConverted ? scaledValue! * fxRate : null;

            // Compute flag reason for this cell
            let flagReason: string | undefined;
            if (valueItem.aiConfidence !== null && valueItem.aiConfidence < 0.5) {
              flagReason = `\u26A0 Low confidence: ${Math.round(valueItem.aiConfidence * 100)}%`;
            } else if (valueItem.aiConfidence !== null && valueItem.aiConfidence < 0.7) {
              flagReason = `\u26A0 Confidence: ${Math.round(valueItem.aiConfidence * 100)}%`;
            } else if (
              (valueItem.valueRaw === null || valueItem.valueRaw === "") &&
              valueItem.rowType === "LineItem"
            ) {
              flagReason = "\u26A0 Value expected";
            }

            return (
              <div>
                {convertedValue !== null ? (
                  <>
                    {/* Show converted value as primary */}
                    <div className="text-sm text-[#1a1a2e] font-mono text-right pr-2">
                      {convertedValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    {/* Original value in small gray text */}
                    <div className="text-[10px] text-[#94a3b8] font-mono text-right pr-2">
                      {valueItem.valueRaw || "\u2014"}
                    </div>
                  </>
                ) : (
                  <EditableCell
                    value={
                      displayUnit === "ones"
                        ? valueItem.valueRaw  // Full precision for ones
                        : valueItem.valueNormalized !== null
                          ? (valueItem.valueNormalized * unitScaleFactor).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                          : valueItem.valueRaw
                    }
                    correctedValue={
                      valueItem.analystCorrectedValue
                        ? displayUnit === "ones"
                          ? valueItem.analystCorrectedValue  // Full precision for ones
                          : (parseFloat(valueItem.analystCorrectedValue.replace(/,/g, "")) * unitScaleFactor).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        : null
                    }
                    confidence={valueItem.aiConfidence}
                    flagReason={flagReason}
                    onSave={(newValue) => {
                      // Reverse-scale: user edits in display unit, save in Dataverse unit
                      const numericVal = parseFloat(newValue.replace(/,/g, ""));
                      const dataverseUnitVal = !isNaN(numericVal)
                        ? (numericVal / unitScaleFactor).toString()
                        : newValue;
                      updateLineItem(valueItem.recordId, {
                        analystCorrectedValue: dataverseUnitVal,
                        reviewStatus: "Corrected",
                      });
                      updateLineItemCorrection(valueItem.recordId, dataverseUnitVal).catch(console.error);
                    }}
                  />
                )}
              </div>
            );
          },
          size: 140,
        })
      );

      // Check if this period starts a delta pair
      const pair = deltaPairs[deltaIdx];
      if (pair && pair.currentIdx === p.colIdx) {
        cols.push(
          columnHelper.display({
            id: `delta_${pair.currentIdx}_${pair.priorIdx}`,
            header: pair.label,
            cell: ({ row }) => {
              if (row.original.row.rowType === "SectionHeader") return null;
              const currItem = row.original.values.get(pair.currentIdx);
              const priorItem = row.original.values.get(pair.priorIdx);
              const delta = computeDelta(
                currItem?.valueNormalized ?? null,
                priorItem?.valueNormalized ?? null,
              );
              if (!delta) return <div className="text-sm text-[#94a3b8]">{"\u2014"}</div>;
              const isPositive = delta.startsWith("+");
              const isLarge = Math.abs(parseFloat(delta)) > 100;
              return (
                <div className={`text-sm text-right pr-2 ${isPositive ? "text-emerald-600" : "text-red-600"} ${isLarge ? "font-semibold" : ""}`}>
                  {delta}
                </div>
              );
            },
            size: 130,
          })
        );
        deltaIdx++;
      }
    });

    return cols;
  }, [periods, deltaPairs, updateLineItem, fxRate, fxTargetCurrency, unitScaleFactor, displayUnit]);

  const table = useReactTable({
    data: pivotedRows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (items.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#64748b] text-sm">
        No line items for this statement.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 z-10">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="bg-[#1a472a] text-white">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-3 py-2 text-left text-xs font-medium"
                  style={{ width: header.getSize() }}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            const isHeader = row.original.row.rowType === "SectionHeader";
            const isFlagged = row.original.isFlagged;
            return (
              <tr
                key={row.id}
                data-flagged={isFlagged || undefined}
                className={`border-b border-[#f0eef5] ${
                  isHeader
                    ? "bg-[#f1f0f7]"
                    : isFlagged
                    ? "bg-red-100 border-l-4 border-l-red-500 hover:bg-red-200"
                    : "hover:bg-[#fafaff]"
                }`}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-1.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
