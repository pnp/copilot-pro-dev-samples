"""
extractor/textract_adapter.py
------------------------------
Converts AWS Textract JSON blocks into the markdown + page_map format
expected by the existing extraction pipeline (Stages 2-5).

The key idea: reconstruct markdown text with embedded HTML <table> tags from
Textract blocks, so all existing heading search, table parsing, and enrichment
logic in html_table_parser.py and the extract stage works unchanged.

Public API:
    reconstruct_markdown(blocks) -> str
    build_page_map(blocks, markdown) -> list[tuple[int, int, int]]
    classify_statements_with_llm(markdown) -> list[dict]

Internal helpers (exposed for testing):
    _build_block_index(blocks) -> dict[str, dict]
    _table_to_html(table_block, index) -> str
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Block index
# ---------------------------------------------------------------------------

def _build_block_index(blocks: list[dict]) -> dict[str, dict]:
    """Build a lookup dict from Block Id -> Block for fast traversal."""
    return {block["Id"]: block for block in blocks}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_child_ids(block: dict, relationship_type: str = "CHILD") -> list[str]:
    """
    Get child IDs from a block's Relationships array for the given type.

    Args:
        block: A Textract block dict.
        relationship_type: The relationship type to look for (e.g. "CHILD").

    Returns:
        List of block IDs, or empty list if no matching relationship.
    """
    for rel in block.get("Relationships", []):
        if rel.get("Type") == relationship_type:
            return rel.get("Ids", [])
    return []


def _get_cell_text(cell_block: dict, index: dict[str, dict]) -> str:
    """
    Get the text content of a CELL block by traversing CELL -> CHILD -> WORD.

    Joins Word.Text values with spaces.
    """
    word_ids = _get_child_ids(cell_block, "CHILD")
    words = []
    for wid in word_ids:
        word_block = index.get(wid)
        if word_block and word_block.get("BlockType") == "WORD":
            words.append(word_block.get("Text", ""))
    return " ".join(words)


# ---------------------------------------------------------------------------
# 2. Table to HTML
# ---------------------------------------------------------------------------

def _table_to_html(table_block: dict, index: dict[str, dict]) -> str:
    """
    Convert a Textract TABLE block into an HTML <table> string.

    - Gets CELL children from the TABLE block's CHILD relationship
    - Groups cells by RowIndex (1-based)
    - Sorts cells within each row by ColumnIndex
    - Gets cell text by traversing CELL -> WORD children
    - Uses <th> for cells with COLUMN_HEADER entity type, <td> otherwise
    - Handles colspan/rowspan attributes when > 1
    """
    cell_ids = _get_child_ids(table_block, "CHILD")

    # Group cells by row
    rows: dict[int, list[dict]] = defaultdict(list)
    for cell_id in cell_ids:
        cell = index.get(cell_id)
        if cell and cell.get("BlockType") == "CELL":
            row_idx = cell.get("RowIndex", 1)
            rows[row_idx].append(cell)

    # Build HTML
    html_parts = ["<table>"]

    for row_num in sorted(rows.keys()):
        cells = sorted(rows[row_num], key=lambda c: c.get("ColumnIndex", 1))
        html_parts.append("<tr>")

        for cell in cells:
            text = _get_cell_text(cell, index)
            entity_types = cell.get("EntityTypes", [])
            is_header = "COLUMN_HEADER" in entity_types

            tag = "th" if is_header else "td"

            # Build attributes for colspan/rowspan
            attrs = ""
            col_span = cell.get("ColumnSpan", 1)
            row_span = cell.get("RowSpan", 1)
            if col_span > 1:
                attrs += f' colspan="{col_span}"'
            if row_span > 1:
                attrs += f' rowspan="{row_span}"'

            html_parts.append(f"<{tag}{attrs}>{text}</{tag}>")

        html_parts.append("</tr>")

    html_parts.append("</table>")
    return "".join(html_parts)


# ---------------------------------------------------------------------------
# 3. Reconstruct markdown
# ---------------------------------------------------------------------------

def reconstruct_markdown(blocks: list[dict]) -> str:
    """
    Build a markdown-like document from Textract blocks.

    - Collects LINE blocks (text) and TABLE blocks (convert to HTML)
    - Sorts by page number, then by vertical position (BoundingBox.Top)
    - Inserts <!-- PAGE N --> markers at page boundaries
    - LINE blocks become \\n{text}
    - TABLE blocks become \\n\\n{html}\\n\\n

    The output mimics what Azure Content Understanding produces, so all
    existing heading search, table parsing, and enrichment logic works.
    """
    index = _build_block_index(blocks)

    # Collect renderable elements: LINEs and TABLEs
    elements: list[tuple[int, float, str, str]] = []
    # Each element: (page, top_position, block_type, content)

    for block in blocks:
        block_type = block.get("BlockType")
        page = block.get("Page", 1)
        top = block.get("Geometry", {}).get("BoundingBox", {}).get("Top", 0.0)

        if block_type == "LINE":
            text = block.get("Text", "")
            elements.append((page, top, "LINE", text))
        elif block_type == "TABLE":
            html = _table_to_html(block, index)
            elements.append((page, top, "TABLE", html))

    # Sort by page, then vertical position
    elements.sort(key=lambda e: (e[0], e[1]))

    # Build markdown with page markers
    parts: list[str] = []
    current_page = 0

    for page, top, block_type, content in elements:
        if page != current_page:
            current_page = page
            parts.append(f"<!-- PAGE {page} -->")

        if block_type == "LINE":
            parts.append(f"\n{content}")
        elif block_type == "TABLE":
            parts.append(f"\n\n{content}\n\n")

    return "".join(parts)


# ---------------------------------------------------------------------------
# 4. Build page map
# ---------------------------------------------------------------------------

def build_page_map(
    blocks: list[dict], markdown: str
) -> list[tuple[int, int, int]]:
    """
    Build a page_map compatible with the existing pipeline.

    Finds <!-- PAGE N --> markers in the markdown and returns a list of
    (start_offset, end_offset, page_number) tuples sorted by offset.
    Each entry covers from one marker to the next (or end of string).
    """
    marker_re = re.compile(r"<!-- PAGE (\d+) -->")
    entries: list[tuple[int, int, int]] = []

    matches = list(marker_re.finditer(markdown))
    for i, m in enumerate(matches):
        page_num = int(m.group(1))
        start = m.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(markdown)
        entries.append((start, end, page_num))

    entries.sort(key=lambda t: t[0])
    return entries


# ---------------------------------------------------------------------------
# 5. Classify statements with LLM
# ---------------------------------------------------------------------------

def classify_statements_with_llm(markdown: str) -> list[dict]:
    """
    Use Azure OpenAI to classify financial statements in the document.

    Sends first 8000 chars of markdown to the LLM and asks it to identify
    statement types (balance_sheet, income_statement, cash_flow).

    For each, returns: statement_type, title_raw, currency (ISO 4217), unit,
    accounting_standard, is_consolidated, report_language, company_name.

    Returns empty list if LLM is not available (graceful fallback).
    """
    # Lazy imports to avoid circular imports and env var issues at module level
    try:
        from extractor.llm_reconciler import _get_client, _DEPLOYMENT
    except Exception:
        logger.warning("[textract_adapter] Could not import LLM client, skipping classification")
        return []

    snippet = markdown[:8000]

    prompt = f"""You are a financial document analyst. Given the following extracted text from a financial report, identify each financial statement present.

For each statement found, return:
- statement_type: one of "balance_sheet", "income_statement", "cash_flow"
- title_raw: the exact title as it appears in the document
- currency: ISO 4217 currency code (e.g. "USD", "EUR", "GBP")
- unit: the unit of values (e.g. "millions", "thousands", "units")
- accounting_standard: e.g. "IFRS", "US GAAP", "GAAP", or null
- is_consolidated: true if consolidated/group statement, false if standalone
- report_language: ISO 639-1 language code (e.g. "en", "fr", "zh")
- company_name: name of the reporting entity

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

        content = response.choices[0].message.content
        if not content:
            logger.warning("[textract_adapter] LLM returned empty content")
            return []
        raw = content.strip()
        parsed = json.loads(raw)

        if isinstance(parsed, dict):
            return parsed.get("statements", [])
        elif isinstance(parsed, list):
            return parsed
        return []

    except Exception as e:
        logger.warning(f"[textract_adapter] LLM classification failed: {e}")
        return []
