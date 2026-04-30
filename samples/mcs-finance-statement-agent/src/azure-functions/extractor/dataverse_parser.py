"""
Parses extraction pipeline results (v1.2 schema) into Dataverse-ready dicts.
Each function returns dicts with cree1_ prefixed keys matching Dataverse column logical names.
All choice fields use integer values (PicklistType).
"""
import json
from typing import Any

from extractor.confidence_scorer import score_statement, flag_rows

# Choice values
STATUS_PENDING_REVIEW = 833060002
REVIEW_STATUS_PENDING = 833060000
REVIEW_STATUS_FLAGGED = 833060003

STATEMENT_TYPE_MAP = {
    "balance_sheet": 833060001,
    "income_statement": 833060000,
    "cash_flow": 833060002,
}

ROW_TYPE_MAP = {
    "section_header": 833060000,
    "line_item": 833060001,
    "subtotal": 833060002,
    "total": 833060003,
}

# Picklist mappings for ExtractionJob choice fields
LANGUAGE_MAP = {"en": 833060000, "zh": 833060001, "jp": 833060002}
CURRENCY_MAP = {
    "USD": 833060000, "CNY": 833060001, "JPY": 833060002,
    "EUR": 833060003, "GBP": 833060004, "AUD": 833060005,
    "CAD": 833060006, "HKD": 833060007, "SGD": 833060008,
}
CURRENCY_UNIT_MAP = {"ones": 833060000, "thousands": 833060001, "millions": 833060002, "billions": 833060003}
REPORT_TYPE_MAP = {"annual_report": 833060000, "quarterly_report": 833060001, "10-K": 833060000, "10-Q": 833060001}
ACCOUNTING_STANDARD_MAP = {"IFRS": 833060000, "Chinese_ASBE": 833060001, "US_GAAP": 833060002, "US-GAAP": 833060002, "GAAP": 833060002}


# Dataverse decimal field limit: -100,000,000,000 to 100,000,000,000
DATAVERSE_DECIMAL_LIMIT = 99_999_999_999

# Unit scaling: from source unit → target unit, with divisor
UNIT_SCALING = {
    "ones":      {"target": "millions",  "divisor": 1_000_000,     "target_code": 833060002},
    "thousands": {"target": "millions",  "divisor": 1_000,         "target_code": 833060002},
    "millions":  {"target": "billions",  "divisor": 1_000,         "target_code": 833060003},
}


def normalize_values_for_dataverse(
    job_row: dict[str, Any],
    line_items: list[tuple[str, dict[str, Any]]],
    source_unit: str,
) -> None:
    """Scale valuenormalized across ALL line items if any value exceeds the Dataverse decimal limit.

    Modifies job_row and line_items in place:
    - Divides all cree1_valuenormalized by the appropriate scaling factor
    - Updates cree1_currencyunit on the job row to reflect the new unit

    This ensures the entire report uses a consistent unit that fits within
    Dataverse's decimal column range (-100B to +100B).
    """
    if not line_items:
        return

    # Check if any value exceeds the limit
    max_abs_value = 0.0
    for _, item in line_items:
        val = item.get("cree1_valuenormalized")
        if val is not None:
            try:
                max_abs_value = max(max_abs_value, abs(float(val)))
            except (TypeError, ValueError):
                pass

    if max_abs_value <= DATAVERSE_DECIMAL_LIMIT:
        return  # All values fit, no scaling needed

    # Determine scaling factor based on source unit
    scaling = UNIT_SCALING.get(source_unit)
    if not scaling:
        # Already in billions or unknown unit — can't scale further
        import logging
        logging.warning(
            f"Value {max_abs_value} exceeds Dataverse limit but unit '{source_unit}' "
            f"cannot be scaled further. Values may be truncated."
        )
        return

    divisor = scaling["divisor"]
    target_unit_code = scaling["target_code"]
    target_unit_name = scaling["target"]

    import logging
    logging.info(
        f"Scaling values: {source_unit} -> {target_unit_name} (÷{divisor:,}) "
        f"because max value {max_abs_value:,.2f} exceeds Dataverse limit {DATAVERSE_DECIMAL_LIMIT:,}"
    )

    # Apply scaling to ALL line items
    for _, item in line_items:
        val = item.get("cree1_valuenormalized")
        if val is not None:
            try:
                item["cree1_valuenormalized"] = round(float(val) / divisor, 10)
            except (TypeError, ValueError):
                pass

    # Update the unit on the job row
    job_row["cree1_currencyunit"] = target_unit_code


def parse_job_row(job_id: str, result: dict, file_name: str = "") -> dict[str, Any]:
    """Parse pipeline result into an ExtractionJob row."""
    doc_meta = {}
    stmt_meta = {}
    total_rows = 0
    periods = set()

    for stype in ["balance_sheet", "income_statement", "cash_flow"]:
        stmt = result.get(stype)
        if not stmt or not isinstance(stmt, dict):
            continue
        if not doc_meta:
            doc_meta = stmt.get("document_metadata", {})
        if not stmt_meta:
            stmt_meta = stmt.get("statement_metadata", {})
        total_rows += len(stmt.get("rows", []))
        for col in stmt.get("columns", []):
            periods.add(col.get("label", ""))

    statements_found = sum(1 for s in ["balance_sheet", "income_statement", "cash_flow"]
                           if result.get(s) and isinstance(result[s], dict))

    # Use statement-level confidence scores from confidence_scorer
    avg_confidence = None
    conf = result.get("confidence", {})
    if isinstance(conf, dict):
        scores = [v["score"] for v in conf.values() if isinstance(v, dict) and "score" in v]
        if scores:
            avg_confidence = sum(scores) / len(scores)

    row = {
        "cree1_jobid": job_id,
        "cree1_companyname": doc_meta.get("company_name", ""),
        "cree1_filename": file_name,
        "cree1_statementsfound": statements_found,
        "cree1_totallineitems": total_rows,
        "cree1_avgconfidence": avg_confidence,
        "cree1_periods": ",".join(sorted(periods)),
        "cree1_summaryjsonfull": json.dumps(result.get("summary", []), ensure_ascii=False),
        "cree1_status": STATUS_PENDING_REVIEW,
    }

    # Only include choice fields if we have a valid mapping (avoid 400 errors)
    lang = doc_meta.get("report_language", "")
    if lang in LANGUAGE_MAP:
        row["cree1_reportlanguage"] = LANGUAGE_MAP[lang]

    currency = stmt_meta.get("currency", "")
    if currency in CURRENCY_MAP:
        row["cree1_currency"] = CURRENCY_MAP[currency]

    unit = stmt_meta.get("unit", "")
    if unit in CURRENCY_UNIT_MAP:
        row["cree1_currencyunit"] = CURRENCY_UNIT_MAP[unit]

    report_type = doc_meta.get("report_type", "")
    if report_type in REPORT_TYPE_MAP:
        row["cree1_reporttype"] = REPORT_TYPE_MAP[report_type]

    acct_std = stmt_meta.get("accounting_standard", "")
    if acct_std in ACCOUNTING_STANDARD_MAP:
        row["cree1_accountingstandard"] = ACCOUNTING_STANDARD_MAP[acct_std]

    return row


def parse_statement_row(statement_type: str, stmt: dict) -> dict[str, Any]:
    """Parse a single statement dict into an ExtractedStatement row."""
    meta = stmt.get("statement_metadata", {})
    page_range = meta.get("page_range", {})

    return {
        "cree1_jobid": "",  # Set by _write_to_dataverse before sending
        "cree1_statementtitle": meta.get("statement_title", ""),
        "cree1_statementname": statement_type,
        "cree1_statementtype": STATEMENT_TYPE_MAP.get(statement_type, 833060000),
        "cree1_pagerangestart": page_range.get("start"),
        "cree1_pagerangeend": page_range.get("end"),
        "cree1_isconsolidated": meta.get("is_consolidated"),
        "cree1_isaudited": meta.get("is_audited"),
        "cree1_rawstatementjsonfull": json.dumps(stmt, ensure_ascii=False),
        "cree1_reviewcomplete": False,
    }


def parse_line_item_rows(statement_type: str, stmt: dict, confidence_result: dict | None = None) -> list[dict[str, Any]]:
    """Parse rows x columns into ExtractedLineItem rows (one per value per period).

    Parameters
    ----------
    confidence_result : dict | None
        Output of confidence_scorer.score_statement(). Used to:
        - Apply statement-level confidence as fallback when per-cell confidence is null
        - Flag rows identified by flag_rows() (validation warnings, parse failures, etc.)
    """
    columns = stmt.get("columns", [])
    col_lookup = {c["column_index"]: c for c in columns}

    # Identify label column indices to skip (e.g., 项目/Item — not a value column)
    _LABEL_COLUMN_NAMES = {"项目", "item", "rubriques", ""}
    label_col_indices = set()
    for c in columns:
        label_lower = c.get("label", "").strip().lower()
        if label_lower in _LABEL_COLUMN_NAMES and c.get("fiscal_year") is None:
            label_col_indices.add(c["column_index"])

    # Build value columns (non-label) for correct period mapping
    value_columns = [c for c in columns if c["column_index"] not in label_col_indices]

    # Statement-level confidence fallback
    stmt_confidence = confidence_result["score"] if confidence_result else None
    flagged_row_indices = set(confidence_result.get("flagged_rows", [])) if confidence_result else set()

    items = []
    for row in stmt.get("rows", []):
        row_idx = row.get("row_index")
        is_flagged = row_idx in flagged_row_indices

        values = row.get("values", [])

        # The values array may have entries for ALL columns including the label column.
        # When a label column exists, it shifts values by 1 position. We detect this
        # by comparing values count vs columns count, and map by position to
        # value (period) columns.
        if label_col_indices and len(values) > len(value_columns):
            # More values than period columns — label column included in values.
            # Take first N values where N = number of period columns.
            data_values = values[:len(value_columns)]
        else:
            # No label column, or values already aligned with period columns.
            data_values = values

        for vi, val in enumerate(data_values):
            if vi >= len(value_columns):
                break
            col = value_columns[vi]

            # Use per-cell confidence if available, fall back to statement-level
            cell_confidence = val.get("confidence")
            if cell_confidence is None:
                cell_confidence = stmt_confidence

            items.append({
                "cree1_jobid": "",  # Set by _write_to_dataverse before sending
                "cree1_lineitemname": row.get("label_normalized") or row.get("label_raw", ""),
                "cree1_rowindex": row_idx,
                "cree1_rowtype": ROW_TYPE_MAP.get(row.get("row_type", ""), 833060001),
                "cree1_indentlevel": row.get("indent_level", 0),
                "cree1_sectionname": row.get("section", ""),
                "cree1_canonicalkey": row.get("canonical_key", ""),
                "cree1_canonicalgroup": row.get("canonical_group", ""),
                "cree1_labelraw": row.get("label_raw", ""),
                "cree1_period": col.get("label", ""),
                "cree1_periodtype": col.get("period_type", ""),
                "cree1_periodenddate": col.get("end_date"),
                "cree1_columnindex": col.get("column_index", vi),
                "cree1_valueraw": val.get("raw"),
                "cree1_valuenormalized": val.get("normalized"),
                "cree1_valuekind": val.get("value_kind", ""),
                "cree1_aiconfidence": cell_confidence,
                "cree1_sourcepage": row.get("source_page"),
                "cree1_signhint": row.get("sign_hint"),
                "cree1_reviewstatus": REVIEW_STATUS_FLAGGED if is_flagged else REVIEW_STATUS_PENDING,
            })

    return items
