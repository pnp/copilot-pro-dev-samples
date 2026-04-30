"""
extractor/pdfplumber_adapter.py
-------------------------------
Converts pdfplumber extraction output into the AnalyzeResult-compatible format
that the existing pipeline (Stages 2-5) expects.

Key responsibilities:
  - Convert pdfplumber tables to HTML <table> strings
  - Reconstruct markdown with page text + embedded HTML tables
  - Build page_map from page markers
  - Classify statements via LLM (same as Textract adapter)
"""
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _table_to_html(table: list[list[str | None]]) -> str:
    """Convert a pdfplumber table (list of rows, each a list of cell values) to HTML.

    First row is treated as header (<th>) if it looks like a header row.
    All other rows use <td>.
    Newlines within cell values are replaced with spaces.
    """
    if not table or not table[0]:
        return ""

    rows_html = []
    for row_idx, row in enumerate(table):
        cells_html = []
        for cell in row:
            text = (cell or "").replace("\n", " ").strip()
            # First row gets <th> tags
            tag = "th" if row_idx == 0 else "td"
            cells_html.append(f"<{tag}>{text}</{tag}>")
        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

    return f"<table>{''.join(rows_html)}</table>"


def reconstruct_markdown(pdfplumber_result: dict) -> str:
    """Build markdown with embedded HTML tables from pdfplumber output.

    For each page:
      1. Insert <!-- PAGE N --> marker
      2. Add page text lines (excluding text that appears in tables)
      3. Add each table as <table> HTML

    The extract stage's heading search works on this text,
    and html_table_parser.py parses the <table> blocks.
    """
    parts = []

    for page_data in pdfplumber_result["pages"]:
        page_num = page_data["page_number"]
        text = page_data["text"]
        tables = page_data["tables"]

        # Page marker for page_map
        parts.append(f"<!-- PAGE {page_num} -->")

        # Add page text (preserves headings for the heading search in extract.py)
        if text:
            parts.append(f"\n{text}\n")

        # Add each table as HTML
        for table in tables:
            html = _table_to_html(table)
            if html:
                parts.append(f"\n\n{html}\n\n")

    return "".join(parts)


def build_page_map(
    pdfplumber_result: dict,
    markdown: str,
) -> list[tuple[int, int, int]]:
    """Build pipeline-compatible page_map from <!-- PAGE N --> markers."""
    page_map = []
    markers = list(re.finditer(r"<!-- PAGE (\d+) -->", markdown))

    for i, match in enumerate(markers):
        page_num = int(match.group(1))
        start = match.start()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(markdown)
        page_map.append((start, end, page_num))

    return page_map


def classify_statements_with_llm(markdown: str) -> list[dict]:
    """Use Azure OpenAI to classify financial statements in the document.

    Same approach as textract_adapter.classify_statements_with_llm.
    Returns empty list if LLM is not available (graceful fallback).
    """
    # Lazy imports to avoid circular imports and env var issues at module level
    try:
        from extractor.llm_reconciler import _get_client, _DEPLOYMENT
    except Exception:
        logger.warning("[pdfplumber_adapter] Could not import LLM client, skipping classification")
        return []

    snippet = markdown[:8000]

    prompt = f"""You are a financial document analyst. Given the following extracted text from a financial report, identify each financial statement present.

For each statement found, return:
- statement_type: one of "balance_sheet", "income_statement", "cash_flow"
- title_raw: the exact title as it appears in the document
- currency: ISO 4217 currency code (e.g. "USD", "EUR", "GBP", "CNY")
- unit: the unit of values (e.g. "millions", "thousands", "ones")
- accounting_standard: e.g. "IFRS", "US_GAAP", "Chinese_ASBE", "Japanese_GAAP", or null
- is_consolidated: true if consolidated/group statement, false if standalone
- report_language: ISO 639-1 language code (e.g. "en", "fr", "zh")
- company_name: name of the reporting entity (in English)

If you cannot determine a field, use null.

Document text:
{snippet}

Respond with a JSON object: {{"statements": [...]}}"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial document analyst. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        if isinstance(parsed, dict):
            return parsed.get("statements", [])
        elif isinstance(parsed, list):
            return parsed
        return []

    except Exception as e:
        logger.warning(f"[pdfplumber_adapter] LLM classification failed: {e}")
        return []
