"""
extractor/schema_mapper.py
--------------------------
Maps the hybrid pipeline output (CU locator metadata + Python parser rows +
CU enrichment) into the v1.2 unified financial statement schema.

Produces one JSON file per statement conforming to:
  docs/schema/financial-statement-unified.schema.json
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .statement_detector import _parse_financial_value


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------

def _normalize_value(raw: str | None) -> dict:
    """
    Convert a raw display value into the v1.2 value cell format.

    Returns:
      {"column_index": ..., "raw": ..., "normalized": ..., "is_null": ...,
       "is_zero": ..., "value_kind": ..., "confidence": None}
    """
    if raw is None or not raw.strip():
        return {
            "raw": None,
            "normalized": None,
            "is_null": True,
            "is_zero": None,
            "value_kind": None,
            "confidence": None,
        }

    parsed = _parse_financial_value(raw)
    is_zero = parsed == 0.0 if parsed is not None else None

    return {
        "raw": raw,
        "normalized": parsed,
        "is_null": False,
        "is_zero": is_zero,
        "value_kind": None,  # set downstream based on section
        "confidence": None,
    }


# ---------------------------------------------------------------------------
# Column metadata builder
# ---------------------------------------------------------------------------

def _build_column_metadata(
    columns: list[str],
    statement_type: str,
) -> list[dict]:
    """Build v1.2 column metadata from the Python parser's column strings."""
    result = []
    for i, col_label in enumerate(columns):
        col_lower = col_label.lower()

        # Detect period type — expanded for Chinese/Japanese
        if any(kw in col_lower for kw in ["three months", "quarter", "q1", "q2", "q3", "q4"]):
            period_type = "quarter"
        elif any(kw in col_lower for kw in ["twelve months", "annual", "fiscal year", "fy "]):
            period_type = "annual"
        elif any(kw in col_lower for kw in ["nine months", "前三季度", "1-9月", "q1-q3"]):
            period_type = "nine_months"
        elif any(kw in col_lower for kw in ["six months", "half", "h1", "半年"]):
            period_type = "half_year"
        elif any(kw in col_lower for kw in ["year to date", "ytd"]):
            period_type = "year_to_date"
        elif statement_type == "balance_sheet":
            period_type = "instant"
        else:
            period_type = "other"

        # Extract year
        year_match = re.search(r"20\d{2}", col_label)
        fiscal_year = int(year_match.group()) if year_match else None

        # Detect if comparative (second/later column of same period type)
        is_comparative = i > 0 and fiscal_year is not None

        result.append({
            "column_index": i,
            "label": col_label,
            "label_raw": col_label,
            "period_type": period_type,
            "fiscal_year": fiscal_year,
            "fiscal_quarter": None,  # TODO: detect from label
            "start_date": None,
            "end_date": None,
            "is_comparative": is_comparative,
        })
    return result


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def _classify_value_kind(section: str, label_lower: str) -> str | None:
    """Determine value_kind from section and label context."""
    if section == "eps" or "per share" in label_lower:
        return "ratio"
    if section == "shares" or "shares" in label_lower:
        return "shares"
    if "margin" in label_lower or "rate" in label_lower or "%" in label_lower:
        return "percentage"
    return "currency"


def _is_required_anchor(canonical_key: str) -> bool:
    """Check if this row is a critical anchor that must always be present."""
    anchors = {
        "revenue", "net_income", "total_assets", "total_liabilities",
        "total_equity", "total_liabilities_and_equity",
        "net_cash_from_operating_activities",
        "net_cash_provided_by_operating_activities",
        "net_cash_used_in_investing_activities",
        "net_cash_used_in_financing_activities",
        "total_costs_and_expenses", "income_from_operations",
        "basic_eps", "diluted_eps",
    }
    return canonical_key in anchors


def build_v12_row(
    row_index: int,
    label: str,
    row_type: str,
    indent_level: int,
    values_raw: list[str | None],
    enrichment: dict,
    num_columns: int,
) -> dict:
    """Build a single v1.2 schema row."""
    canonical_key = enrichment["canonical_key"]
    section = enrichment["section"]
    label_lower = label.lower()

    # Build value cells — column_index is 0-based, matching the columns metadata
    value_cells = []
    for i in range(num_columns):
        raw = values_raw[i] if i < len(values_raw) else None
        cell = _normalize_value(raw)
        cell["column_index"] = i
        cell["value_kind"] = _classify_value_kind(section, label_lower)
        value_cells.append(cell)

    return {
        "row_index": row_index,
        "label_raw": label,
        "label_normalized": enrichment.get("label_normalized"),
        "label_language": enrichment.get("label_language", "en"),
        "canonical_key": canonical_key,
        "canonical_group": enrichment.get("canonical_group"),
        "row_type": row_type,
        "indent_level": indent_level,
        "section": section,
        "parent_canonical_key": None,  # TODO: infer from hierarchy
        "sign_hint": None,
        "is_derived_total": row_type in ("subtotal", "total"),
        "is_required_anchor": _is_required_anchor(canonical_key),
        "source_page": None,
        "source_bbox": None,
        "values": value_cells,
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _run_validation(rows: list[dict], num_columns: int) -> dict:
    """
    Run subtotal validation on the v1.2 rows.

    Returns the validation block with status, warnings, errors.
    """
    warnings = []
    errors = []

    # Check required anchors
    present_keys = {r["canonical_key"] for r in rows}
    for r in rows:
        if r["is_required_anchor"] and r["canonical_key"] not in present_keys:
            errors.append({
                "code": "MISSING_ANCHOR",
                "message": f"Required anchor row '{r['canonical_key']}' not found",
                "severity": "error",
                "row_index": None,
                "canonical_key": r["canonical_key"],
                "column_index": None,
                "expected": None,
                "actual": None,
                "difference": None,
            })

    # Subtotal validation: sum indented children, compare to subtotal
    for i, row in enumerate(rows):
        if row["row_type"] != "subtotal":
            continue

        # Find preceding children (indent > 0, until previous subtotal/total)
        children = []
        for j in range(i - 1, -1, -1):
            prev = rows[j]
            if prev["row_type"] in ("subtotal", "total"):
                break
            if prev["row_type"] == "section_header":
                continue
            if prev["row_type"] == "line_item":
                children.append(prev)

        if not children:
            continue

        for col_idx in range(num_columns):
            total_cell = row["values"][col_idx] if col_idx < len(row["values"]) else {}
            total_val = total_cell.get("normalized")
            if total_val is None:
                continue

            child_sum = 0.0
            all_parseable = True
            for child in children:
                child_cell = child["values"][col_idx] if col_idx < len(child["values"]) else {}
                child_val = child_cell.get("normalized")
                if child_val is None and not child_cell.get("is_null", True):
                    all_parseable = False
                    break
                child_sum += child_val or 0.0

            if not all_parseable:
                continue

            diff = abs(total_val - child_sum)
            if diff > 2.0:
                warnings.append({
                    "code": "SUBTOTAL_MISMATCH",
                    "message": (
                        f"Row '{row['canonical_key']}' col {col_idx}: "
                        f"subtotal={total_val}, sum of children={child_sum}, "
                        f"diff={diff}"
                    ),
                    "severity": "warning",
                    "row_index": row["row_index"],
                    "canonical_key": row["canonical_key"],
                    "column_index": col_idx,
                    "expected": child_sum,
                    "actual": total_val,
                    "difference": diff,
                })

    if errors:
        status = "failed"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"

    return {
        "status": status,
        "validator_version": "2.0.0",
        "rule_set_version": "1.0.0",
        "validation_run_id": None,
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "warnings": warnings,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Top-level assembly
# ---------------------------------------------------------------------------

def assemble_v12_statement(
    statement_type: str,
    locator_metadata: dict,
    parser_rows: list[str],
    parser_columns: list[str],
    parser_cells: list[dict],
    enrichment_lookup: dict,
    source_file_name: str,
) -> dict:
    """
    Assemble a complete v1.2 schema document from all pipeline stages.

    Args:
        statement_type: "balance_sheet", "income_statement", or "cash_flow"
        locator_metadata: Dict from CU locator (company, currency, etc.)
        parser_rows: Row labels from Python parser
        parser_columns: Column headers from Python parser
        parser_cells: Cell dicts from Python parser
        enrichment_lookup: Dict from build_enrichment_lookup()
        source_file_name: Original PDF filename
    """
    from .enrichment import enrich_all_rows

    # Extract currency/unit metadata embedded by html_table_parser in the
    # first cell (from column headers like "£000").  Use as fallback when
    # the CU locator didn't provide currency or unit.
    table_currency_unit = {}
    if parser_cells:
        table_currency_unit = parser_cells[0].get("_currency_unit", {}) or {}

    # parser_columns already contains only data column headers (label column
    # is not included), so this is the true number of data columns.
    num_columns = len(parser_columns)

    # Build grid from parser cells
    grid: dict[int, dict[int, dict]] = {}
    for c in parser_cells:
        grid.setdefault(c["row"], {})[c["col"]] = c

    # Collect all labels and row_types for batch enrichment
    sorted_indices = sorted(grid.keys())
    all_labels = []
    all_row_types = []
    all_indent_levels = []
    all_values_raw = []

    for row_idx in sorted_indices:
        label_cell = grid[row_idx].get(0, {})
        label = label_cell.get("content", "")
        row_type = label_cell.get("row_type", "line_item")
        indent_level = label_cell.get("indent_level", 0)

        values_raw = []
        for col_idx in range(1, num_columns + 1):
            val_cell = grid[row_idx].get(col_idx, {})
            content = val_cell.get("content", "")
            values_raw.append(content if content.strip() else None)

        all_labels.append(label)
        all_row_types.append(row_type)
        all_indent_levels.append(indent_level)
        all_values_raw.append(values_raw)

    # Batch enrichment (CU lookup + LLM translation for non-English)
    enrichments = enrich_all_rows(
        all_labels, all_row_types, enrichment_lookup, statement_type
    )

    # Build v1.2 rows
    v12_rows = []
    for i, row_idx in enumerate(sorted_indices):
        label = all_labels[i]
        row_type = all_row_types[i]
        indent_level = all_indent_levels[i]
        values_raw = all_values_raw[i]
        enrichment = enrichments[i]

        v12_row = build_v12_row(
            row_index=len(v12_rows),
            label=label,
            row_type=row_type,
            indent_level=indent_level,
            values_raw=values_raw,
            enrichment=enrichment,
            num_columns=num_columns,
        )
        v12_rows.append(v12_row)

    # Build column metadata
    v12_columns = _build_column_metadata(parser_columns, statement_type)

    # Run validation
    validation = _run_validation(v12_rows, num_columns)

    # Resolve currency and unit: CU locator > table column headers > defaults.
    # The CU locator provides currency/unit from AI analysis; the table parser
    # extracts them from column headers (e.g. "£000" → GBP + thousands).
    resolved_currency = (
        locator_metadata.get("currency")
        or table_currency_unit.get("currency")
        or "USD"
    )
    resolved_unit = (
        locator_metadata.get("unit")
        or table_currency_unit.get("unit")
        or "ones"
    )
    resolved_symbol = (
        _currency_to_symbol(locator_metadata.get("currency", ""))
        or table_currency_unit.get("currency_symbol")
        or _currency_to_symbol(resolved_currency)
    )

    # Assemble the document
    return {
        "schema_version": "1.2.0",
        "document_metadata": {
            "source_file_name": source_file_name,
            "source_file_hash": None,
            "company_name": locator_metadata.get("company_name"),
            "company_name_raw": locator_metadata.get("company_name_raw"),
            "report_type": _infer_report_type(source_file_name),
            "report_language": locator_metadata.get("report_language", "en"),
            "source_country": None,
            "source_exchange": None,
            "ticker": None,
            "identifier": None,
        },
        "statement_metadata": {
            "statement_type": statement_type,
            "statement_title": locator_metadata.get("title_english"),
            "statement_title_raw": locator_metadata.get("title_raw"),
            "accounting_standard": locator_metadata.get("accounting_standard"),
            "currency": resolved_currency,
            "currency_symbol": resolved_symbol,
            "unit": resolved_unit,
            "unit_raw": None,
            "is_consolidated": locator_metadata.get("is_consolidated", True),
            "is_audited": None,
            "page_range": {
                "start": locator_metadata.get("page_start", 1),
                "end": locator_metadata.get("page_end", 1),
            },
            "bbox_coordinate_system": "normalized_0_1",
        },
        "columns": v12_columns,
        "rows": v12_rows,
        "validation": validation,
    }


def _infer_report_type(filename: str) -> str:
    """Infer report type from filename."""
    fl = filename.lower()
    if "10-q" in fl:
        return "10-Q"
    if "10-k" in fl:
        return "10-K"
    if "exhibit" in fl or "earnings" in fl:
        return "earnings_release"
    if "annual" in fl:
        return "annual_report"
    if "quarter" in fl or "qr" in fl or "q1" in fl or "q2" in fl or "q3" in fl or "q4" in fl:
        return "quarterly_report"
    if "interim" in fl:
        return "interim_report"
    return "other"


def _currency_to_symbol(currency: str) -> str | None:
    """Map ISO 4217 code to display symbol."""
    return {
        "USD": "$",
        "CNY": "\u00a5",
        "JPY": "\u00a5",
        "EUR": "\u20ac",
        "GBP": "\u00a3",
    }.get(currency)
