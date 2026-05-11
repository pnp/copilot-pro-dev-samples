/** Types for the HITL Review Grid — maps to Dataverse columns */

export type StatementType = "IncomeStatement" | "BalanceSheet" | "CashFlow";
export type ReviewStatus = "Pending" | "Accepted" | "Corrected" | "Flagged" | "Resolved";
export type RowType = "SectionHeader" | "LineItem" | "Subtotal" | "Total";

export interface ReviewStatement {
  recordId: string;
  statementTitle: string;
  statementName: string;
  statementType: StatementType;
  pageRangeStart: number | null;
  pageRangeEnd: number | null;
}

export interface ReviewLineItem {
  recordId: string;
  jobId: string;
  statementRecordId: string;
  statementType: StatementType;
  lineItemName: string;
  rowIndex: number;
  rowType: RowType;
  indentLevel: number;
  sectionName: string;
  canonicalKey: string;
  labelRaw: string;
  period: string;
  periodType: string;
  columnIndex: number;
  valueRaw: string | null;
  valueNormalized: number | null;
  valueKind: string;
  aiConfidence: number | null;
  sourcePage: number | null;
  analystCorrectedValue: string | null;
  reviewStatus: ReviewStatus;
  analystNotes: string | null;
}

export interface ReviewJob {
  recordId: string;
  jobId: string;
  companyName: string;
  status: string;
  statementsFound: number;
  totalLineItems: number;
  avgConfidence: number;
  currency: string;
  currencyUnit: string;
  periods: string;
  summaryJson: string | null;
  fxRatesJson: string | null;
}

/** FX conversion state for the HITL grid */
export interface FxConversionState {
  targetCurrency: string | null;  // null = no conversion
  spotRate: number | null;        // For BS items (closing rate)
  avgRate: number | null;         // For IS/CF items (period average)
  rateDate: string;
  rateSource: string;
  isLoading: boolean;
}

export const TARGET_CURRENCIES = [
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "AUD", symbol: "A$", name: "Australian Dollar" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "HKD", symbol: "HK$", name: "Hong Kong Dollar" },
  { code: "SGD", symbol: "S$", name: "Singapore Dollar" },
  { code: "JPY", symbol: "¥", name: "Japanese Yen" },
] as const;
