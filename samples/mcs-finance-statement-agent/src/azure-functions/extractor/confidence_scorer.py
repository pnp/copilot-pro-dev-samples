"""
extractor/confidence_scorer.py
--------------------------------
Confidence scoring module for extracted financial statements.

Computes a composite confidence score (0.0-1.0) from 6 signals:
  1. subtotal_validation  — ratio of subtotals that pass cross-validation
  2. section_coverage     — ratio of expected section groups present
  3. row_count            — 1.0 if row count is in expected range
  4. column_dates         — ratio of columns whose label contains a 20xx year
  5. empty_label_ratio    — 1.0 if blank labels <= 5% of rows
  6. leaked_headers       — 1.0 if no leaked header rows detected

Public API:
  score_statement(stmt, statement_type) -> dict
  flag_rows(stmt) -> set[int]

Individual signal functions are importable for testing (prefixed with _score_).
"""

import re
from typing import Dict, List, Set

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Signal weights (must sum to 1.0)
WEIGHTS: Dict[str, float] = {
    "subtotal_validation": 0.20,
    "section_coverage": 0.20,
    "row_count": 0.15,
    "column_dates": 0.15,
    "empty_label_ratio": 0.15,
    "leaked_headers": 0.15,
}

# Confidence level thresholds
THRESHOLDS: Dict[str, float] = {
    "high": 0.85,
    "medium": 0.60,
}

# Expected row count ranges per statement type
ROW_RANGES: Dict[str, tuple] = {
    "balance_sheet": (15, 120),
    "income_statement": (10, 80),
    "cash_flow": (15, 80),
}

# Expected section groups per statement type.
# Each entry is a list of groups; a group is a set of alternative section names
# (the group is satisfied if ANY section in the set appears in the rows).
SECTION_GROUPS: Dict[str, List[Set[str]]] = {
    "balance_sheet": [
        {"assets", "current_assets", "non_current_assets"},
        {"liabilities", "current_liabilities", "non_current_liabilities"},
        {"equity"},
    ],
    "income_statement": [
        {"revenue"},
        {"operating_expenses", "expenses"},
    ],
    "cash_flow": [
        {"operating_activities"},
        {"investing_activities"},
        {"financing_activities"},
    ],
}

# Regex to detect a 4-digit year in the 2000s range within a column label
_YEAR_RE = re.compile(r"\b20\d{2}\b")

# Regex to detect year-like or unit-string values (leaked headers)
# Matches: 4-digit year (20xx), "USD millions", "in thousands", "(USD)", etc.
_LEAKED_VALUE_RE = re.compile(
    r"^(\d{4}|[A-Za-z$€£¥].*(?:thousand|million|billion|USD|EUR|GBP|JPY|AUD|CAD).*)$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Signal functions
# ---------------------------------------------------------------------------

def _score_subtotal_validation(stmt: dict) -> float:
    """
    Ratio of subtotals that pass cross-validation.

    Warnings come from stmt["validation"]["warnings"] list.
    Each warning has a "row_index" key. Count subtotals (rows where
    row_type == "subtotal"), count how many have a matching row_index
    in warnings. Score = (total - failed) / total.
    If no subtotals, return 1.0.
    """
    rows = stmt.get("rows", [])
    warnings = stmt.get("validation", {}).get("warnings", [])

    subtotal_indices = {
        row["row_index"]
        for row in rows
        if row.get("row_type") == "subtotal"
    }

    if not subtotal_indices:
        return 1.0

    warned_indices = {w["row_index"] for w in warnings}
    failed = subtotal_indices & warned_indices
    return (len(subtotal_indices) - len(failed)) / len(subtotal_indices)


def _score_section_coverage(stmt: dict, statement_type: str) -> float:
    """
    Check if expected section groups are present.

    Score = groups_matched / total_groups.
    A group matches if ANY section in the group set is present in the rows.
    """
    groups = SECTION_GROUPS.get(statement_type, [])
    if not groups:
        return 1.0

    rows = stmt.get("rows", [])
    present_sections = {row.get("section", "") for row in rows}

    matched = sum(
        1 for group in groups if group & present_sections
    )
    return matched / len(groups)


def _score_row_count(stmt: dict, statement_type: str) -> float:
    """
    1.0 if row count is within the expected range, 0.0 otherwise.
    """
    rows = stmt.get("rows", [])
    count = len(rows)
    lo, hi = ROW_RANGES.get(statement_type, (0, float("inf")))
    return 1.0 if lo <= count <= hi else 0.0


def _score_column_dates(stmt: dict) -> float:
    """
    Ratio of columns whose label contains a 4-digit year (20xx).
    Returns 0.0 if there are no columns.
    """
    columns = stmt.get("columns", [])
    if not columns:
        return 0.0

    with_year = sum(
        1 for col in columns if _YEAR_RE.search(col.get("label", ""))
    )
    return with_year / len(columns)


def _score_empty_label_ratio(stmt: dict) -> float:
    """
    1.0 if blank labels (empty or whitespace-only) are <= 5% of rows,
    0.0 otherwise.
    Returns 1.0 if there are no rows.
    """
    rows = stmt.get("rows", [])
    if not rows:
        return 1.0

    blank_count = sum(
        1 for row in rows if not row.get("label_raw", "").strip()
    )
    ratio = blank_count / len(rows)
    return 1.0 if ratio <= 0.05 else 0.0


def _score_leaked_headers(stmt: dict) -> float:
    """
    1.0 if no rows have a blank label where all values look like
    years or unit-strings (leaked header rows), 0.0 if any are found.
    """
    rows = stmt.get("rows", [])

    for row in rows:
        label = row.get("label_raw", "")
        if label.strip():
            # Non-blank label — cannot be a leaked header
            continue

        values = row.get("values", [])
        if not values:
            continue

        # Check if ALL values look like years or unit strings
        all_look_like_headers = all(
            _LEAKED_VALUE_RE.match((v.get("raw") or "").strip())
            for v in values
            if (v.get("raw") or "").strip()
        )

        # Only flag if there's at least one non-empty value that looks like a header
        non_empty_values = [v for v in values if (v.get("raw") or "").strip()]
        if non_empty_values and all_look_like_headers:
            return 0.0

    return 1.0


# ---------------------------------------------------------------------------
# Row flagging
# ---------------------------------------------------------------------------

def flag_rows(stmt: dict) -> Set[int]:
    """
    Return a set of row_index values for rows needing review.

    A row is flagged if any of the following apply:
    - label_raw is blank (empty or whitespace-only)
    - row_index appears in validation warnings
    - section is "other"
    - Any value has normalized=None but raw is non-empty (parse failure)
    - Label contains "total" (case insensitive) but row_type is "line_item"
    """
    rows = stmt.get("rows", [])
    warnings = stmt.get("validation", {}).get("warnings", [])
    warned_indices = {w["row_index"] for w in warnings}

    flagged: Set[int] = set()

    for row in rows:
        idx = row["row_index"]

        # Blank label
        if not row.get("label_raw", "").strip():
            flagged.add(idx)
            continue

        # In validation warnings
        if idx in warned_indices:
            flagged.add(idx)
            continue

        # Section is "other" AND it's a line_item with a value (not section headers)
        # Don't flag entire OCI sections just because they're classified as "other"
        if row.get("section") == "other" and row.get("row_type") == "line_item":
            vals = row.get("values", [])
            has_value = any(v.get("normalized") is not None for v in vals)
            if not has_value:
                flagged.add(idx)
                continue

        # Parse failure: normalized is None but raw is non-empty
        for val in row.get("values", []):
            if val.get("normalized") is None and (val.get("raw") or "").strip() and not val.get("is_null", False):
                flagged.add(idx)
                break

        if idx in flagged:
            continue

        # Label contains "total" but row_type is "line_item"
        label = row.get("label_raw", "")
        if "total" in label.lower() and row.get("row_type") == "line_item":
            flagged.add(idx)

    return flagged


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def _classify_level(score: float) -> str:
    """Map a 0.0-1.0 score to a confidence level string."""
    if score >= THRESHOLDS["high"]:
        return "high"
    if score >= THRESHOLDS["medium"]:
        return "medium"
    return "low"


def score_statement(stmt: dict, statement_type: str) -> dict:
    """
    Compute a composite confidence score for an extracted statement.

    Parameters
    ----------
    stmt : dict
        The statement dict in v1.2 shape.
    statement_type : str
        One of "balance_sheet", "income_statement", "cash_flow".

    Returns
    -------
    dict with keys:
        score       : float  — composite score in [0.0, 1.0]
        level       : str    — "high", "medium", or "low"
        signals     : dict   — individual signal scores keyed by signal name
        flagged_rows: list   — sorted list of flagged row_index values
    """
    signals = {
        "subtotal_validation": _score_subtotal_validation(stmt),
        "section_coverage": _score_section_coverage(stmt, statement_type),
        "row_count": _score_row_count(stmt, statement_type),
        "column_dates": _score_column_dates(stmt),
        "empty_label_ratio": _score_empty_label_ratio(stmt),
        "leaked_headers": _score_leaked_headers(stmt),
    }

    total_weight = sum(WEIGHTS.values())
    composite = sum(signals[k] * WEIGHTS[k] for k in WEIGHTS) / total_weight

    return {
        "score": composite,
        "level": _classify_level(composite),
        "signals": signals,
        "flagged_rows": sorted(flag_rows(stmt)),
    }
