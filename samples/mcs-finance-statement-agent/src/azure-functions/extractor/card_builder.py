"""Adaptive Card JSON builder for financial statement HITL review."""

import json
import re
from typing import Any

STATEMENT_DISPLAY_NAMES = {
    "balance_sheet": "Balance Sheet",
    "income_statement": "Income Statement",
    "cash_flow": "Cash Flow",
}

SECTION_CHOICES = [
    {"title": "Current Assets", "value": "current_assets"},
    {"title": "Non-Current Assets", "value": "non_current_assets"},
    {"title": "Current Liabilities", "value": "current_liabilities"},
    {"title": "Non-Current Liabilities", "value": "non_current_liabilities"},
    {"title": "Equity", "value": "equity"},
    {"title": "Revenue", "value": "revenue"},
    {"title": "Operating Expenses", "value": "operating_expenses"},
    {"title": "Tax", "value": "tax"},
    {"title": "Other", "value": "other"},
]

ROW_TYPE_CHOICES = [
    {"title": "Line Item", "value": "line_item"},
    {"title": "Section Header", "value": "section_header"},
    {"title": "Subtotal", "value": "subtotal"},
    {"title": "Total", "value": "total"},
]

EDIT_ALL_PAGE_SIZE = 20


# ─── Navigator Card ─────────────────────────────────────────────────────────


REVIEW_GRID_URL = os.environ.get(
    "REVIEW_GRID_URL",
    "https://apps.powerapps.com/play/e/Default-269a92bb-9fea-4197-94ce-f1993452a98a"
    "/a/33824507-997c-4c99-9c70-b498395ef0fe"
    "?tenantId=269a92bb-9fea-4197-94ce-f1993452a98a",
)


def build_navigator_card(
    company_name: str,
    currency: str,
    unit: str,
    confidence: dict,
    summary: list,
    job_id: str = "",
) -> dict:
    """Build the entry-point Navigator card showing all 3 statements."""

    # Build summary table rows
    table_rows = [{
        "type": "TableRow",
        "style": "accent",
        "cells": [
            {"type": "TableCell", "items": [
                {"type": "TextBlock", "text": "Statement", "weight": "Bolder", "size": "Small"},
            ]},
            {"type": "TableCell", "items": [
                {"type": "TextBlock", "text": "Confidence", "weight": "Bolder", "size": "Small"},
            ]},
            {"type": "TableCell", "items": [
                {"type": "TextBlock", "text": "Rows", "weight": "Bolder", "size": "Small",
                 "horizontalAlignment": "Right"},
            ]},
        ],
    }]

    summary_map = {s.get("statement_type", s.get("statement", "")): s.get("row_count", s.get("rows", 0)) for s in summary}

    for stmt_key in ("balance_sheet", "income_statement", "cash_flow"):
        display_name = STATEMENT_DISPLAY_NAMES[stmt_key]
        conf_entry = confidence.get(stmt_key)
        row_count = summary_map.get(stmt_key, 0)

        if conf_entry is None:
            level_text = "\u2014 Not found"
            color = "Default"
        else:
            level = conf_entry.get("level", "medium")
            flagged = conf_entry.get("flagged_rows", [])
            if level == "high":
                level_text = "\u2713 High"
                color = "Good"
            elif level == "medium":
                level_text = f"\u26a0 Medium ({len(flagged)} issues)"
                color = "Warning"
            else:
                level_text = f"\u26a0 Low ({len(flagged)} issues)"
                color = "Attention"

        table_rows.append({
            "type": "TableRow",
            "cells": [
                {"type": "TableCell", "items": [
                    {"type": "TextBlock", "text": display_name, "weight": "Bolder"},
                ]},
                {"type": "TableCell", "items": [
                    {"type": "TextBlock", "text": level_text, "color": color},
                ]},
                {"type": "TableCell", "items": [
                    {"type": "TextBlock", "text": str(row_count),
                     "horizontalAlignment": "Right"},
                ]},
            ],
        })

    body = [
        {"type": "TextBlock", "text": "Extraction Complete", "size": "Large", "weight": "Bolder"},
        {"type": "TextBlock", "text": f"{company_name}", "size": "Medium", "isSubtle": True},
        {"type": "TextBlock", "text": f"Currency: {currency}  \u2502  Unit: {unit}",
         "isSubtle": True, "spacing": "Small"},
        {
            "type": "Table",
            "gridStyle": "accent",
            "firstRowAsHeader": True,
            "showGridLines": True,
            "columns": [{"width": 2}, {"width": 2}, {"width": 1}],
            "rows": table_rows,
        },
    ]

    actions = [
        {"type": "Action.Submit", "title": "Generate Excel", "data": {"action": "skip_review"}},
    ]

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": body,
        "actions": actions,
    }


# ─── Statement Review Card ──────────────────────────────────────────────────


def _flag_reason(row: dict, validation: dict) -> str | None:
    """Determine the flag reason for a row."""
    reasons = []
    if not row.get("label_raw"):
        reasons.append("Missing label")
    # Check validation warnings for subtotal mismatch
    for w in validation.get("warnings", []):
        if isinstance(w, dict) and w.get("row_index") == row["row_index"] and "subtotal" in str(w).lower():
            reasons.append("Subtotal mismatch")
            break
    if row.get("section") == "other":
        reasons.append("Unclassified section")
    for val in row.get("values", []):
        if val.get("normalized") is None and val.get("raw"):
            reasons.append("Value parse error")
            break
    label = (row.get("label_raw") or "").lower()
    if "total" in label and row.get("row_type") == "line_item":
        reasons.append("Possible type mismatch")
    return "; ".join(reasons) if reasons else None


def _get_row_value(row: dict, field: str, corrections: dict) -> str:
    """Get the value for a row field, applying corrections if present."""
    row_key = f"row_{row['row_index']}"
    corr = corrections.get(row_key, {})
    if field == "label":
        return corr.get("label", row.get("label_normalized") or row.get("label_raw", ""))
    elif field == "section":
        return corr.get("section", row.get("section", "other"))
    elif field == "row_type":
        return corr.get("row_type", row.get("row_type", "line_item"))
    elif field.startswith("val_"):
        col_idx = int(field.split("_")[1])
        if field in corr:
            return corr[field]
        values = row.get("values", [])
        if col_idx < len(values):
            return values[col_idx].get("raw", "") or ""
        return ""
    return ""


# ─── Table-based row builders ────────────────────────────────────────────────


def _build_table_header_row(columns: list) -> dict:
    """Build the header row for the financial data table."""
    cells = [
        {"type": "TableCell", "items": [
            {"type": "TextBlock", "text": "Line Item", "weight": "Bolder", "size": "Small"},
        ]},
    ]
    for col in columns:
        cells.append({"type": "TableCell", "items": [
            {"type": "TextBlock", "text": col["label"], "weight": "Bolder",
             "size": "Small", "horizontalAlignment": "Right"},
        ]})
    return {"type": "TableRow", "style": "accent", "cells": cells}


def _build_readonly_table_row(row: dict, columns: list) -> dict:
    """Build a read-only table row with proper visual hierarchy."""
    row_type = row.get("row_type", "line_item")
    is_emphasis = row_type in ("section_header", "subtotal", "total")
    weight = "Bolder" if is_emphasis else "Default"

    label = row.get("label_normalized") or row.get("label_raw", "") or ""

    cells = [
        {"type": "TableCell", "items": [
            {"type": "TextBlock", "text": label, "weight": weight, "wrap": True},
        ]},
    ]
    for col in columns:
        ci = col["column_index"]
        values = row.get("values", [])
        raw = values[ci].get("raw", "") if ci < len(values) else ""
        cells.append({"type": "TableCell", "items": [
            {"type": "TextBlock", "text": raw or "\u2014", "weight": weight,
             "horizontalAlignment": "Right"},
        ]})

    table_row: dict[str, Any] = {"type": "TableRow", "cells": cells}
    if row_type in ("subtotal", "total"):
        table_row["style"] = "accent"
    return table_row


def _build_editable_table_row(
    row: dict, columns: list, corrections: dict, flag_text: str | None,
) -> dict:
    """Build an editable table row with inline input fields.

    The label cell contains: flag badge, label input, and section/type dropdowns.
    Value cells contain text inputs aligned with the table columns.
    """
    idx = row["row_index"]

    # ── Label cell: flag + input + section/type ──
    label_items: list[dict[str, Any]] = []
    if flag_text:
        label_items.append({
            "type": "TextBlock", "text": f"\u26a0 {flag_text}",
            "size": "Small", "color": "Warning", "wrap": True,
        })
    label_items.append({
        "type": "Input.Text",
        "id": f"row_{idx}_label",
        "value": _get_row_value(row, "label", corrections),
        "placeholder": "Label",
    })
    label_items.append({
        "type": "ColumnSet",
        "columns": [
            {
                "type": "Column", "width": "stretch",
                "items": [{
                    "type": "Input.ChoiceSet",
                    "id": f"row_{idx}_section",
                    "value": _get_row_value(row, "section", corrections),
                    "style": "compact",
                    "choices": SECTION_CHOICES,
                }],
            },
            {
                "type": "Column", "width": "stretch",
                "items": [{
                    "type": "Input.ChoiceSet",
                    "id": f"row_{idx}_row_type",
                    "value": _get_row_value(row, "row_type", corrections),
                    "style": "compact",
                    "choices": ROW_TYPE_CHOICES,
                }],
            },
        ],
    })

    cells: list[dict[str, Any]] = [{"type": "TableCell", "items": label_items}]

    # ── Value cells ──
    for col in columns:
        ci = col["column_index"]
        cells.append({"type": "TableCell", "items": [{
            "type": "Input.Text",
            "id": f"row_{idx}_val_{ci}",
            "value": _get_row_value(row, f"val_{ci}", corrections),
        }]})

    table_row: dict[str, Any] = {"type": "TableRow", "cells": cells}
    if flag_text:
        table_row["style"] = "warning"
    return table_row


def build_statement_review_card(
    statement_type: str,
    statement_json: dict,
    confidence_entry: dict,
    corrections: dict,
    step_num: int,
    total_steps: int,
    editable: bool = True,
    edit_all: bool = False,
    edit_all_page: int = 0,
) -> dict:
    """Build a review card for a single statement.

    All rendering modes use a single Table element for consistent column
    alignment, grid lines, and proper header row.

    Rendering modes:
      - Standard (editable=True, edit_all=False): all rows in original order,
        flagged rows as editable table rows, clean rows as read-only table rows.
      - Edit All (edit_all=True): paginated, ALL rows as editable table rows.
      - Read-only (editable=False): all rows as read-only table rows.
    """

    display_name = STATEMENT_DISPLAY_NAMES.get(statement_type, statement_type)
    rows = statement_json.get("rows", [])
    columns = statement_json.get("columns", [])
    validation = statement_json.get("validation", {})
    metadata = statement_json.get("statement_metadata", {})

    level = confidence_entry.get("level", "medium")
    flagged_indices = set(confidence_entry.get("flagged_rows", []))

    # Page info
    page_range = metadata.get("page_range", {})
    page_start = page_range.get("start", "?")
    page_end = page_range.get("end", "?")
    page_text = f"Pages {page_start}-{page_end}" if page_start != page_end else f"Page {page_start}"

    level_display = {"high": "High", "medium": "Medium", "low": "Low"}.get(level, level.title())
    confidence_icon = "\u2713" if level == "high" else "\u26a0"

    body: list[dict[str, Any]] = [
        {"type": "TextBlock", "text": f"{display_name} Review", "size": "Large", "weight": "Bolder"},
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "items": [{"type": "TextBlock", "text": f"{confidence_icon} {level_display} Confidence"}],
                },
                {
                    "type": "Column",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"{page_text}  \u2502  {len(rows)} rows  \u2502  {len(flagged_indices)} flagged",
                        }
                    ],
                },
            ],
        },
    ]

    # Handle empty statement
    if len(rows) == 0:
        body.append({"type": "TextBlock", "text": "No data extracted", "isSubtle": True})
        actions = _build_navigation_actions(step_num, total_steps, editable)
        return _wrap_card(body, actions)

    total_pages = max(1, -(-len(rows) // EDIT_ALL_PAGE_SIZE))  # ceil division

    # ── Build the data table ──
    col_defs = [{"width": 3}] + [{"width": 1} for _ in columns]
    table_rows = [_build_table_header_row(columns)]

    if editable and edit_all:
        # ── Edit All mode: paginated, every row editable ──
        edit_all_page = min(edit_all_page, total_pages - 1)
        page_start_idx = edit_all_page * EDIT_ALL_PAGE_SIZE
        page_end_idx = min(page_start_idx + EDIT_ALL_PAGE_SIZE, len(rows))
        page_rows = rows[page_start_idx:page_end_idx]

        body.append({
            "type": "TextBlock",
            "text": f"Editing rows {page_start_idx + 1}\u2013{page_end_idx} of {len(rows)}",
            "isSubtle": True,
        })
        for row in page_rows:
            flag_text = None
            if row["row_index"] in flagged_indices:
                flag_text = _flag_reason(row, validation) or "Review needed"
            table_rows.append(
                _build_editable_table_row(row, columns, corrections, flag_text)
            )

    elif editable:
        # ── Standard mode: flagged rows editable, clean rows read-only ──
        for row in rows:
            if row["row_index"] in flagged_indices:
                reason = _flag_reason(row, validation) or "Review needed"
                table_rows.append(
                    _build_editable_table_row(row, columns, corrections, reason)
                )
            else:
                table_rows.append(_build_readonly_table_row(row, columns))

    else:
        # ── Read-only mode ──
        for row in rows:
            table_rows.append(_build_readonly_table_row(row, columns))

    body.append({
        "type": "Table",
        "gridStyle": "accent",
        "firstRowAsHeader": True,
        "showGridLines": True,
        "columns": col_defs,
        "rows": table_rows,
    })

    actions = _build_navigation_actions(
        step_num, total_steps, editable,
        edit_all=edit_all, edit_all_page=edit_all_page, total_pages=total_pages,
    )
    return _wrap_card(body, actions)


def _build_navigation_actions(
    step_num: int,
    total_steps: int,
    editable: bool,
    *,
    edit_all: bool = False,
    edit_all_page: int = 0,
    total_pages: int = 1,
) -> list:
    actions = []

    # Edit All pagination
    if edit_all:
        if edit_all_page > 0:
            actions.append({
                "type": "Action.Submit", "title": "\u2190 Page",
                "data": {"action": "edit_all_page_prev"},
            })
        if edit_all_page < total_pages - 1:
            actions.append({
                "type": "Action.Submit", "title": "Page \u2192",
                "data": {"action": "edit_all_page_next"},
            })

    # Statement navigation
    if step_num > 1:
        actions.append({"type": "Action.Submit", "title": "\u2190 Previous", "data": {"action": "previous"}})
    if step_num < total_steps:
        actions.append({"type": "Action.Submit", "title": "Next \u2192", "data": {"action": "next"}})
    else:
        actions.append({
            "type": "Action.Submit",
            "title": "Submit & Generate Excel",
            "data": {"action": "submit"},
        })

    # Mode switches
    if editable and not edit_all:
        actions.append({"type": "Action.Submit", "title": "Edit All", "data": {"action": "edit_all"}})
    if not editable:
        actions.append({"type": "Action.Submit", "title": "Edit Anyway", "data": {"action": "edit_anyway"}})
    return actions


def _wrap_card(body: list, actions: list) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": body,
        "actions": actions,
    }


# ─── Parse Card Submission ───────────────────────────────────────────────────

_ROW_FIELD_RE = re.compile(r"^row_(\d+)_(.+)$")


def parse_card_submission(payload: dict, statement_json: dict) -> tuple[str, dict]:
    """Parse flat Adaptive Card submission into (action, corrections) tuple."""

    action = payload.get("action", "")
    rows = statement_json.get("rows", [])

    # Index rows by row_index for quick lookup
    row_map = {r["row_index"]: r for r in rows}

    corrections: dict[str, dict] = {}

    for key, submitted_value in payload.items():
        if key == "action":
            continue
        m = _ROW_FIELD_RE.match(key)
        if not m:
            continue
        row_idx = int(m.group(1))
        field = m.group(2)
        row = row_map.get(row_idx)
        if row is None:
            continue

        original = _get_original_value(row, field)
        if str(submitted_value) != str(original):
            row_key = f"row_{row_idx}"
            if row_key not in corrections:
                corrections[row_key] = {}
            corrections[row_key][field] = submitted_value

    return action, corrections


def _get_original_value(row: dict, field: str) -> str:
    """Get the original value from a row for comparison."""
    if field == "label":
        return row.get("label_raw", "")
    elif field == "section":
        return row.get("section", "other")
    elif field == "row_type":
        return row.get("row_type", "line_item")
    elif field.startswith("val_"):
        col_idx = int(field.split("_")[1])
        values = row.get("values", [])
        if col_idx < len(values):
            return values[col_idx].get("raw", "") or ""
        return ""
    return ""


# ─── Session State Management ────────────────────────────────────────────────

STATEMENT_ORDER = ["balance_sheet", "income_statement", "cash_flow"]


def init_session_state(confidence: dict, job_id: str = "",
                       available_statements: list[str] | None = None) -> str:
    """Create the initial session state from confidence data.

    Determines which statements actually exist and builds an ordered list.
    A statement is included only if it appears in *available_statements*
    (when provided) or its confidence level is not 'not_found'.
    Returns a JSON string that the topic stores opaquely.
    """
    if available_statements is not None:
        statements = [
            stype for stype in STATEMENT_ORDER
            if stype in available_statements
        ]
    else:
        statements = [
            stype for stype in STATEMENT_ORDER
            if confidence.get(stype, {}).get("level") != "not_found"
            and confidence.get(stype) is not None
        ]
    state = {
        "jobId": job_id,
        "phase": "navigator",
        "step": 0,
        "statements": statements,
        "corrections": {},
        "editable": False,
        "editAll": False,
        "editAllPage": 0,
    }
    return json.dumps(state, ensure_ascii=False)


def advance_session_state(
    session_state_str: str,
    raw_payload: dict,
    statement_json: dict | None = None,
) -> tuple[str, str]:
    """Advance the session state machine based on a card submit payload.

    Args:
        session_state_str: Current session state JSON string.
        raw_payload: The flat key-value payload from the Adaptive Card submit.
        statement_json: The v1.2 statement dict for the current step
                        (needed to diff corrections). None for navigator actions.

    Returns:
        (topic_action, updated_session_state_str) where topic_action is one of:
          - "continue": show another card (loop back)
          - "done": apply corrections and export
          - "skip": export without corrections
    """
    state = json.loads(session_state_str)
    if not isinstance(raw_payload, dict):
        raw_payload = {}
    raw_action = raw_payload.get("action", "")
    phase = state.get("phase", "navigator")
    step = state.get("step", 0)
    statements = state.get("statements", [])
    total_steps = len(statements)

    # ── Navigator phase ──
    if phase == "navigator":
        if raw_action == "skip_review":
            return "skip", json.dumps(state, ensure_ascii=False)
        # start_review → advance to step 1
        state["phase"] = "review"
        state["step"] = 1
        state["editable"] = False
        state["editAll"] = False
        state["editAllPage"] = 0
        return "continue", json.dumps(state, ensure_ascii=False)

    # ── Review phase ──
    # First, extract corrections from the card payload for the current statement
    current_stype = statements[step - 1] if 0 < step <= total_steps else None

    if statement_json is not None and current_stype:
        _action, new_corrections = parse_card_submission(raw_payload, statement_json)
        # Merge new corrections into accumulated corrections for this statement
        if new_corrections:
            if current_stype not in state["corrections"]:
                state["corrections"][current_stype] = {}
            for row_key, fields in new_corrections.items():
                if row_key not in state["corrections"][current_stype]:
                    state["corrections"][current_stype][row_key] = {}
                state["corrections"][current_stype][row_key].update(fields)

    # Now handle the action
    if raw_action == "next":
        if step >= total_steps:
            # Past the last statement → done
            state["phase"] = "export"
            return "done", json.dumps(state, ensure_ascii=False)
        state["step"] = step + 1
        state["editable"] = False
        state["editAll"] = False
        state["editAllPage"] = 0
        return "continue", json.dumps(state, ensure_ascii=False)

    if raw_action == "previous":
        state["step"] = max(1, step - 1)
        state["editable"] = False
        state["editAll"] = False
        state["editAllPage"] = 0
        return "continue", json.dumps(state, ensure_ascii=False)

    if raw_action == "submit":
        state["phase"] = "export"
        return "done", json.dumps(state, ensure_ascii=False)

    if raw_action in ("edit", "edit_anyway"):
        state["editable"] = True
        state["editAll"] = False
        state["editAllPage"] = 0
        return "continue", json.dumps(state, ensure_ascii=False)

    if raw_action == "edit_all":
        state["editable"] = True
        state["editAll"] = True
        state["editAllPage"] = 0
        return "continue", json.dumps(state, ensure_ascii=False)

    if raw_action == "edit_all_page_next":
        state["editAllPage"] = state.get("editAllPage", 0) + 1
        return "continue", json.dumps(state, ensure_ascii=False)

    if raw_action == "edit_all_page_prev":
        state["editAllPage"] = max(0, state.get("editAllPage", 0) - 1)
        return "continue", json.dumps(state, ensure_ascii=False)

    # Unknown action — treat as continue (safe fallback)
    return "continue", json.dumps(state, ensure_ascii=False)
