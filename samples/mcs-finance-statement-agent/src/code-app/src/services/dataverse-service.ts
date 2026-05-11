/**
 * Dataverse Service — HITL Review Grid
 * Fetches job, statements, and line items for a given jobId.
 * Writes analyst corrections back to Dataverse.
 */
import { Cree1_extractionjobsService } from "@/generated/services/Cree1_extractionjobsService";
import { Cree1_extractedstatement1sService } from "@/generated/services/Cree1_extractedstatement1sService";
import { Cree1_extractedlineitemsService } from "@/generated/services/Cree1_extractedlineitemsService";
import type { ReviewJob, ReviewStatement, ReviewLineItem, StatementType, ReviewStatus, RowType } from "@/types/extraction";

const STATEMENT_TYPE_MAP: Record<number, StatementType> = {
  833060000: "IncomeStatement",
  833060001: "BalanceSheet",
  833060002: "CashFlow",
};

const ROW_TYPE_MAP: Record<number, RowType> = {
  833060000: "SectionHeader",
  833060001: "LineItem",
  833060002: "Subtotal",
  833060003: "Total",
};

const REVIEW_STATUS_MAP: Record<number, ReviewStatus> = {
  833060000: "Pending",
  833060001: "Accepted",
  833060002: "Corrected",
  833060003: "Flagged",
  833060004: "Resolved",
};

const CURRENCY_DISPLAY_MAP: Record<number, string> = {
  833060000: "USD", 833060001: "CNY", 833060002: "JPY",
  833060003: "EUR", 833060004: "GBP", 833060005: "AUD",
  833060006: "CAD", 833060007: "HKD", 833060008: "SGD",
};

const CURRENCY_UNIT_DISPLAY_MAP: Record<number, string> = {
  833060000: "ones", 833060001: "thousands", 833060002: "millions", 833060003: "billions",
};

const STATUS_MAP: Record<number, string> = {
  833060000: "Uploading",
  833060001: "Extracting",
  833060002: "PendingReview",
  833060003: "Reviewing",
  833060004: "Approved",
  833060005: "Rejected",
};

export async function fetchJobByJobId(jobId: string): Promise<ReviewJob | null> {
  const safeJobId = sanitizeGuid(jobId);
  const result = await Cree1_extractionjobsService.getAll({
    filter: `cree1_jobid eq '${safeJobId}'`,
  });
  const row = result.data?.[0];
  if (!row) return null;
  return {
    recordId: row.cree1_extractionjobid,
    jobId: row.cree1_jobid || "",
    companyName: row.cree1_companyname || "",
    status: STATUS_MAP[row.cree1_status as unknown as number] || "Unknown",
    statementsFound: Number(row.cree1_statementsfound) || 0,
    totalLineItems: Number(row.cree1_totallineitems) || 0,
    avgConfidence: Number(row.cree1_avgconfidence) || 0,
    currency: row.cree1_currencyname || CURRENCY_DISPLAY_MAP[row.cree1_currency as unknown as number] || "",
    currencyUnit: (() => {
      const rawLabel = (row.cree1_currencyunitname || "").toLowerCase();
      const known = ["ones", "thousands", "millions", "billions"];
      if (known.includes(rawLabel)) return rawLabel;
      // Dataverse SDK may return option-set value as string or number — handle both
      const code = Number(row.cree1_currencyunit);
      return (!isNaN(code) && CURRENCY_UNIT_DISPLAY_MAP[code]) || "ones";
    })(),
    periods: row.cree1_periods || "",
    summaryJson: row.cree1_summaryjsonfull || row.cree1_summaryjson || null,
    fxRatesJson: (row as any).cree1_fxrates || null,
  };
}

function sanitizeGuid(value: string): string {
  return value.replace(/[^a-zA-Z0-9\-]/g, "");
}

export async function fetchStatementsByJobId(jobId: string): Promise<ReviewStatement[]> {
  const safeJobId = sanitizeGuid(jobId);
  const result = await Cree1_extractedstatement1sService.getAll({
    filter: `cree1_jobid eq '${safeJobId}'`,
    orderBy: ["cree1_statementtype asc"],
  });
  if (!result.data) return [];
  return result.data.map((row) => ({
    recordId: row.cree1_extractedstatement1id,
    statementTitle: row.cree1_statementtitle || "",
    statementName: row.cree1_statementname || "",
    statementType: STATEMENT_TYPE_MAP[row.cree1_statementtype as unknown as number] || "BalanceSheet",
    pageRangeStart: row.cree1_pagerangestart ? Number(row.cree1_pagerangestart) : null,
    pageRangeEnd: row.cree1_pagerangeend ? Number(row.cree1_pagerangeend) : null,
  }));
}

export async function fetchLineItemsByJobId(jobId: string): Promise<ReviewLineItem[]> {
  const safeJobId = sanitizeGuid(jobId);
  const result = await Cree1_extractedlineitemsService.getAll({
    filter: `cree1_jobid eq '${safeJobId}'`,
    orderBy: ["cree1_rowindex asc", "cree1_columnindex asc"],
  });
  if (!result.data) return [];
  return result.data.map((row) => ({
    recordId: row.cree1_extractedlineitemid,
    jobId: row.cree1_jobid,
    statementRecordId: row._cree1_extractedstatement_value || "",
    statementType: "BalanceSheet", // Placeholder — resolved via statementRecordId lookup in review.tsx
    lineItemName: row.cree1_lineitemname || "",
    rowIndex: Number(row.cree1_rowindex) || 0,
    rowType: ROW_TYPE_MAP[row.cree1_rowtype as unknown as number] || "LineItem",
    indentLevel: Number(row.cree1_indentlevel) || 0,
    sectionName: row.cree1_sectionname || "",
    canonicalKey: row.cree1_canonicalkey || "",
    labelRaw: row.cree1_labelraw || "",
    period: row.cree1_period || "",
    periodType: row.cree1_periodtype || "",
    columnIndex: Number(row.cree1_columnindex) || 0,
    valueRaw: row.cree1_valueraw || null,
    valueNormalized: row.cree1_valuenormalized ? Number(row.cree1_valuenormalized) : null,
    valueKind: row.cree1_valuekind || "",
    aiConfidence: row.cree1_aiconfidence ? Number(row.cree1_aiconfidence) : null,
    sourcePage: row.cree1_sourcepage ? Number(row.cree1_sourcepage) : null,
    analystCorrectedValue: row.cree1_analystcorrectedvalue || null,
    reviewStatus: REVIEW_STATUS_MAP[row.cree1_reviewstatus as unknown as number] || "Pending",
    analystNotes: row.cree1_analystnotes || null,
  }));
}

export async function updateLineItemCorrection(
  recordId: string,
  correctedValue: string,
  notes?: string
): Promise<void> {
  await Cree1_extractedlineitemsService.update(recordId, {
    cree1_analystcorrectedvalue: correctedValue,
    cree1_reviewstatus: 833060002 as any,
    ...(notes ? { cree1_analystnotes: notes } : {}),
  });
}

export async function updateJobStatus(recordId: string, status: "Approved" | "Reviewing"): Promise<void> {
  const statusCode = status === "Approved" ? 833060004 : 833060003;
  await Cree1_extractionjobsService.update(recordId, {
    cree1_status: statusCode as any,
  });
}

export async function updateFxTargetCurrency(recordId: string, currency: string | null): Promise<void> {
  await Cree1_extractionjobsService.update(recordId, {
    cree1_fxtargetcurrency: currency || "",
  } as any);
}

export async function updateDisplayUnit(recordId: string, unitCode: number): Promise<void> {
  await Cree1_extractionjobsService.update(recordId, {
    cree1_currencyunit: unitCode,
  } as any);
}
