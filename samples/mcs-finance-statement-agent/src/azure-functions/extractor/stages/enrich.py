"""
Stage 4: Enrich — translate rows + columns, verify company name, clean labels.

Expanded scope over the current enrichment.py:
  1. Column header translation (e.g. "2025年前三季度 (1-9月)" -> "Q1-Q3 2025 (Jan-Sep)")
  2. Company name verification (cross-check CU Locator vs 编制单位 line in markdown)
  3. Label cleanup (strip parenthetical noise like "(Loss shown as '-')")
  4. Row label translation (existing batch LLM translation, reused via schema_mapper)
"""
import logging
import re
from typing import Optional

from .contracts import (
    CandidateStatement,
    EnrichedStatement,
    EnrichResult,
    ExtractedStatement,
    ExtractResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column header translation
# ---------------------------------------------------------------------------

# Month name lookup
_MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def translate_column_header(raw: str) -> str:
    """Translate a non-English column header to English.

    Returns the translated header, or the original if no pattern matches.
    """
    result = raw.strip()

    # Label column header
    if result == "项目":
        return "Item"

    # Chinese Q1-Q3 period: 2025年前三季度 (1-9月) → Jan-Sep 2025
    result = re.sub(
        r"(\d{4})\s*年\s*前三季度\s*[（(]1-9月[)）]?",
        r"Jan-Sep \1", result,
    )
    # Chinese H1 period: 2025年半年度 (1-6月) → Jan-Jun 2025
    result = re.sub(
        r"(\d{4})\s*年\s*半年度\s*[（(]1-6月[)）]?",
        r"Jan-Jun \1", result,
    )

    # Full date: 2025年9月30日 → Sep 30, 2025 (must be before year-only pattern)
    def _date_repl(m: re.Match) -> str:
        year, month, day = m.group(1), int(m.group(2)), m.group(3)
        mn = _MONTH_NAMES[month] if 1 <= month <= 12 else str(month)
        return f"{mn} {day}, {year}"
    result = re.sub(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", _date_repl, result)

    # Year only: 2025年 / 2025年度 → FY 2025
    result = re.sub(r"(\d{4})\s*年\s*(?:度|年度)?", r"FY \1 ", result)

    # Japanese: 2025年3月期 → Mar 2025
    def _jp_repl(m: re.Match) -> str:
        year, month = m.group(1), int(m.group(2))
        mn = _MONTH_NAMES[month] if 1 <= month <= 12 else str(month)
        return f"{mn} {year}"
    result = re.sub(r"(\d{4})年(\d{1,2})月期", _jp_repl, result)

    # Cleanup pass: fix any remaining partial translations
    # e.g., "FY 20259月30日" → from a mangled earlier run
    def _cleanup_date(m: re.Match) -> str:
        prefix = m.group(1).strip()
        year = m.group(2)
        month = int(m.group(3))
        day = m.group(4)
        mn = _MONTH_NAMES[month] if 1 <= month <= 12 else str(month)
        return f"{mn} {day}, {year}"
    result = re.sub(r"(FY\s+)?(\d{4})\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", _cleanup_date, result)

    # Remove stale "FY" prefix if a full date was produced
    result = re.sub(r"^FY\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s)", r"\1", result)

    # Normalize verbose period format: "Q1-Q3 2025 (Jan-Sep)" → "Jan-Sep 2025"
    result = re.sub(r"Q1-Q3\s+(\d{4})\s*\(Jan-Sep\)", r"Jan-Sep \1", result)
    result = re.sub(r"H1\s+(\d{4})\s*\(Jan-Jun\)", r"Jan-Jun \1", result)

    return result.strip()


# ---------------------------------------------------------------------------
# Company name verification
# ---------------------------------------------------------------------------

def verify_company_name(
    locator_name: Optional[str],
    markdown: str,
) -> Optional[str]:
    """Cross-check the CU Locator's company name against the markdown.

    Looks for 编制单位 (preparation unit) line in Chinese reports.
    If found and different from locator_name, returns the markdown version.
    Otherwise returns locator_name.
    """
    if not markdown:
        return locator_name

    # Look for 编制单位：<company name> pattern
    m = re.search(r"编制单位[：:]\s*(.+?)[\s\n]", markdown[:5000])
    if m:
        doc_name = m.group(1).strip()
        if doc_name and locator_name and doc_name != locator_name:
            logger.info(
                f"  Company name mismatch: locator='{locator_name}', "
                f"document='{doc_name}'. Using document version."
            )
            return doc_name

    return locator_name


# ---------------------------------------------------------------------------
# Label cleanup
# ---------------------------------------------------------------------------

_NOISE_PATTERNS = [
    r"""\s*[（(](?:Loss|Losses?)\s+(?:shown|indicated)\s+as\s+["'\u2018\u2019\u201c\u201d-]+[)）]""",
    r"\s*[（(](?:亏损|损失).*?[)）]",
    r"\s*[（(](?:Note|注)\s*\d+[)）]",
]


def clean_label(raw: str) -> str:
    """Strip parenthetical noise from a label. Preserves raw in label_raw."""
    result = raw
    for pattern in _NOISE_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result.strip()


# ---------------------------------------------------------------------------
# Stage entry point
# ---------------------------------------------------------------------------

def run_enrich(
    extract_result: ExtractResult,
    selected: dict[str, CandidateStatement],
    enrichment_lookup: dict,
    markdown: str,
    source_file_name: str,
) -> EnrichResult:
    """Run Stage 4: enrich each extracted statement.

    Calls schema_mapper.assemble_v12_statement() which internally handles
    row enrichment (CU lookup + LLM translation). This stage adds:
    - Column header translation
    - Company name verification
    - Label cleanup (applied to the v12 doc after assembly)

    Args:
        extract_result: Output from Stage 3.
        selected: Selected candidates from Stage 2.
        enrichment_lookup: CU extractor enrichment from Stage 1.
        markdown: Full document markdown (for company name verification).
        source_file_name: Original PDF filename.

    Returns:
        EnrichResult with enriched v1.2 documents.
    """
    from extractor.schema_mapper import assemble_v12_statement

    statements: dict[str, EnrichedStatement] = {}

    for stype, extracted in extract_result.statements.items():
        candidate = selected.get(stype)

        if candidate:
            locator_metadata = candidate.to_dict()
        else:
            # No selected candidate (e.g. Textract backend where LLM
            # classification was sparse). Build minimal metadata so
            # enrich can still process the extracted statement.
            logger.info(f"  {stype}: no selected candidate, using extraction defaults")
            locator_metadata = {
                "statement_type": stype,
                "company_name": None,
                "report_language": None,
                "currency": None,
                "unit": None,
                "accounting_standard": None,
            }

        # Verify company name against document text
        verified_name = verify_company_name(
            candidate.company_name if candidate else None, markdown
        )
        if verified_name:
            locator_metadata["company_name"] = verified_name

        # Translate column headers
        translated_columns = [
            translate_column_header(col) for col in extracted.columns
        ]
        columns_translated = translated_columns != extracted.columns

        # Assemble v1.2 document (includes row enrichment + validation)
        v12_doc = assemble_v12_statement(
            statement_type=stype,
            locator_metadata=locator_metadata,
            parser_rows=extracted.rows,
            parser_columns=translated_columns,
            parser_cells=extracted.cells,
            enrichment_lookup=enrichment_lookup.copy(),
            source_file_name=source_file_name,
        )

        # Post-process: clean labels in the assembled document
        for row in v12_doc.get("rows", []):
            raw_label = row.get("label_raw", "")
            cleaned = clean_label(raw_label)
            if cleaned != raw_label:
                # Keep raw, update normalized display
                if not row.get("label_normalized"):
                    row["label_normalized"] = cleaned

        # Store translated column info in the v12 doc columns
        for i, col_meta in enumerate(v12_doc.get("columns", [])):
            if i < len(extracted.columns):
                col_meta["label_raw"] = extracted.columns[i]

        statements[stype] = EnrichedStatement(
            statement_type=stype,
            v12_doc=v12_doc,
            company_name_verified=verified_name,
            columns_translated=columns_translated,
        )

    return EnrichResult(statements=statements)
