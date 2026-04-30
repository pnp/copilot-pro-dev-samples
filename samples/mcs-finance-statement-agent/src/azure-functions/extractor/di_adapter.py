"""
extractor/di_adapter.py
------------------------
Adapter for Azure Document Intelligence results → pipeline AnalyzeResult.

Unlike Textract/pdfplumber adapters, DI with output_content_format="markdown"
already returns markdown with embedded HTML tables.  This adapter only needs to:
  1. Build a page_map from the DI page spans
  2. Classify statements via LLM (reuses the same prompt as textract_adapter)

Public API:
    build_page_map(di_result, markdown) -> list[tuple[int, int, int]]
    classify_statements_with_llm(markdown) -> list[dict]
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Build page map
# ---------------------------------------------------------------------------

def build_page_map(
    di_result: dict, markdown: str
) -> list[tuple[int, int, int]]:
    """
    Build a page_map from DI page spans.

    DI pages include span offsets into the markdown content string,
    so we can directly map (offset, offset+length, page_number).

    Falls back to parsing <!-- PageHeader --> or <!-- PageBreak --> markers
    if page spans are not available.
    """
    pages = di_result.get("pages", [])
    entries: list[tuple[int, int, int]] = []

    for page in pages:
        page_num = page.get("pageNumber", 1)
        spans = page.get("spans", [])
        if spans:
            # Use the first span's offset and the last span's end
            start = spans[0]["offset"]
            last = spans[-1]
            end = last["offset"] + last["length"]
            entries.append((start, end, page_num))

    if entries:
        entries.sort(key=lambda t: t[0])
        return entries

    # Fallback: look for page markers in markdown (DI sometimes inserts these)
    marker_re = re.compile(r"<!-- PageBreak -->|<!-- PAGE (\d+) -->")
    matches = list(marker_re.finditer(markdown))

    if not matches:
        # Single page document — entire content is page 1
        return [(0, len(markdown), 1)]

    page_num = 1
    for i, m in enumerate(matches):
        if m.group(1):
            page_num = int(m.group(1))
        start = m.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(markdown)
        entries.append((start, end, page_num))
        page_num += 1

    entries.sort(key=lambda t: t[0])
    return entries


# ---------------------------------------------------------------------------
# 2. Classify statements with LLM (same as textract_adapter)
# ---------------------------------------------------------------------------

def classify_statements_with_llm(markdown: str) -> list[dict]:
    """
    Use Azure OpenAI to classify financial statements in the document.

    Sends first 8000 chars of markdown to the LLM and asks it to identify
    statement types (balance_sheet, income_statement, cash_flow).

    Returns empty list if LLM is not available (graceful fallback).
    """
    try:
        from extractor.llm_reconciler import _get_client, _DEPLOYMENT
    except Exception:
        logger.warning(
            "[di_adapter] Could not import LLM client, skipping classification"
        )
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
                {
                    "role": "system",
                    "content": "You are a financial document analyst. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("[di_adapter] LLM returned empty content")
            return []
        raw = content.strip()
        parsed = json.loads(raw)

        if isinstance(parsed, dict):
            return parsed.get("statements", [])
        elif isinstance(parsed, list):
            return parsed
        return []

    except Exception as e:
        logger.warning(f"[di_adapter] LLM classification failed: {e}")
        return []
