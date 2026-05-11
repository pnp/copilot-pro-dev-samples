"""
Stage 3: Extract — full-markdown heading search + anti-contamination merging.

Hybrid approach:
  - FINDING tables: search the FULL markdown (like old pipeline) — locator
    page ranges are unreliable (can point to summary tables, not statements)
  - MERGING tables: use anti-contamination checks to stop at the right boundary
    (other statement headings, parent company markers, note headings, unrelated labels)

Search priority:
  1. Known heading patterns for statement type (full markdown)
  2. Locator's title_raw as fallback (full markdown)

Anti-contamination during table merging:
  - Stop if gap contains another statement heading or parent company markers
  - Stop if next table's rows contain labels from a different statement type
  - Stop at note headings (Notes to Financial Statements, etc.)
  - Max 3 continuation tables
"""
import logging
import re
from typing import Optional

from .contracts import (
    CandidateStatement,
    ExtractedStatement,
    ExtractResult,
    SelectResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heading patterns per statement type
# ---------------------------------------------------------------------------

_HEADING_PATTERNS: dict[str, list[str]] = {
    "balance_sheet": [
        "合并资产负债表", "連結貸借対照表",
        "STATEMENT OF FINANCIAL POSITION",
        "CONDENSED CONSOLIDATED BALANCE SHEET",
        "CONSOLIDATED BALANCE SHEET", "BALANCE SHEET",
        "BILAN", "资产负债表",
    ],
    "income_statement": [
        "合并利润表", "連結損益計算書",
        "STATEMENT OF PROFIT OR LOSS",
        "CONSOLIDATED STATEMENT OF PROFIT OR LOSS",
        "CONDENSED CONSOLIDATED STATEMENTS OF INCOME",
        "CONSOLIDATED STATEMENTS OF INCOME",
        "CONSOLIDATED STATEMENT OF INCOME", "INCOME STATEMENT",
        "COMPTE DE RESULTAT", "利润表",
        # OCI/Comprehensive Income — only match if content validation confirms it has revenue
        # (UK small companies use SCI as the income statement)
        "STATEMENT OF COMPREHENSIVE INCOME",
    ],
    "cash_flow": [
        "合并现金流量表", "連結キャッシュ・フロー計算書",
        "STATEMENT OF CASH FLOWS",
        "CONDENSED CONSOLIDATED STATEMENTS OF CASH",
        "CONSOLIDATED STATEMENTS OF CASH",
        "CONSOLIDATED STATEMENT OF CASH", "CASH FLOW",
        "TABLEAU DES FLUX", "现金流量表",
    ],
}

# Note headings / section dividers that signal we've left the statement
_NOTE_HEADING_RE = re.compile(
    r"\b\d{1,2}\.\s+[A-Z]"
    r"|\bNote\s+\d"
    r"|\bNotes to\b"
    r"|Statement of Changes"
    r"|Comprehensive Income"
    r"|Directors[''']?\s*Report"
    r"|Accounting Policies"
    r"|Significant Accounting"
    r"|母公司"
    r"|个别财务报表"
    r"|Segment\s+(?:Information|Results|Revenue)"
    r"|Supplemental\s+(?:Financial|Revenue)"
    r"|Revenue\s+by\s+(?:Segment|Geography)"
    r"|Reconciliation\s+of"
    # French PCG: stop BS continuation at Income Statement heading
    r"|COMPTE\s+DE\s+R[EÉ]SULTAT",
    re.IGNORECASE,
)

# Labels that don't belong in a continuation table for this statement type
_NON_CONTINUATION_LABELS: dict[str, list[str]] = {
    "balance_sheet": [
        "administrative expenses", "wages and salaries", "revenue",
        "cost of sales", "operating profit", "profit for",
        "depreciation", "amortisation", "amortization",
        "directors' emoluments", "directors emoluments",
        "pension cost", "social security", "audit fee",
        "tax charge", "corporation tax", "deferred tax",
        "dividend", "interest payable", "interest receivable",
        "underlying ebitda", "ebitda", "cash from operating",
    ],
    "income_statement": [
        "total assets", "total liabilities", "total equity",
        "cash and cash equivalents", "trade debtors", "trade creditors",
        "fixed assets", "current assets", "creditors",
    ],
    "cash_flow": [
        "total assets", "total liabilities", "total equity",
        "trade debtors", "trade creditors", "fixed assets",
        "share capital", "retained earnings",
        "underlying ebitda", "ebitda reconciliation",
        # Segment data that bleeds after CF ends
        "segment", "family of apps", "reality labs",
        "segment revenue", "segment income", "segment operating",
        "revenue by geography", "headcount",
    ],
}

MAX_CONTINUATION_TABLES = 3


# ---------------------------------------------------------------------------
# Content validation — does the table actually match the statement type?
# ---------------------------------------------------------------------------

# Labels that indicate a table is an Income Statement (not a Cash Flow)
_IS_CONTENT_LABELS = [
    "revenue", "total revenue", "operating revenue",
    "cost of sales", "cost of goods", "gross profit",
    "operating expenses", "operating profit", "ebitda",
    "profit before tax", "income tax", "net income",
    "earnings per share", "diluted earnings",
    # French PCG
    "chiffre d'affaires", "produits d'exploitation",
    "charges d'exploitation", "resultat d'exploitation",
    # Non-GAAP indicators (should NOT be in CF)
    "non-gaap", "adjusted ebitda", "adjusted operating",
]

# Labels that indicate a table is a Cash Flow statement
_CF_CONTENT_LABELS = [
    "cash flows from operating", "cash provided by operating",
    "cash used in investing", "cash flows from investing",
    "cash flows from financing", "cash provided by financing",
    "net increase in cash", "net decrease in cash",
    "cash at beginning", "cash at end",
    "cash and cash equivalents at",
]


def _validate_table_content(statement_type: str, markdown: str, table_start: int, table_end: int) -> bool:
    """Check if a table's content matches the expected statement type.

    Returns True if content looks correct, False if it's the wrong statement.
    """
    table_html = markdown[table_start:min(table_end, table_start + 3000)]
    first_cells = re.findall(r"<td[^>]*>(.*?)</td>", table_html, re.DOTALL | re.IGNORECASE)
    cell_text = " ".join(re.sub(r"<[^>]+>", "", c).strip().lower() for c in first_cells[:15])

    if statement_type == "cash_flow":
        # If first rows contain IS-like content but no CF-like content, it's wrong
        has_is_content = any(label in cell_text for label in _IS_CONTENT_LABELS)
        has_cf_content = any(label in cell_text for label in _CF_CONTENT_LABELS)
        if has_is_content and not has_cf_content:
            logger.info(f"  {statement_type}: table content looks like Income Statement, skipping")
            return False

    if statement_type == "income_statement":
        # If first rows only contain OCI items (hedging, translation) with no revenue/profit, skip
        has_revenue = any(label in cell_text for label in [
            "revenue", "total revenue", "operating revenue", "sales",
            "turnover", "gross profit", "operating profit", "profit before",
            "chiffre d'affaires", "produits d'exploitation",
        ])
        has_oci_only = any(label in cell_text for label in ["hedging", "translation differences"])
        has_no_profit = not any(label in cell_text for label in ["profit", "loss", "income", "revenue", "turnover", "sales"])
        if has_oci_only and has_no_profit:
            logger.info(f"  {statement_type}: table content looks like pure OCI statement, skipping")
            return False

    return True


# ---------------------------------------------------------------------------
# Full-markdown heading search (like old pipeline — reliable)
# ---------------------------------------------------------------------------

def _find_heading_offset(
    statement_type: str,
    title_raw: str,
    markdown: str,
) -> Optional[int]:
    """Find the heading offset by searching the FULL markdown.

    Strategy 1: Known heading patterns (most reliable — language-aware)
    Strategy 2: Locator's title_raw as fallback

    Both strategies validate table content to avoid picking the wrong table
    (e.g., P&L summary on the CF page, OCI instead of IS).

    Returns absolute offset into the markdown, or None.
    """
    # --- Strategy 1: Known heading patterns (full markdown) ---
    for pattern in _HEADING_PATTERNS.get(statement_type, []):
        for m in re.finditer(re.escape(pattern), markdown, re.IGNORECASE):
            lookahead = markdown[m.start():m.start() + 500]
            lookbehind = markdown[max(0, m.start() - 100):m.start()]

            # Check: heading before a <table>, OR heading inside a <caption> within a <table>
            has_table_ahead = "<table>" in lookahead.lower()
            has_table_behind = "<table>" in lookbehind.lower() and "<caption>" in lookbehind.lower()

            if has_table_ahead or has_table_behind:
                # Find the actual table start
                if has_table_behind:
                    table_start = markdown.rfind("<table>", max(0, m.start() - 100), m.start())
                else:
                    table_start = markdown.find("<table>", m.start())
                table_end = markdown.find("</table>", table_start) if table_start >= 0 else -1

                # Validate: does the table content match this statement type?
                if table_start >= 0 and table_end >= 0:
                    if not _validate_table_content(statement_type, markdown, table_start, table_end):
                        continue  # Skip this match, try next occurrence

                    # Skip tables that are too small to be a primary statement
                    # (likely a summary or note table with the same heading)
                    row_count = len(re.findall(r"<tr>", markdown[table_start:table_end], re.IGNORECASE))
                    min_rows = {"balance_sheet": 10, "income_statement": 8, "cash_flow": 8}.get(statement_type, 5)
                    if row_count < min_rows:
                        logger.info(
                            f"  {statement_type}: skipping small table at offset {m.start()} "
                            f"({row_count} rows < {min_rows} min)"
                        )
                        continue

                logger.info(
                    f"  {statement_type}: matched heading pattern "
                    f"'{pattern}' at offset {m.start()}"
                    f"{' (caption)' if has_table_behind else ''}"
                )
                return table_start if has_table_behind else m.start()

    # --- Strategy 2: Locator's raw title (full markdown) ---
    if title_raw and len(title_raw) > 5:
        for prefix_len in [len(title_raw), 40, 20]:
            prefix = title_raw[:prefix_len].strip()
            if not prefix:
                continue
            idx = markdown.lower().find(prefix.lower())
            if idx >= 0:
                lookahead = markdown[idx:idx + 500]
                if "<table>" in lookahead.lower():
                    logger.info(
                        f"  {statement_type}: matched title_raw "
                        f"'{prefix[:40]}' at offset {idx}"
                    )
                    return idx

    return None



# ---------------------------------------------------------------------------
# Table merging with anti-contamination
# ---------------------------------------------------------------------------

def _merge_continuation_tables(
    statement_type: str,
    markdown: str,
    table_start: int,
    initial_end: int,
) -> tuple[int, int]:
    """Merge consecutive tables that belong to the same statement.

    Uses content-based checks only (like old pipeline). No page range constraints
    because locator page ranges can be wrong.

    Returns (end_offset, tables_merged).
    """
    # Build set of OTHER statement type headings
    other_headings: list[str] = []
    for other_type, patterns in _HEADING_PATTERNS.items():
        if other_type != statement_type:
            other_headings.extend(patterns)

    end_offset = initial_end
    tables_merged = 1

    while tables_merged < MAX_CONTINUATION_TABLES:
        remaining = markdown[end_offset:]
        next_table = remaining.find("<table>")
        if next_table < 0:
            break

        gap_text = remaining[:next_table]

        # Stop: another statement type heading in the gap
        if any(h.upper() in gap_text.upper() for h in other_headings):
            break

        # Stop: note headings or parent company markers in the gap
        # Exception: "Comprehensive Income" is a valid IS continuation (IFRS)
        note_match = _NOTE_HEADING_RE.search(gap_text)
        if note_match:
            matched_text = note_match.group(0)
            if statement_type == "income_statement" and "comprehensive income" in matched_text.lower():
                pass  # Allow IS to continue past SCI heading
            else:
                break

        # Stop: large gap (> 500 chars non-whitespace = section break)
        gap_stripped = re.sub(r"\s+", "", gap_text)
        if len(gap_stripped) > 500:
            break

        # Stop: next table has a <caption> with another statement's heading
        next_close = remaining.find("</table>", next_table)
        if next_close < 0:
            break
        next_table_html = remaining[next_table:next_close]
        caption_match = re.search(r"<caption>(.*?)</caption>", next_table_html[:500], re.IGNORECASE)
        if caption_match:
            caption_text = caption_match.group(1).upper()
            if any(h.upper() in caption_text for h in other_headings):
                logger.info(f"  {statement_type}: stopping merge — next table caption contains other statement heading")
                break

        # Stop: next table content doesn't belong to this statement type
        first_cells = re.findall(
            r"<td[^>]*>(.*?)</td>", next_table_html[:2000],
            re.DOTALL | re.IGNORECASE,
        )
        first_labels = " ".join(
            re.sub(r"<[^>]+>", "", c).strip().lower()
            for c in first_cells[:6]
        )
        bad_labels = _NON_CONTINUATION_LABELS.get(statement_type, [])
        if any(bl in first_labels for bl in bad_labels):
            break

        end_offset = end_offset + next_close + len("</table>")
        tables_merged += 1

    return end_offset, tables_merged


# ---------------------------------------------------------------------------
# Locate a single statement's table
# ---------------------------------------------------------------------------

def locate_table(
    statement_type: str,
    candidate: CandidateStatement,
    markdown: str,
    page_map: list[tuple[int, int, int]],
) -> Optional[dict]:
    """Find and merge table(s) for a statement in the markdown.

    Uses full-markdown heading search (reliable) + content-based merging
    with anti-contamination (prevents bleeding).

    Returns dict with md_offset, md_end_offset, start_page, end_page, tables_merged
    or None if not found.
    """
    from extractor.statement_detector import _offset_to_page

    title_raw = (candidate.title_raw or "").strip()

    # Step 1: Find heading in FULL markdown
    direct_offset = _find_heading_offset(statement_type, title_raw, markdown)

    if direct_offset is None:
        logger.warning(f"  {statement_type}: could not locate via heading search")
        return None

    # Step 2: Find the table block
    table_start = markdown.find("<table>", direct_offset)
    if table_start < 0:
        return None
    table_end = markdown.find("</table>", table_start)
    if table_end < 0:
        return None
    initial_end = table_end + len("</table>")

    # Step 3: Merge continuation tables (content-based anti-contamination)
    end_offset, tables_merged = _merge_continuation_tables(
        statement_type, markdown, table_start, initial_end,
    )

    start_page = _offset_to_page(direct_offset, page_map) if page_map else 1
    end_page = _offset_to_page(end_offset, page_map) if page_map else start_page

    logger.info(
        f"  {statement_type}: located table at pages {start_page}-{end_page} "
        f"({tables_merged} table(s), {end_offset - direct_offset} chars)"
    )

    return {
        "md_offset": direct_offset,
        "md_end_offset": end_offset,
        "start_page": start_page,
        "end_page": end_page,
        "tables_merged": tables_merged,
    }


# ---------------------------------------------------------------------------
# Stage entry point
# ---------------------------------------------------------------------------

def _locate_by_llm_classification(
    statement_type: str,
    classification,  # TableClassification from llm_table_classifier
    markdown: str,
    page_map: list[tuple[int, int, int]],
) -> Optional[dict]:
    """Locate and merge tables starting from an LLM-classified table offset."""
    from extractor.statement_detector import _offset_to_page

    table_start = classification.md_offset
    table_end_initial = classification.md_end_offset

    # Merge continuation tables (same anti-contamination logic)
    end_offset, tables_merged = _merge_continuation_tables(
        statement_type, markdown, table_start, table_end_initial,
    )

    start_page = _offset_to_page(table_start, page_map) if page_map else 1
    end_page = _offset_to_page(end_offset, page_map) if page_map else start_page

    logger.info(
        f"  {statement_type}: LLM classified table at pages {start_page}-{end_page} "
        f"({tables_merged} table(s), confidence={classification.confidence:.2f})"
    )

    return {
        "md_offset": table_start,
        "md_end_offset": end_offset,
        "start_page": start_page,
        "end_page": end_page,
        "tables_merged": tables_merged,
    }


def run_extract(
    select_result: SelectResult,
    markdown: str,
    page_map: list[tuple[int, int, int]],
    pages: list[dict],
    requested_types: list[str] | None = None,
) -> ExtractResult:
    """Run Stage 3: locate and parse tables for each selected statement.

    Strategy (layered, most reliable first):
      1. Heading pattern search (fast, works for known formats)
      2. LLM table classifier (handles any language/format, one call for all)
      3. CU Locator title_raw fallback (last resort)

    Args:
        select_result: Output from Stage 2.
        markdown: Full document markdown from CU.
        page_map: Page offset map from Stage 1.
        pages: Raw page objects from CU.
        requested_types: Statement types to extract (for fallback search).

    Returns:
        ExtractResult with parsed data per statement.
    """
    from extractor.html_table_parser import parse_html_table

    if requested_types is None:
        requested_types = list(select_result.selected.keys())

    statements: dict[str, ExtractedStatement] = {}
    failures: dict[str, str] = {}

    # --- Layer 1: Try heading pattern search for each type ---
    types_needing_llm = []

    for stype in requested_types:
        candidate = select_result.selected.get(stype)

        if candidate:
            location = locate_table(stype, candidate, markdown, page_map)
        else:
            dummy = CandidateStatement(statement_type=stype)
            location = locate_table(stype, dummy, markdown, page_map)

        if location:
            rows, columns, cells = parse_html_table(
                markdown, location["md_offset"], location["md_end_offset"]
            )
            if cells:
                statements[stype] = ExtractedStatement(
                    statement_type=stype,
                    rows=rows, columns=columns, cells=cells,
                    md_offset=location["md_offset"],
                    md_end_offset=location["md_end_offset"],
                    start_page=location["start_page"],
                    end_page=location["end_page"],
                    tables_merged=location.get("tables_merged", 1),
                )
                continue

        # Heading search failed — need LLM fallback
        types_needing_llm.append(stype)

    # --- Layer 2: LLM table classifier for any types not found ---
    if types_needing_llm:
        logging.info(
            f"[Extract] Heading search missed: {types_needing_llm}. "
            f"Running LLM table classifier..."
        )
        try:
            from extractor.llm_table_classifier import classify_tables, get_best_table

            classifications = classify_tables(markdown)

            for stype in list(types_needing_llm):
                best = get_best_table(classifications, stype)
                if not best:
                    continue

                location = _locate_by_llm_classification(
                    stype, best, markdown, page_map,
                )
                if not location:
                    continue

                rows, columns, cells = parse_html_table(
                    markdown, location["md_offset"], location["md_end_offset"]
                )
                if cells:
                    statements[stype] = ExtractedStatement(
                        statement_type=stype,
                        rows=rows, columns=columns, cells=cells,
                        md_offset=location["md_offset"],
                        md_end_offset=location["md_end_offset"],
                        start_page=location["start_page"],
                        end_page=location["end_page"],
                        tables_merged=location.get("tables_merged", 1),
                    )
                    types_needing_llm.remove(stype)

        except Exception as e:
            logging.warning(f"[Extract] LLM classifier failed: {e}")

    # --- Mark remaining as failures ---
    for stype in types_needing_llm:
        failures[stype] = "could_not_locate_in_markdown"

    return ExtractResult(statements=statements, failures=failures)
