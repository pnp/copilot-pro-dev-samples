"""
extractor/html_table_parser.py
-------------------------------
Parses HTML tables from the prebuilt-documentAnalyzer markdown output
into structured rows, columns, and cells.

The prebuilt-documentAnalyzer returns financial tables as clean HTML:
  <table>
    <tr><th colspan="2">Three Months Ended</th>...</tr>
    <tr><th>2025</th><th>2024</th>...</tr>
    <tr><td>Revenue</td><td>$ 59,893</td>...</tr>
  </table>

This is dramatically cleaner than the \n\n-separated plain text from
prebuilt-read — no currency splitting, no column alignment issues,
no continuation fragments.
"""

import re
from typing import Optional


def _strip_tags(html: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    return text.strip()


def _parse_financial_value(raw: str) -> Optional[float]:
    """Parse a financial value string to float."""
    s = raw.strip()
    if not s:
        return None
    s = re.sub(r"^[\$\u00a5\u20ac\u00a3]\s*", "", s)
    if not s:
        return None
    if re.match(r"^[\u2014\-\uff0d]+$", s):  # dashes = zero
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "")
    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Currency and unit extraction from column headers
# ---------------------------------------------------------------------------

# Patterns for extracting currency + unit from column header text.
# Examples: "£000", "$'000", "€M", "¥百万", "RMB'000", "US$ millions"
_CURRENCY_UNIT_PATTERNS = [
    # Symbol + multiplier: "£000", "$'000", "€000", "¥千元"
    (re.compile(r"^[\$£€¥]\s*[''']?\s*000\s*$"), {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}, "thousands"),
    (re.compile(r"^[\$£€¥]\s*[''']?\s*M\s*$", re.IGNORECASE), {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}, "millions"),
    (re.compile(r"^[\$£€¥]\s*[''']?\s*000[''']?\s*000\s*$"), {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}, "millions"),
    # ISO code + multiplier: "RMB'000", "USD'000", "GBP millions"
    (re.compile(r"^(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)\s*[''']?\s*000\s*$", re.IGNORECASE), None, "thousands"),
    (re.compile(r"^(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)\s*millions?\s*$", re.IGNORECASE), None, "millions"),
    (re.compile(r"^(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)\s*thousands?\s*$", re.IGNORECASE), None, "thousands"),
    (re.compile(r"^(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)\s*billions?\s*$", re.IGNORECASE), None, "billions"),
]

# Currency symbol to ISO code mapping
_SYMBOL_TO_ISO = {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}

# Standalone currency patterns (just the symbol or code, no unit)
_CURRENCY_ONLY_PATTERNS = [
    re.compile(r"^[\$£€¥]$"),
    re.compile(r"^(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)$", re.IGNORECASE),
]

# Unit patterns from parenthetical notes: "(In millions)", "(In thousands)"
_PAREN_UNIT_RE = re.compile(
    r"\(\s*(?:in\s+)?(millions?|thousands?|billions?|百万|千|万)\s*\)",
    re.IGNORECASE,
)

# ISO code normalization
_ISO_NORMALIZE = {
    "RMB": "CNY",
}


def extract_currency_and_unit(
    header_rows: list[list[str]],
    all_text: str = "",
) -> dict:
    """
    Extract currency code and unit multiplier from table column headers
    and surrounding text.

    Returns {"currency": str|None, "unit": str|None, "currency_symbol": str|None}.

    Examines:
      1. Column header cells (e.g. "£000", "RMB'000", "$M")
      2. Parenthetical notes in header rows (e.g. "(In millions)")
      3. Currency symbols appearing in data cells
    """
    currency = None
    unit = None
    currency_symbol = None

    # Flatten all header cell text for scanning
    all_header_text = " ".join(
        cell for row in header_rows for cell in row if cell.strip()
    )

    # Strategy 1: Match column header cells against known patterns
    for row in header_rows:
        for cell in row:
            cell_stripped = cell.strip()
            if not cell_stripped:
                continue
            for pattern, symbol_map, unit_value in _CURRENCY_UNIT_PATTERNS:
                m = pattern.match(cell_stripped)
                if m:
                    unit = unit_value
                    if symbol_map:
                        # Pattern uses symbol — extract from first char
                        sym = cell_stripped[0]
                        currency = symbol_map.get(sym)
                        currency_symbol = sym
                    else:
                        # Pattern captured ISO code
                        iso = m.group(1).upper()
                        currency = _ISO_NORMALIZE.get(iso, iso)
                        currency_symbol = _currency_code_to_symbol(currency)
                    break
            if currency and unit:
                break
        if currency and unit:
            break

    # Strategy 2: Parenthetical unit in headers "(In millions)"
    if not unit:
        m = _PAREN_UNIT_RE.search(all_header_text)
        if not m:
            m = _PAREN_UNIT_RE.search(all_text[:2000])
        if m:
            raw_unit = m.group(1).lower()
            if "million" in raw_unit or "百万" in raw_unit:
                unit = "millions"
            elif "thousand" in raw_unit or "千" in raw_unit:
                unit = "thousands"
            elif "billion" in raw_unit:
                unit = "billions"
            elif "万" in raw_unit:
                unit = "ten_thousands"

    # Strategy 3: Currency symbol in header text
    if not currency:
        for sym, iso in _SYMBOL_TO_ISO.items():
            if sym in all_header_text:
                currency = iso
                currency_symbol = sym
                break

    # Strategy 4: ISO code in header text
    if not currency:
        iso_m = re.search(
            r"\b(USD|GBP|EUR|JPY|CNY|RMB|HKD|SGD|AUD|CHF)\b",
            all_header_text, re.IGNORECASE,
        )
        if iso_m:
            iso = iso_m.group(1).upper()
            currency = _ISO_NORMALIZE.get(iso, iso)
            currency_symbol = _currency_code_to_symbol(currency)

    return {
        "currency": currency,
        "unit": unit,
        "currency_symbol": currency_symbol,
    }


def _currency_code_to_symbol(code: str) -> str | None:
    """Map ISO 4217 code to display symbol."""
    return {
        "USD": "$", "GBP": "£", "EUR": "€",
        "JPY": "¥", "CNY": "¥",
    }.get(code)


# ---------------------------------------------------------------------------
# Table parsing
# ---------------------------------------------------------------------------

def _parse_single_table(
    table_html: str,
) -> tuple[list[list[str]], list[list[str]]]:
    """
    Parse a single <table> block into header_rows and data_rows.

    Returns (header_rows, data_rows) where each is a list of cell-value lists.
    """
    tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<(td|th)[^>]*>(.*?)</(?:td|th)>", re.DOTALL | re.IGNORECASE)
    colspan_pattern = re.compile(r'colspan="?(\d+)"?', re.IGNORECASE)
    tag_start_pattern = re.compile(r"<(td|th)[^>]*>", re.IGNORECASE)

    header_rows: list[list[str]] = []
    data_rows: list[list[str]] = []

    for tr_content in tr_pattern.findall(table_html):
        cells_in_row = td_pattern.findall(tr_content)
        is_header = any(tag.lower() == "th" for tag, _ in cells_in_row)

        row_values = []
        # We need to iterate through tag matches to get colspan from the
        # opening tag, not from the overall tr_content.
        tag_starts = list(tag_start_pattern.finditer(tr_content))
        cell_matches = list(td_pattern.finditer(tr_content))

        for ci, cell_m in enumerate(cell_matches):
            text = _strip_tags(cell_m.group(2))
            # Get colspan from the corresponding opening tag
            opening_tag = tag_starts[ci].group(0) if ci < len(tag_starts) else ""
            colspan_m = colspan_pattern.search(opening_tag)
            span = int(colspan_m.group(1)) if colspan_m else 1
            row_values.append(text)
            for _ in range(span - 1):
                row_values.append("")

        if is_header:
            header_rows.append(row_values)
        else:
            data_rows.append(row_values)

    return header_rows, data_rows


def parse_html_table(
    markdown: str,
    start_offset: int,
    end_offset: int,
) -> tuple[list[str], list[str], list[dict]]:
    """
    Parse HTML <table>(s) in the given markdown range.

    When multiple tables are present (page-break continuations), the FIRST
    table's headers are used for column identification.  Subsequent tables'
    header rows are discarded (they're repeated page headers), and their
    data rows are appended.

    Returns (rows, columns, cells) where:
      - rows: list of label strings (one per data row)
      - columns: list of column header strings
      - cells: list of cell dicts compatible with the existing pipeline

    Also populates cells[*]["_table_currency_unit"] on the first cell with
    extracted currency/unit metadata from column headers.
    """
    section = markdown[start_offset:end_offset]

    # Find individual <table>...</table> blocks
    table_matches = re.findall(
        r"<table>(.*?)</table>", section, re.DOTALL | re.IGNORECASE
    )
    if not table_matches:
        return [], [], []

    # Parse each table separately — use first table's headers, merge data rows
    primary_header_rows: list[list[str]] = []
    all_data_rows: list[list[str]] = []

    for idx, table_html in enumerate(table_matches):
        header_rows, data_rows = _parse_single_table(table_html)
        if idx == 0:
            # First table: keep its headers as the canonical column definitions
            primary_header_rows = header_rows
        # Append all data rows from every table
        all_data_rows.extend(data_rows)

    # Build column headers from the primary (first) table's headers.
    # When multiple header rows exist, prefer the one with year labels
    # (e.g. "2025", "2024") over a unit-only row (e.g. "£000", "£000").
    # Financial tables often have two header rows:
    #   <th>2025</th><th>2024</th>       ← year row (best for column labels)
    #   <th>£000</th><th>£000</th>       ← unit row (used for currency/unit)
    _YEAR_RE = re.compile(r"\b20\d{2}\b")
    _UNIT_ONLY_RE = re.compile(
        r"^[\$£€¥]\s*[''']?\s*\d*\s*$"   # "£000", "$M", "€"
        r"|^(USD|GBP|EUR|JPY|CNY|RMB).*$",  # "RMB'000"
        re.IGNORECASE,
    )

    columns: list[str] = []
    if primary_header_rows:
        # Find the best header row: prefer one with year labels
        best_header = primary_header_rows[-1]  # default: last row
        for hrow in primary_header_rows:
            non_empty = [h for h in hrow if h.strip()]
            if any(_YEAR_RE.search(h) for h in non_empty):
                best_header = hrow
                break

        if best_header and not best_header[0].strip():
            columns = [h for h in best_header[1:] if h.strip()]
        else:
            columns = [h for h in best_header if h.strip()]

    # Extract currency and unit from the column headers
    currency_unit = extract_currency_and_unit(
        primary_header_rows, section[:2000]
    )

    # Build rows and cells from data rows
    rows: list[str] = []
    cells: list[dict] = []
    num_cols = len(columns) if columns else 0

    for data_row in all_data_rows:
        if not data_row:
            continue

        label = data_row[0] if data_row else ""
        label = label or ""  # guard against None
        values = data_row[1:] if len(data_row) > 1 else []
        values = [v or "" for v in values]  # guard against None values

        # Skip rows that look like repeated table headers leaked into data
        # (e.g. a row where all values are year strings "2025", "2024" or
        # unit strings "£000", "$M").
        if label.strip() == "" and values:
            all_header_like = all(
                re.match(r"^\d{4}$", v.strip())
                or re.match(r"^[\$£€¥]\s*[''']?\s*\d*$", v.strip())
                or v.strip() == ""
                for v in values
            )
            if all_header_like and any(v.strip() for v in values):
                continue

        # Determine row_type
        label_lower = label.lower().strip()
        has_values = any(v.strip() for v in values)

        if not has_values and label.strip():
            row_type = "section_header"
        elif label_lower.startswith("total "):
            row_type = "total" if any(
                kw in label_lower for kw in
                ["total assets", "total liabilities and", "total revenue"]
            ) else "subtotal"
        elif label_lower.startswith("net cash") or label_lower.startswith("net increase") or label_lower.startswith("net decrease"):
            row_type = "subtotal"
        else:
            row_type = "line_item"

        row_index = len(rows)
        rows.append(label)

        # Label cell
        cells.append({
            "row": row_index, "col": 0, "content": label,
            "kind": "content", "row_type": row_type, "indent_level": 0,
        })

        # Value cells — always emit num_cols cells
        for col_idx in range(num_cols):
            raw = values[col_idx].strip() if col_idx < len(values) else ""
            cells.append({
                "row": row_index, "col": col_idx + 1,
                "content": raw if raw else "",
                "kind": "content", "row_type": row_type, "indent_level": 0,
            })

    # Post-pass: set indent_level for items between section_header and subtotal
    in_section = False
    for c in cells:
        if c["col"] != 0:
            continue
        if c["row_type"] == "section_header":
            in_section = True
        elif c["row_type"] in ("subtotal", "total"):
            in_section = False
        elif c["row_type"] == "line_item" and in_section:
            c["indent_level"] = 1
            for vc in cells:
                if vc["row"] == c["row"] and vc["col"] > 0:
                    vc["indent_level"] = 1

    # Attach currency/unit metadata so callers can use it
    if cells:
        cells[0]["_currency_unit"] = currency_unit

    return rows, columns, cells
