import type { ReviewStatement } from "@/types/extraction";

interface StatementTabsProps {
  statements: ReviewStatement[];
  activeTab: string;
  onTabChange: (statementType: string) => void;
  itemCounts: Record<string, number>;
  flagCounts: Record<string, number>;
}

export function StatementTabs({ statements, activeTab, onTabChange, itemCounts, flagCounts }: StatementTabsProps) {
  const TAB_LABELS: Record<string, string> = {
    IncomeStatement: "Income Statement",
    BalanceSheet: "Balance Sheet",
    CashFlow: "Cash Flow",
  };

  return (
    <div className="flex border-b border-[#e5e2f0] bg-white px-4">
      {statements.map((stmt) => {
        const isActive = activeTab === stmt.statementType;
        const count = itemCounts[stmt.statementType] || 0;
        const flags = flagCounts[stmt.statementType] || 0;
        return (
          <button
            key={stmt.recordId}
            onClick={() => onTabChange(stmt.statementType)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              isActive
                ? "border-[#6B4EE6] text-[#6B4EE6]"
                : "border-transparent text-[#64748b] hover:text-[#1a1a2e]"
            }`}
          >
            {TAB_LABELS[stmt.statementType] || stmt.statementTitle}
            <span className="ml-1.5 text-xs text-[#94a3b8]">({count})</span>
            {flags > 0 && (
              <span className="ml-1 text-xs text-amber-600 font-medium">&middot; {flags} flagged</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
