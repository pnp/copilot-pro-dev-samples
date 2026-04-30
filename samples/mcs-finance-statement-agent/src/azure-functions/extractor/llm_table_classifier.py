"""
LLM-based table classifier for financial statement extraction.

Replaces hardcoded heading patterns and content label matching with a single
LLM call that classifies all tables in the document markdown.

Public API:
    classify_tables(markdown) -> list[TableClassification]
"""
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Azure OpenAI client (reuses same pattern as llm_reconciler)
# ---------------------------------------------------------------------------

_client: Optional[AzureOpenAI] = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        api_ver = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
        if not endpoint:
            raise EnvironmentError("AZURE_OPENAI_ENDPOINT must be set.")
        api_key = os.environ.get("AZURE_OPENAI_KEY")
        if api_key:
            _client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_ver,
            )
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            _client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version=api_ver,
            )
    return _client


_DEPLOYMENT = lambda: os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TableClassification:
    """Classification result for a single table in the document."""
    table_index: int
    md_offset: int           # Absolute offset of <table> in markdown
    md_end_offset: int       # Absolute offset of </table> end
    statement_type: str      # "balance_sheet", "income_statement", "cash_flow", "other"
    confidence: float        # 0.0 - 1.0
    is_consolidated: bool
    reasoning: str           # Brief explanation from LLM


# ---------------------------------------------------------------------------
# Table extraction helpers
# ---------------------------------------------------------------------------

def _extract_table_summaries(markdown: str, max_rows: int = 8) -> list[dict]:
    """Extract a summary of each table in the markdown for LLM classification.

    Returns list of dicts with: index, offset, end_offset, header_context, first_rows.
    """
    tables = []
    search_start = 0

    while True:
        table_start = markdown.find("<table>", search_start)
        if table_start < 0:
            break
        table_end = markdown.find("</table>", table_start)
        if table_end < 0:
            break
        table_end += len("</table>")

        table_html = markdown[table_start:min(table_end, table_start + 8000)]

        # Extract header context (text before the table, e.g., headings/captions)
        context_start = max(0, table_start - 300)
        header_context = markdown[context_start:table_start]
        # Clean to just text
        header_context = re.sub(r"<[^>]+>", " ", header_context)
        header_context = re.sub(r"\s+", " ", header_context).strip()[-200:]

        # Extract first N rows of cell content
        rows_html = re.findall(r"<tr>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)
        row_texts = []
        for row_html in rows_html[:max_rows]:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.DOTALL | re.IGNORECASE)
            cell_texts = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            row_texts.append(cell_texts)

        # Count total rows (for size context)
        total_rows = len(rows_html)

        tables.append({
            "index": len(tables),
            "offset": table_start,
            "end_offset": table_end,
            "header_context": header_context,
            "first_rows": row_texts,
            "total_rows": total_rows,
        })

        search_start = table_end

    return tables


def _build_classification_prompt(table_summaries: list[dict]) -> str:
    """Build the LLM prompt for table classification."""
    table_descriptions = []

    for t in table_summaries:
        rows_display = []
        for row in t["first_rows"]:
            rows_display.append(" | ".join(row))

        desc = (
            f"--- Table {t['index']} ({t['total_rows']} rows) ---\n"
            f"Context before table: {t['header_context'][:200]}\n"
            f"First rows:\n" + "\n".join(rows_display)
        )
        table_descriptions.append(desc)

    tables_text = "\n\n".join(table_descriptions)

    return f"""You are a financial statement classifier. Given the following tables extracted from a financial report PDF, classify each table.

For each table, determine:
1. **statement_type**: One of "balance_sheet", "income_statement", "cash_flow", or "other"
2. **confidence**: 0.0 to 1.0 how confident you are
3. **is_consolidated**: true if this is a consolidated (group) statement, false if parent/standalone
4. **reasoning**: One sentence explaining why

Classification rules:
- **balance_sheet**: Contains assets, liabilities, equity. Has "total assets" or equivalent.
- **income_statement**: Contains revenue/sales, expenses, profit/loss. Shows profitability over a period. Includes: profit & loss, statement of comprehensive income (if it contains revenue).
- **cash_flow**: Contains operating/investing/financing cash flows. Shows cash movements.
- **other**: Notes, summaries, segment data, OCI-only statements without revenue, parent company statements, or any non-primary financial statement.

Important:
- Prefer CONSOLIDATED statements over parent company statements.
- If a table is a parent company statement (母公司, parent company, individuel), classify as "other".
- A "Statement of Comprehensive Income" that contains revenue IS an income_statement.
- A "Statement of Comprehensive Income" with ONLY hedging/translation items is "other".
- Tables with very few rows (< 5) that look like summary/index tables are "other".

Tables:
{tables_text}

Respond with a JSON object: {{"tables": [...]}} where each element has: table_index (int), statement_type (string), confidence (float), is_consolidated (bool), reasoning (string)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_tables(markdown: str) -> list[TableClassification]:
    """Classify all tables in the document markdown using LLM.

    Returns a list of TableClassification objects, one per table found.
    """
    table_summaries = _extract_table_summaries(markdown)

    if not table_summaries:
        logging.info("[LLM Classifier] No tables found in markdown")
        return []

    logging.info(f"[LLM Classifier] Classifying {len(table_summaries)} tables...")

    prompt = _build_classification_prompt(table_summaries)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        # Handle both {"tables": [...]} and bare [...] formats
        if isinstance(parsed, list):
            classifications_raw = parsed
        elif isinstance(parsed, dict):
            classifications_raw = parsed.get("tables", parsed.get("classifications", []))
        else:
            classifications_raw = []

    except Exception as e:
        logging.warning(f"[LLM Classifier] LLM call failed: {e}")
        return []

    # Build offset lookup
    offset_map = {t["index"]: t for t in table_summaries}

    results = []
    for item in classifications_raw:
        idx = item.get("table_index", -1)
        t = offset_map.get(idx)
        if not t:
            continue

        results.append(TableClassification(
            table_index=idx,
            md_offset=t["offset"],
            md_end_offset=t["end_offset"],
            statement_type=item.get("statement_type", "other"),
            confidence=float(item.get("confidence", 0.0)),
            is_consolidated=bool(item.get("is_consolidated", False)),
            reasoning=item.get("reasoning", ""),
        ))

    # Log results
    for r in results:
        if r.statement_type != "other":
            logging.info(
                f"[LLM Classifier] Table {r.table_index}: {r.statement_type} "
                f"(confidence={r.confidence:.2f}, consolidated={r.is_consolidated}) "
                f"— {r.reasoning}"
            )

    return results


def get_best_table(
    classifications: list[TableClassification],
    statement_type: str,
    min_confidence: float = 0.5,
) -> Optional[TableClassification]:
    """Get the best classified table for a given statement type.

    Prefers consolidated over non-consolidated, then highest confidence.
    """
    matches = [
        c for c in classifications
        if c.statement_type == statement_type and c.confidence >= min_confidence
    ]

    if not matches:
        return None

    # Sort: consolidated first, then by confidence descending
    matches.sort(key=lambda c: (c.is_consolidated, c.confidence), reverse=True)
    return matches[0]
