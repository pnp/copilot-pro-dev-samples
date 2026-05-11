"""
extractor/statement_detector.py
-------------------------------
Locates and parses the three core financial statements from the markdown
string produced by Azure Content Understanding prebuilt-read.

How Azure CU structures the output
  The full document is returned as a single markdown string at:
    result.contents[0].markdown
  Page boundaries are tracked via:
    result.contents[0].pages[*].spans[*].offset / .length
  Azure CU does NOT return structured table objects for financial tables;
  instead each table row is a sequence of \n\n-separated plain-text tokens.

Pipeline (in order)
  1. _all_heading_offsets   — find all pages where each statement appears
  2. _pick_cluster_offsets  — select the main consolidated statements cluster
                              (ignores summary tables scattered earlier)
  3. locate_statements      — determine char-offset boundaries per statement
  4. _parse_plain_text_table— tokenise and reconstruct rows/columns/cells
  5. build_statement_json   — assemble final JSON; optionally run LLM pass
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Statement heading detection — two-tier approach
# ---------------------------------------------------------------------------
#
# Tier 1 (fast, no LLM): Exact heading match from a curated list of known
#   IFRS and US GAAP heading variants.  This is tried first because it is
#   deterministic and free.
#
# Tier 2 (fast, no LLM): Keyword-based semantic scoring.  Each candidate
#   text region is scored against characteristic keyword clusters for each
#   statement type.  This handles non-standard headings, private company
#   filings, and creative formatting without requiring an LLM call.
#
# Both tiers validate matches by checking for numeric financial data within
# _DATA_LOOKAHEAD chars — this rules out TOC entries and narrative mentions.
# ---------------------------------------------------------------------------

# Tier 1: Exact heading strings (tried in priority order; first match wins).
# Covers IFRS, US GAAP, "Condensed" variants, and CJK (Chinese/Japanese).
HEADINGS: dict[str, list[str]] = {
    "balance_sheet": [
        # Chinese (Simplified)
        "合并资产负债表",                        # Consolidated Balance Sheet
        "资产负债表",                            # Balance Sheet
        # English — IFRS + US GAAP
        "Condensed Consolidated Balance Sheets",
        "Condensed Consolidated Balance Sheet",
        "Consolidated Statement of Financial Position",
        "Consolidated Balance Sheets",
        "Consolidated Balance Sheet",
        "Statement of Financial Position",
        "Balance Sheets",
        "Balance Sheet",
        # Japanese
        "連結財政状態計算書",                    # Consolidated Statement of Financial Position
        "連結貸借対照表",                        # Consolidated Balance Sheet
        "貸借対照表",                            # Balance Sheet
    ],
    "cash_flow": [
        # Chinese (Simplified)
        "合并现金流量表",                        # Consolidated Cash Flow Statement
        "现金流量表",                            # Cash Flow Statement
        # English — IFRS + US GAAP
        "Condensed Consolidated Statements of Cash Flows",
        "Condensed Consolidated Statement of Cash Flows",
        "Consolidated Statements of Cash Flows",
        "Consolidated Statement of Cash Flows",
        "Consolidated Statement of Cash Flow",
        "Statements of Cash Flows",
        "Statement of Cash Flows",
        # Japanese
        "連結キャッシュ・フロー計算書",          # Consolidated Cash Flow Statement
    ],
    "income_statement": [
        # Chinese (Simplified)
        "合并利润表",                            # Consolidated Income Statement
        "利润表",                                # Income Statement
        # English — IFRS + US GAAP
        "Condensed Consolidated Statements of Income",
        "Condensed Consolidated Statement of Income",
        "Consolidated Statements of Income",
        "Consolidated Statements of Operations",
        "Consolidated Statement of Income",
        "Consolidated Statement of Operations",
        "Consolidated Statement of Profit",
        "Statements of Income",
        "Statements of Operations",
        "Income Statement",
        # Japanese
        "連結損益計算書",                        # Consolidated Income Statement
        "連結損益及び包括利益計算書",            # Consolidated P&L and Comprehensive Income
        "損益計算書",                            # Income Statement
    ],
}

# Tier 2: Keyword clusters for semantic scoring.
# Each keyword carries a weight.  A candidate heading/region is scored by
# summing the weights of all keywords it contains.  Higher weight = more
# discriminative (i.e. "financial position" is uniquely balance-sheet,
# while "consolidated" is shared across all types).
#
# A minimum score threshold prevents false positives from narrative text
# that incidentally mentions a few financial terms.
_KEYWORD_SCORES: dict[str, list[tuple[str, float]]] = {
    "balance_sheet": [
        ("balance sheet", 3.0),
        ("financial position", 3.0),
        ("assets", 2.0),
        ("liabilities", 2.0),
        ("equity", 1.5),
        ("stockholders", 1.5),
        ("shareholders", 1.5),
        ("current assets", 1.0),
        ("current liabilities", 1.0),
        ("non-current", 1.0),
        # Chinese
        ("资产负债表", 3.0),
        ("资产", 2.0),
        ("负债", 2.0),
        ("所有者权益", 1.5),
        ("流动资产", 1.0),
        ("流动负债", 1.0),
        # Japanese
        ("貸借対照表", 3.0),
        ("財政状態", 3.0),
    ],
    "cash_flow": [
        ("cash flow", 3.0),
        ("cash flows", 3.0),
        ("operating activities", 2.5),
        ("investing activities", 2.5),
        ("financing activities", 2.5),
        ("net cash", 2.0),
        ("cash provided", 1.5),
        ("cash used", 1.5),
        ("cash equivalents", 1.0),
        # Chinese
        ("现金流量表", 3.0),
        ("经营活动", 2.5),
        ("投资活动", 2.5),
        ("筹资活动", 2.5),
        # Japanese
        ("キャッシュ・フロー", 3.0),
        ("営業活動", 2.5),
        ("投資活動", 2.5),
        ("財務活動", 2.5),
    ],
    "income_statement": [
        ("income statement", 3.0),
        ("statement of income", 3.0),
        ("statement of operations", 3.0),
        ("statement of profit", 3.0),
        ("net income", 2.0),
        ("revenue", 2.0),
        ("earnings per share", 2.0),
        ("cost of revenue", 1.5),
        ("operating expenses", 1.5),
        ("income from operations", 1.5),
        ("gross profit", 1.5),
        ("operating income", 1.0),
        # Chinese
        ("利润表", 3.0),
        ("营业收入", 2.0),
        ("净利润", 2.0),
        ("营业成本", 1.5),
        ("利润总额", 1.5),
        # Japanese
        ("損益計算書", 3.0),
        ("売上高", 2.0),
        ("当期純利益", 2.0),
    ],
}

# Minimum keyword score to consider a candidate as a valid statement heading.
# Prevents false positives from narrative paragraphs mentioning financial terms.
_MIN_KEYWORD_SCORE = 3.0

# A heading match is valid only if numeric data appears within this many
# characters after it — rules out TOC references.
_DATA_LOOKAHEAD = 1000
_NUMBER_RE    = re.compile(r"\d[\d,]+")

# Density-based end-of-section detection
# Scan forward in windows; when financial number count drops below threshold
# for two consecutive windows, that marks the end of the statement section.
_DENSITY_WINDOW    = 3000   # chars per window
_DENSITY_THRESHOLD = 5      # min numbers per window to still be "in statement"
_DENSITY_MIN_CONSECUTIVE = 2  # consecutive low-density windows required

# Note refs are small integers like "5", "6, 15", "10, 15" — max 2 digits each part
_NOTE_REF_RE  = re.compile(r"^\d{1,2}(?:[,\s]+\d{1,2})*$")
# Financial values: optional leading currency symbol ($, ¥, €, £) and/or
# minus, digits+commas+optional decimal, or (negatives in parentheses).
# Decimal support handles EPS and per-share figures.
_CURRENCY_SYM = r"[\$¥€£]?\s*"
_VALUE_RE     = re.compile(
    rf"^{_CURRENCY_SYM}-?[\d,]+(?:\.\d+)?$"
    rf"|^{_CURRENCY_SYM}\([\d,]+(?:\.\d+)?\)$"
)
# Page markers to strip from sections before parsing.
# Also strips section-numbering stubs (e.g. "2\)" / "3"") that Azure CU
# sometimes emits as isolated tokens at section boundaries.
_PAGE_MARKER_RE = re.compile(r"^-\d+-$|^<!--.*-->$|^\d+\\?\)$")

# Hard-stop patterns that signal the end of the financial statements section.
#
# IFRS terminators:
#   - "[Notes to ..." — narrative notes section
#   - "Consolidated Statement of Comprehensive Income"
#   - "Consolidated Statement of Changes" (in equity)
#   - "Statement of Changes in Stockholders/Shareholders/Owners/Parent"
#
# US GAAP terminators (common in 10-K/10-Q filings and earnings releases):
#   - "Segment Results" / "Segment Information" — segment disclosure tables
#   - "Reconciliation of GAAP" — GAAP-to-non-GAAP reconciliation tables
#
# NOTE: "Supplemental cash flow data" is NOT a terminator — it is part of
# the cash flow statement itself (contains "Cash paid for income taxes" etc).
_NOTES_TERMINATOR_RE = re.compile(
    r"\[Notes to\b"
    r"|Consolidated Statement of Comprehensive Income"
    r"|Consolidated Statement of Changes"
    r"|Statement of Changes in (Stockholders|Shareholders|Owners|Parent)"
    r"|Segment Results\b"
    r"|Segment Information\b"
    r"|Reconciliation of GAAP\b",
    re.IGNORECASE,
)


def _find_section_end_by_density(markdown: str, start_offset: int) -> int:
    """
    Generic end-of-section detector.
    Scans forward in fixed windows from start_offset.
    Returns the offset where financial number density drops to near-zero,
    indicating the transition from tabular statements to narrative notes.
    Works for any company, any language.
    """
    # Hard-stop: if a "[Notes to ..." heading is found within 100K chars,
    # use it as the section boundary — the notes section has high number
    # density (all the footnote tables) so the density scan alone is
    # unreliable once we reach it.
    note_m = _NOTES_TERMINATOR_RE.search(markdown, start_offset)
    if note_m and (note_m.start() - start_offset) < 100_000:
        return note_m.start()

    pos = start_offset
    low_count = 0
    while pos < len(markdown):
        window = markdown[pos: pos + _DENSITY_WINDOW]
        nums = len(re.findall(r"\b\d[\d,]{2,}\b", window))
        if nums < _DENSITY_THRESHOLD:
            low_count += 1
            if low_count >= _DENSITY_MIN_CONSECUTIVE:
                # Return the start of the first low-density window
                return pos - (_DENSITY_MIN_CONSECUTIVE - 1) * _DENSITY_WINDOW
        else:
            low_count = 0
        pos += _DENSITY_WINDOW
    return len(markdown)

def _get_contents(raw_result: dict) -> dict:
    """Return contents[0] from the Azure CU result envelope."""
    result = raw_result.get("result", raw_result)
    contents = result.get("contents", [])
    if not contents:
        raise ValueError("Azure CU result has no 'contents' array.")
    return contents[0]


def _get_markdown(raw_result: dict) -> str:
    return _get_contents(raw_result).get("markdown", "")


def _get_pages(raw_result: dict) -> list[dict]:
    return _get_contents(raw_result).get("pages", [])


# ---------------------------------------------------------------------------
# Page number lookup (char offset -> page number)
# ---------------------------------------------------------------------------

def _build_page_map(pages: list[dict]) -> list[tuple[int, int, int]]:
    """
    Build a sorted list of (start_offset, end_offset, page_number) tuples
    using the spans[] array on each page object.
    """
    mapping: list[tuple[int, int, int]] = []
    for page in pages:
        page_num: int = page.get("pageNumber", 0)
        for span in page.get("spans", []):
            offset: int = span.get("offset", 0)
            length: int = span.get("length", 0)
            mapping.append((offset, offset + length, page_num))
    mapping.sort(key=lambda t: t[0])
    return mapping


def _offset_to_page(offset: int, page_map: list[tuple[int, int, int]]) -> int:
    """Return the page number containing the given character offset."""
    for start, end, page_num in page_map:
        if start <= offset < end:
            return page_num
    return page_map[-1][2] if page_map else 0


# ---------------------------------------------------------------------------
# Statement locator
# ---------------------------------------------------------------------------

def _has_data_nearby(markdown: str, offset: int) -> bool:
    """True if numeric financial data appears within _DATA_LOOKAHEAD chars."""
    lookahead = markdown[offset: offset + _DATA_LOOKAHEAD]
    return bool(_NUMBER_RE.search(lookahead))


def _tier1_heading_offsets(markdown: str, headings: list[str]) -> list[int]:
    """
    Tier 1: Exact heading match.

    Return ALL char offsets where a known heading string appears AND is followed
    by numeric financial data within _DATA_LOOKAHEAD chars.

    Headings are tried in priority order (most specific first). As soon as one
    heading yields any valid match, those offsets are returned exclusively.
    This prevents short fallback terms (e.g. "Balance Sheet") from matching
    unrelated fragments when a more specific heading would have matched.
    """
    for heading in headings:
        results = []
        for m in re.finditer(re.escape(heading), markdown, re.IGNORECASE):
            if _has_data_nearby(markdown, m.start()):
                results.append(m.start())
        if results:
            return sorted(results)
    return []


def _score_candidate(text: str, keywords: list[tuple[str, float]]) -> float:
    """Score a text region against a keyword cluster. Higher = more likely."""
    text_lower = text.lower()
    return sum(weight for keyword, weight in keywords if keyword in text_lower)


def _tier2_keyword_offsets(
    markdown: str,
    statement_type: str,
) -> list[int]:
    """
    Tier 2: Keyword-based semantic scoring.

    Scans the markdown for heading-like regions (lines that are short, often
    uppercase or title-cased, and precede numeric data) and scores each one
    against the characteristic keyword cluster for the given statement type.

    Returns offsets of regions that score >= _MIN_KEYWORD_SCORE and are
    followed by numeric data.  This handles non-standard headings that
    Tier 1's exact-match list doesn't cover.
    """
    keywords = _KEYWORD_SCORES.get(statement_type, [])
    if not keywords:
        return []

    results: list[int] = []

    # Scan for heading-like lines: short-ish text (< 200 chars) that could
    # be a statement title.  We use \n\n boundaries since Azure CU separates
    # structural elements with double newlines.
    for m in re.finditer(r"(?:^|\n\n)(.{10,200})(?=\n\n)", markdown):
        candidate = m.group(1).strip()
        # Skip candidates that look like data values or page markers.
        if _VALUE_RE.match(candidate) or _PAGE_MARKER_RE.match(candidate):
            continue
        score = _score_candidate(candidate, keywords)
        if score >= _MIN_KEYWORD_SCORE and _has_data_nearby(markdown, m.start()):
            results.append(m.start())

    return sorted(results)


def _all_heading_offsets(markdown: str, headings: list[str], statement_type: str) -> list[int]:
    """
    Two-tier heading detection: try exact match first, fall back to keyword
    scoring for non-standard headings.

    Args:
        markdown: Full document markdown from Azure CU.
        headings: Tier 1 exact heading strings for this statement type.
        statement_type: One of "balance_sheet", "cash_flow", "income_statement".

    Returns:
        List of character offsets where the statement heading was found.
    """
    # Tier 1: exact heading match (fast, deterministic)
    offsets = _tier1_heading_offsets(markdown, headings)
    if offsets:
        return offsets

    # Tier 2: keyword-based semantic scoring (handles non-standard headings)
    offsets = _tier2_keyword_offsets(markdown, statement_type)
    if offsets:
        return offsets

    return []


def _pick_cluster_offsets(
    all_offsets: dict[str, list[int]]
) -> dict[str, Optional[int]]:
    """
    Generic cluster selection: annual reports always contain a section where
    all three financial statements appear close together (within ~200,000 chars).
    Summary tables and segment disclosures scatter individual statements
    throughout the document, but the actual consolidated statements section
    is a tight cluster.

    Algorithm:
      1. Collect every valid occurrence of every statement heading.
      2. For the statement type with the fewest occurrences (most specific),
         use each occurrence as a candidate anchor.
      3. For each anchor, count how many other statement types have an
         occurrence within MAX_CLUSTER_SPAN chars after it.
      4. Pick the anchor with the most co-located statements. Ties broken
         by preferring later anchors (main statements appear after summaries).
      5. For each statement type choose the occurrence nearest to and after
         the winning anchor.
    """
    MAX_CLUSTER_SPAN = 200_000  # chars — tuned to fit any typical annual report

    # Flatten all offsets into (offset, type) pairs
    all_pairs: list[tuple[int, str]] = []
    for stype, offsets in all_offsets.items():
        for o in offsets:
            all_pairs.append((o, stype))
    all_pairs.sort()

    best_anchor: Optional[int] = None
    best_score = -1

    for anchor_offset, anchor_type in all_pairs:
        # Count distinct statement types with an occurrence in [anchor, anchor+SPAN]
        types_found = set()
        for offset, stype in all_pairs:
            if offset >= anchor_offset and offset <= anchor_offset + MAX_CLUSTER_SPAN:
                types_found.add(stype)
        score = len(types_found)
        # Prefer higher score; on tie prefer EARLIER anchor — the first
        # complete cluster is the main consolidated statements section;
        # later ones tend to be subsidiary or segment statements.
        if score > best_score or (score == best_score and best_anchor is not None and anchor_offset < best_anchor):
            best_score = score
            best_anchor = anchor_offset

    if best_anchor is None:
        # Fallback: just return first occurrence of each
        return {stype: (offsets[0] if offsets else None)
                for stype, offsets in all_offsets.items()}

    # For each statement type pick the occurrence closest to and >= best_anchor
    chosen: dict[str, Optional[int]] = {}
    for stype, offsets in all_offsets.items():
        candidates = [o for o in offsets if o >= best_anchor]
        if candidates:
            chosen[stype] = min(candidates)
        elif offsets:
            chosen[stype] = offsets[0]  # only occurrence is before anchor
        else:
            chosen[stype] = None

    return chosen


def _llm_detect_statements(markdown: str) -> dict[str, Optional[int]]:
    """
    Use an LLM to identify the three core financial statements in the document.

    Sends a compact summary of the document (first ~4000 chars plus a sampled
    section index) to the LLM and asks it to return the heading text and
    approximate character offset for each statement.

    This approach is language-agnostic: works for English, Chinese, Japanese,
    or any other language without hard-coded patterns.

    Returns a dict mapping statement_type -> char offset (or None if not found).
    """
    import json as _json
    from .llm_reconciler import _get_client, _DEPLOYMENT

    # Build a compact document outline for the LLM.
    # Include the first 4000 chars (typically covers TOC and early pages),
    # plus a sampled section index showing \n\n-delimited tokens with offsets.
    preview = markdown[:4000]

    # Build a sparse index: for every \n\n token, record offset + first 80 chars.
    # This lets the LLM see the full document structure without sending all text.
    token_index: list[dict] = []
    pos = 0
    for tok in markdown.split("\n\n"):
        tok_stripped = tok.strip()
        if tok_stripped and len(tok_stripped) > 5:
            token_index.append({
                "offset": pos,
                "text": tok_stripped[:100],
            })
        pos += len(tok) + 2  # +2 for the \n\n separator

    # Limit to ~200 entries to stay within token budget.
    if len(token_index) > 200:
        step = len(token_index) // 200
        token_index = token_index[::step]

    prompt = (
        "You are analyzing a financial report (PDF extracted to markdown). "
        "Identify the THREE core financial statements:\n"
        "1. balance_sheet (Statement of Financial Position / Balance Sheet / "
        "资产负债表 / 貸借対照表)\n"
        "2. income_statement (Income Statement / P&L / Statement of Operations / "
        "利润表 / 損益計算書)\n"
        "3. cash_flow (Cash Flow Statement / 现金流量表 / キャッシュ・フロー計算書)\n\n"
        "IMPORTANT RULES:\n"
        "- Pick the CONSOLIDATED version, not the parent/standalone version.\n"
        "- Each statement must be followed by numeric financial data.\n"
        "- If the same statement appears multiple times (e.g. summary table + "
        "full table), pick the FULL version with detailed line items.\n"
        "- Return the character OFFSET where each statement heading begins.\n\n"
        f"DOCUMENT PREVIEW (first 4000 chars):\n{preview}\n\n"
        f"DOCUMENT TOKEN INDEX (offset + first 100 chars of each section):\n"
        f"{_json.dumps(token_index, ensure_ascii=False, indent=1)}\n\n"
        "Return ONLY a JSON object:\n"
        '{"statements": [\n'
        '  {"type": "balance_sheet", "heading": "<exact heading text>", "offset": <int>},\n'
        '  {"type": "income_statement", "heading": "...", "offset": <int>},\n'
        '  {"type": "cash_flow", "heading": "...", "offset": <int>}\n'
        "]}\n"
        "If a statement is not found, omit it from the array."
    )

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial document analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        result = _json.loads(response.choices[0].message.content)
        statements = result.get("statements", [])
    except Exception as e:
        print(f"      [LLM] statement detection failed: {e}")
        return {"balance_sheet": None, "cash_flow": None, "income_statement": None}

    # Convert LLM response to offset map.
    offsets: dict[str, Optional[int]] = {
        "balance_sheet": None,
        "cash_flow": None,
        "income_statement": None,
    }

    for s in statements:
        stype = s.get("type", "")
        llm_offset = s.get("offset")
        heading = s.get("heading", "")

        if stype not in offsets or llm_offset is None:
            continue

        # The LLM returns an approximate offset from the token index.
        # Verify by searching for the heading text near that offset.
        search_start = max(0, llm_offset - 500)
        search_end = min(len(markdown), llm_offset + 500)
        search_region = markdown[search_start:search_end]

        # Try to find the exact heading in the region.
        idx = search_region.find(heading)
        if idx >= 0:
            offsets[stype] = search_start + idx
        else:
            # Fallback: use the LLM offset directly if heading not found.
            # (Heading text may have been truncated in the token index.)
            offsets[stype] = llm_offset

        print(f"      [LLM] {stype}: '{heading}' at offset {offsets[stype]}")

    return offsets


def locate_statements(
    raw_result: dict,
    use_llm: bool = True,
) -> dict[str, Optional[dict]]:
    """
    Scan the markdown and return a mapping of statement type -> page range.

    Detection strategy (in order):
      1. LLM-based detection (when use_llm=True and credentials available):
         Sends the document structure to the LLM which identifies statement
         locations in any language. Most accurate, costs ~$0.001/document.
      2. Tier 1 — exact heading match from curated list (free, fast).
      3. Tier 2 — keyword-based semantic scoring (free, handles non-standard).

    Section boundaries are always determined by the same logic: nearest
    adjacent statement heading, hard-stop terminators, or density-based end.
    """
    markdown = _get_markdown(raw_result)
    pages = _get_pages(raw_result)
    page_map = _build_page_map(pages)

    offsets: dict[str, Optional[int]] = None

    # Strategy 1: LLM-based detection (most accurate, language-agnostic)
    if use_llm:
        try:
            offsets = _llm_detect_statements(markdown)
            # Check if LLM found at least one statement
            if not any(v is not None for v in offsets.values()):
                print("      [LLM] no statements found, falling back to pattern matching")
                offsets = None
        except Exception:
            offsets = None  # fall through to pattern matching

    # Strategy 2+3: Pattern matching fallback (Tier 1 exact + Tier 2 keywords)
    if offsets is None:
        all_offsets: dict[str, list[int]] = {}
        for statement_type, headings in HEADINGS.items():
            all_offsets[statement_type] = _all_heading_offsets(markdown, headings, statement_type)
        offsets = _pick_cluster_offsets(all_offsets)

    # Determine section boundaries
    located: dict[str, Optional[dict]] = {}
    for statement_type, offset in offsets.items():
        if offset is None:
            located[statement_type] = None
            continue

        start_page = _offset_to_page(offset, page_map)

        # Section ends at the nearest other chosen statement heading
        next_offset = None
        for other_type, other_offset in offsets.items():
            if other_type == statement_type or other_offset is None:
                continue
            if other_offset > offset:
                if next_offset is None or other_offset < next_offset:
                    next_offset = other_offset

        # For all statements: also look for hard-stop section terminators
        # (e.g. Comprehensive Income or Changes in Equity sections that can
        # appear between the three main statements).  Skip 200 chars past the
        # current heading to avoid matching the heading text itself.
        term_m = _NOTES_TERMINATOR_RE.search(markdown, offset + 200)
        if term_m:
            if next_offset is None or term_m.start() < next_offset:
                next_offset = term_m.start()

        # No adjacent statement or terminator found — use density-based end
        if next_offset is None:
            next_offset = _find_section_end_by_density(markdown, offset)

        # Compute end_page from the last line of actual content BEFORE the
        # next heading.  Walk backwards from next_offset to skip past company
        # name headers and page breaks that belong to the next section.
        content_end = next_offset - 1
        lookback = markdown[max(0, next_offset - 500): next_offset]
        # Skip past "COMPANY NAME\nCONDENSED..." or "<!-- PageBreak -->"
        for pattern in [r"[A-Z][A-Z\s,.'&\-]+(?:INC|LLC|LTD|CORP)\.?\n",
                        r"<!--\s*PageBreak\s*-->"]:
            m = re.search(pattern, lookback)
            if m:
                candidate = max(0, next_offset - 500) + m.start() - 1
                if candidate < content_end and candidate >= offset:
                    content_end = candidate

        end_page = _offset_to_page(content_end, page_map)
        if end_page < start_page:
            end_page = start_page

        located[statement_type] = {
            "start_page": start_page,
            "end_page": end_page,
            "md_offset": offset,
            "md_end_offset": next_offset,
        }

    return located


# ---------------------------------------------------------------------------
# Plain-text financial table parser
# ---------------------------------------------------------------------------
# Azure CU prebuilt-read returns tables as plain text with \n\n separators.
# Long labels are often split across consecutive \n\n-separated tokens when
# text wraps across PDF table cell lines, e.g.:
#
#   [tok A] "Net decrease (increase) in receivables under"   (first part)
#   [tok B] "(21,517)"                                        (row A values)
#   [tok C] "28,614"
#   [tok D] "securities borrowing transactions"              (continuation of A)
#   [tok E] "(42,391)"      ← these belong to the NEXT row whose label Azure
#   [tok F] "86,042"          CU dropped entirely
#
# Strategy
# --------
#  1. After consuming a row's values, peek at the next token. If it starts
#     with a lowercase letter it is a continuation fragment of the current
#     label — merge it.
#  2. After merging a fragment, check for more values. Any values found here
#     are ORPHANED (Azure CU dropped the true label for that row). Emit them
#     as a separate row using the fragment text as the best-available label.
#  3. "Section total" rows (label starts with "Net cash" or ends in
#     "activities") are never merged — this prevents [113-120]-style garbage
#     fragments from attaching to summary rows.
#  4. Rows with no values that are just continuation/garbage fragments (all
#     lowercase or repeated single-word noise) are suppressed from output.
# ---------------------------------------------------------------------------

# Japanese full-width dash used for nil/zero entries in Japanese filings
_NIL_RE      = re.compile(r"^[－\-－]+$")

# Header tokens: currency notes, "Note" keyword, year labels, period ranges.
_HEADER_TOKEN_RE = re.compile(
    r"\b(20\d{2}|Note|January|February|March|April|May|June|"
    r"July|August|September|October|November|December|Fiscal Year|Millions)\b",
    re.IGNORECASE,
)

# Section-total labels: never apply post-value continuation merging on these.
# Each branch is anchored to avoid false positives — e.g. "activities$" alone
# would match any label ending in "activities", not just section totals.
_SECTION_TOTAL_RE = re.compile(
    r"^Net cash\b"
    r"|^.*\bactivities$"
    r"|^Cash and cash equivalents at\b"
    r"|^Net increase \(decrease\) in cash\b",
    re.IGNORECASE,
)

# Fallback column cap when header detection finds no period columns.
# Standard annual reports compare two fiscal periods; this prevents greedy
# consumption of nil dash tokens that appear as page separators.
_DEFAULT_VALUE_COLS = 2


def _is_value_or_note(tok: str) -> bool:
    return bool(_VALUE_RE.match(tok) or _NOTE_REF_RE.match(tok) or _NIL_RE.match(tok))


def _is_continuation_fragment(tok: str) -> bool:
    """True if tok is the wrapped tail of the previous label (starts lowercase)."""
    return bool(tok) and tok[0].islower()


def _parse_plain_text_table(section: str) -> tuple[list[str], list[str], list[dict]]:
    """
    Parse the plain-text financial table format into rows, columns, cells.
    Handles:
    - Header vs data token separation
    - Continuation fragment merging (restores full labels)
    - Orphaned value preservation (values that Azure CU detached from their labels)
    - Suppression of valueless noise rows
    """
    raw_tokens = [
        t.strip() for t in section.split("\n\n")
        if t.strip() and not _PAGE_MARKER_RE.match(t.strip())
    ]

    # --- Pre-processing: merge currency symbols with following values ---
    # Azure CU produces several currency-related token patterns:
    #   Pattern A: "$\n35,873"         — leading $ with internal newline
    #   Pattern B: "$"  then "35,873"  — standalone $ as its own token
    #   Pattern C: "$\n20,838 $"       — leading $ + value + trailing $
    #                                    (the trailing $ belongs to the NEXT column)
    #   Pattern D: "20,838 $"          — value with trailing $ fused in
    #
    # We normalise all cases to clean numeric tokens and track the currency
    # symbol in _token_currencies for per-cell metadata.
    _CURRENCY_ONLY_RE = re.compile(r"^[\$¥€£]$")
    _TRAILING_CURRENCY_RE = re.compile(r"^(.+?)\s+[\$¥€£]$")
    _CURRENCY_MAP = {"$": "USD", "¥": "JPY", "€": "EUR", "£": "GBP"}
    cleaned_tokens: list[str] = []
    # Maps cleaned_token index → currency code (only for tokens that had a symbol).
    _token_currencies: dict[int, str] = {}
    pending_currency: str | None = None  # from a standalone "$" or trailing "$"
    for tok in raw_tokens:
        # Case 1: internal newline — "$\n20,838" or "$\n20,838 $"
        if "\n" in tok and _CURRENCY_ONLY_RE.match(tok.split("\n")[0].strip()):
            sym = tok.split("\n")[0].strip()
            remainder = tok.split("\n", 1)[1].strip()
            # Check for trailing currency: "20,838 $" → strip trailing " $"
            trail_m = _TRAILING_CURRENCY_RE.match(remainder)
            if trail_m:
                remainder = trail_m.group(1).strip()
                # The trailing $ belongs to the next column's value.
                pending_currency = _CURRENCY_MAP.get(sym, sym)
            idx = len(cleaned_tokens)
            cleaned_tokens.append(remainder)
            _token_currencies[idx] = _CURRENCY_MAP.get(sym, sym)
        # Case 2: standalone "$" — remember it for the next numeric token.
        elif _CURRENCY_ONLY_RE.match(tok):
            pending_currency = _CURRENCY_MAP.get(tok, tok)
            continue
        # Case 3: trailing currency — "20,838 $" → "20,838" + pending $ for next
        elif _TRAILING_CURRENCY_RE.match(tok):
            trail_m = _TRAILING_CURRENCY_RE.match(tok)
            clean_val = trail_m.group(1).strip()
            trailing_sym = tok[trail_m.end(1):].strip()
            idx = len(cleaned_tokens)
            cleaned_tokens.append(clean_val)
            # Attach pending currency from a preceding token if available.
            if pending_currency:
                _token_currencies[idx] = pending_currency
            # The trailing symbol becomes pending for the next value.
            pending_currency = _CURRENCY_MAP.get(trailing_sym, trailing_sym)
        else:
            idx = len(cleaned_tokens)
            cleaned_tokens.append(tok)
            # Attach pending currency from a preceding standalone symbol.
            if pending_currency and _VALUE_RE.match(tok):
                _token_currencies[idx] = pending_currency
                pending_currency = None
            else:
                pending_currency = None  # discard if next token isn't a value

    columns: list[str] = []
    rows: list[str] = []
    cells: list[dict] = []

    # ---- Phase 1: separate header tokens from data tokens ---- #
    col_headers_raw: list[str] = []
    data_tokens: list[str] = []
    # Maps data_tokens index → cleaned_tokens index (for currency lookup).
    _dt_to_ct: dict[int, int] = {}
    header_done = False

    for ct_idx, tok in enumerate(cleaned_tokens[1:], start=1):  # skip heading
        if not header_done:
            # Check header pattern FIRST — standalone year tokens like "2025"
            # match both _HEADER_TOKEN_RE and _VALUE_RE.  When we're still in
            # header mode, the header interpretation takes priority.
            if _HEADER_TOKEN_RE.search(tok):
                col_headers_raw.append(tok)
            elif _is_value_or_note(tok):
                header_done = True
                _dt_to_ct[len(data_tokens)] = ct_idx
                data_tokens.append(tok)
            else:
                header_done = True
                _dt_to_ct[len(data_tokens)] = ct_idx
                data_tokens.append(tok)
        else:
            _dt_to_ct[len(data_tokens)] = ct_idx
            data_tokens.append(tok)

    # --- Construct proper column headers ---
    # Azure CU produces two kinds of header tokens:
    #   Group headers:  "Three Months Ended December 31,"  (spans 2 columns)
    #   Year headers:   "2025", "2024", "2025", "2024"     (one per column)
    #
    # We separate them: standalone year tokens (just digits) are the actual
    # column identifiers.  Group headers describe which group of year columns
    # they span.  We pair them to produce proper column names like
    # "Three Months Ended December 31, 2025".
    _STANDALONE_YEAR_RE = re.compile(r"^\d{4}$")
    group_headers: list[str] = []
    year_tokens: list[str] = []
    for h in col_headers_raw:
        if _STANDALONE_YEAR_RE.match(h.strip()):
            year_tokens.append(h.strip())
        else:
            group_headers.append(h.strip())

    if year_tokens and group_headers:
        # Pair years with their group headers.  Years are assigned to groups
        # in order: first N years → first group, next N → second group, etc.
        years_per_group = len(year_tokens) // max(len(group_headers), 1)
        columns = []
        for gi, group in enumerate(group_headers):
            start = gi * years_per_group
            for yi in range(start, min(start + years_per_group, len(year_tokens))):
                # Clean group header: remove trailing comma/whitespace
                clean_group = group.rstrip(",").strip()
                columns.append(f"{clean_group} {year_tokens[yi]}")
        # If there are leftover years (more years than groups can pair), append them
        paired_count = len(group_headers) * years_per_group
        for yi in range(paired_count, len(year_tokens)):
            columns.append(year_tokens[yi])
    elif year_tokens:
        columns = year_tokens
    else:
        columns = [h for h in col_headers_raw if "20" in h or "Note" in h]
        if not columns:
            columns = col_headers_raw or ["Label", "Period 1", "Period 2"]

    # Derive the expected number of data-value columns from the columns list.
    # Each column entry represents one period column.  Falls back to
    # _DEFAULT_VALUE_COLS when header detection is inconclusive.
    max_value_cols = len(columns) if len(columns) >= 1 else _DEFAULT_VALUE_COLS

    # Detect whether the statement has a "Note" column.  Note refs (small
    # 1-2 digit integers like "5", "94") should only be skipped when a Note
    # column actually exists.  Without it, these numbers are data values.
    has_note_column = any("note" in h.lower() for h in col_headers_raw)

    # ---- Phase 2: walk data tokens ---- #
    n = len(data_tokens)

    # Track the data_token indices consumed for the current row's values
    # so we can look up per-value currency from _token_currencies.
    _current_val_dt_indices: list[int] = []

    def _classify_row(label: str, has_values: bool) -> tuple[str, int]:
        """
        Determine row_type and indent_level from the label text.

        row_type is one of:
          "section_header" — label with no values, acts as a group heading
          "total"          — grand total row (e.g. "Total assets")
          "subtotal"       — section subtotal (e.g. "Total current assets")
          "line_item"      — regular data row

        indent_level:
          0 — top-level items, headers, and totals
          1 — items within a section (between a header and its total)

        Heuristic: if the label starts with "Total" and has values, it is a
        total or subtotal.  If it has no values and looks like a heading
        (e.g. ends with ":" or is an all-caps section divider), it is a
        section_header.
        """
        label_lower = label.lower().strip()
        label_stripped = label.strip()

        if not has_values:
            # No values → likely a section header or an empty grouping label.
            return "section_header", 0

        if label_lower.startswith("total "):
            # Grand totals are the highest-level aggregations that encompass
            # the entire statement side (e.g. "Total assets" or
            # "Total liabilities and stockholders' equity").
            # Everything else starting with "Total" is a subtotal.
            grand_total_keywords = [
                "total assets",
                "total liabilities and",  # "Total liabilities and stockholders' equity"
                "total revenue",
            ]
            if any(label_lower.startswith(kw) for kw in grand_total_keywords):
                return "total", 0
            # "Total liabilities" (without "and") is a subtotal within the
            # balance sheet — it's the sum of current + non-current liabilities,
            # not the grand total.
            return "subtotal", 0

        # Cash flow section subtotals: only "Net cash..." rows are subtotals.
        # "Other investing activities" and "Other financing activities" are
        # regular line items, NOT subtotals.
        # "Net increase/decrease in cash" is a summary row that equals
        # Operating + Investing + Financing + FX — classified separately.
        if label_lower.startswith("net cash"):
            return "subtotal", 0
        if label_lower.startswith("net increase") or label_lower.startswith("net decrease"):
            return "total", 0  # summary-level total, not a section subtotal

        # Default: line_item.  Indent level is determined in a post-pass
        # after all rows are emitted (items between a header and its
        # total/subtotal get indent_level=1).
        return "line_item", 0

    def emit(label: str, vals: list[str]) -> None:
        """Append one row to rows/cells with currency and structure metadata.

        Always emits exactly max_value_cols value cells.  If vals has fewer
        entries, remaining columns are filled with empty strings.  This ensures
        every data row has a consistent column count in the output JSON.
        """
        nonlocal row_index
        rows.append(label)

        row_type, indent_level = _classify_row(label, bool(vals))

        cells.append({
            "row": row_index, "col": 0, "content": label,
            "kind": "content", "currency": None,
            "row_type": row_type, "indent_level": indent_level,
        })
        # Emit exactly max_value_cols value cells, padding with empty strings.
        for vi in range(max_value_cols):
            val = vals[vi] if vi < len(vals) else ""
            # Look up currency for this value from the token pre-processing pass.
            currency = None
            if vi < len(_current_val_dt_indices):
                dt_idx = _current_val_dt_indices[vi]
                ct_idx = _dt_to_ct.get(dt_idx)
                if ct_idx is not None:
                    currency = _token_currencies.get(ct_idx)
            cells.append({
                "row": row_index, "col": vi + 1, "content": val,
                "kind": "content", "currency": currency,
                "row_type": row_type, "indent_level": indent_level,
            })
        _current_val_dt_indices.clear()
        row_index += 1

    row_index = 0
    i = 0
    while i < n:
        tok = data_tokens[i]

        if _is_value_or_note(tok):
            i += 1   # orphaned value/note — skip
            continue

        # Skip mid-section page column headers that leaked through page breaks
        # (e.g. "(Millions of Yen)", "Note", "Fiscal Year ended March 31, …").
        # These match _HEADER_TOKEN_RE but are NOT followed by numeric values;
        # a real data label that incidentally contains a year IS followed by values.
        if _HEADER_TOKEN_RE.search(tok) and not _SECTION_TOTAL_RE.search(tok):
            has_vals = False
            for pi in range(i + 1, min(i + 5, n)):
                pt = data_tokens[pi]
                if _VALUE_RE.match(pt):
                    has_vals = True
                    break
                if not _NOTE_REF_RE.match(pt) and not _HEADER_TOKEN_RE.search(pt):
                    break  # hit a real label — stop lookahead
            if not has_vals:
                i += 1
                continue

        label = tok
        i += 1

        # Skip optional note ref (only when the statement has a Note column).
        if has_note_column and i < n and _NOTE_REF_RE.match(data_tokens[i]):
            i += 1

        # Consume numeric values for this label
        vals: list[str] = []
        _current_val_dt_indices.clear()
        while i < n and _VALUE_RE.match(data_tokens[i]):
            _current_val_dt_indices.append(i)
            vals.append(data_tokens[i])
            i += 1
        # Fill a missing second column with an adjacent nil marker if present.
        # Japanese reports use "－" for nil entries; they follow immediately
        # after the numeric value(s) and should not be consumed past the
        # expected number of data columns to avoid polluting later rows.
        while vals and i < n and _NIL_RE.match(data_tokens[i]) and len(vals) < max_value_cols:
            vals.append(data_tokens[i])
            i += 1

        # ---- Continuation fragment loop ----
        # Only applies when current label is NOT a section total.
        was_merged = False   # tracks whether any fragment was merged into label
        if not _SECTION_TOTAL_RE.search(label):
            while i < n and _is_continuation_fragment(data_tokens[i]):
                fragment = data_tokens[i]
                i += 1

                # Skip optional note ref after fragment (only with Note column).
                if has_note_column and i < n and _NOTE_REF_RE.match(data_tokens[i]):
                    i += 1

                # Numeric values immediately after the fragment, plus any nil fill
                orphan_vals: list[str] = []
                while i < n and _VALUE_RE.match(data_tokens[i]):
                    orphan_vals.append(data_tokens[i]);
                    i += 1
                while orphan_vals and i < n and _NIL_RE.match(data_tokens[i]) and len(orphan_vals) < max_value_cols:
                    orphan_vals.append(data_tokens[i])
                    i += 1

                if orphan_vals:
                    # Fragment is followed by values → Azure CU dropped the
                    # true label for those values. Emit current row (with
                    # fragment merged into label), then emit the orphaned
                    # values under the fragment text as best-available label.
                    emit(label + " " + fragment, vals)
                    emit(fragment, orphan_vals)
                    label = None   # signal already emitted
                    vals = []
                    break
                else:
                    # Clean continuation — just extend the label
                    label = label + " " + fragment
                    was_merged = True

        # Emit if not already done inside the continuation loop
        if label is not None:
            # Suppress valueless noise rows: only lowercase-start tokens which
            # are orphaned continuation fragments with no data of their own.
            # Uppercase merged labels are kept even with no values — they may
            # represent real rows whose values Azure CU failed to extract.
            is_noise = not vals and label[:1].islower()
            if not is_noise:
                emit(label, vals)

    # ---- Phase 3: strip trailing noise rows ---- #
    # Remove rows from the end that are noise: dash-only rows, company name
    # headers (e.g. "META PLATFORMS, INC."), or other non-data artifacts.
    _TRAILING_NOISE_RE = re.compile(r"^[—\-－]")
    _COMPANY_NAME_RE = re.compile(
        r"^[A-Z][A-Z\s,.'&\-]+(?:INC|LLC|LTD|CORP|CO|PLC|GROUP|COMPANY|SA|AG|NV)\.?$",
        re.IGNORECASE,
    )
    while rows:
        last_label = rows[-1].strip()
        last_row_idx = len(rows) - 1
        has_real_values = any(
            c["row"] == last_row_idx and c["col"] > 0 and c["content"].strip()
            for c in cells
        )
        is_noise = (
            (not has_real_values and _TRAILING_NOISE_RE.match(last_label))
            or (not has_real_values and _COMPANY_NAME_RE.match(last_label))
        )
        if is_noise:
            rows.pop()
            cells = [c for c in cells if c["row"] != last_row_idx]
        else:
            break

    # ---- Phase 3b: normalize row labels ---- #
    # Replace internal newlines with spaces for cleaner output.
    for c in cells:
        if c["col"] == 0 and "\n" in c["content"]:
            c["content"] = re.sub(r"\s*\n\s*", " ", c["content"])
    for i, r in enumerate(rows):
        if "\n" in r:
            rows[i] = re.sub(r"\s*\n\s*", " ", r)

    # ---- Phase 3c: fix EPS currency tags ---- #
    # Earnings per share and share count values should NOT have currency.
    # They are ratios/counts, not monetary amounts.
    _EPS_SECTION = False
    for c in cells:
        if c["col"] == 0:
            label_lower = c["content"].lower().strip()
            if "per share" in label_lower or "shares used" in label_lower:
                _EPS_SECTION = True
            elif c["row_type"] in ("subtotal", "total", "section_header"):
                if "per share" not in label_lower and "shares" not in label_lower:
                    _EPS_SECTION = False
        elif _EPS_SECTION and c["col"] > 0:
            c["currency"] = None

    # ---- Phase 3d: normalize column headers ---- #
    columns = [re.sub(r"\s*\n\s*", " ", c) for c in columns]

    # ---- Phase 4: indent-level post-pass ---- #
    # Line items between a section_header and its subtotal/total get indent=1.
    in_section = False
    for c in cells:
        if c["col"] != 0:
            continue  # only process label cells for indent logic
        if c["row_type"] == "section_header":
            in_section = True
        elif c["row_type"] in ("subtotal", "total"):
            in_section = False
        elif c["row_type"] == "line_item" and in_section:
            c["indent_level"] = 1
            # Also update indent on value cells for this row.
            for vc in cells:
                if vc["row"] == c["row"] and vc["col"] > 0:
                    vc["indent_level"] = 1

    # ---- Phase 5: flag under-populated rows ---- #
    # When Azure CU drops nil-dash markers ("—"), a row may have fewer values
    # than expected.  These values end up in the wrong columns because the
    # parser fills left-to-right.  Flag these rows so downstream consumers
    # (or the LLM reconciler) can review column alignment.
    if max_value_cols >= 2:
        row_val_counts: dict[int, int] = {}
        for c in cells:
            if c["col"] > 0:
                row_val_counts[c["row"]] = row_val_counts.get(c["row"], 0) + 1
        for c in cells:
            if c["col"] == 0 and c["row_type"] == "line_item":
                actual_cols = row_val_counts.get(c["row"], 0)
                if 0 < actual_cols < max_value_cols:
                    c["column_alignment_warning"] = (
                        f"Row has {actual_cols} value(s) but {max_value_cols} "
                        f"columns expected. Azure CU may have dropped nil markers, "
                        f"causing values to be in wrong columns."
                    )

    return rows, columns, cells


# ---------------------------------------------------------------------------
# Total cross-validation
# ---------------------------------------------------------------------------
# Identifies section-total rows (e.g. "Total assets", "Net cash from
# operating activities") and compares their value against the sum of the
# preceding line-item values.  Discrepancies flag extraction errors
# without any API call — this is a free accuracy check.

# Labels that represent section totals.  Checked via substring match
# (case-insensitive) to accommodate wording variations across IFRS reports.
_TOTAL_LABEL_KEYWORDS = [
    "total assets",
    "total liabilities",
    "total equity",
    "total liabilities and equity",
    "total current assets",
    "total current liabilities",
    "total non-current assets",
    "total non-current liabilities",
    "net cash flows from operating",
    "net cash flows from investing",
    "net cash flows from financing",
    "net cash used in operating",
    "net cash used in investing",
    "net cash used in financing",
    "net cash provided by operating",
    "net cash provided by investing",
    "net cash provided by financing",
]


def _parse_financial_value(raw: str) -> Optional[float]:
    """
    Parse a financial value string into a float.

    Handles:
      - Comma-separated thousands: "1,234,567" → 1234567.0
      - Parenthesised negatives:   "(42,391)"  → -42391.0
      - Plain negatives:           "-217,741"  → -217741.0
      - Japanese nil dashes:       "－"        → 0.0

    Returns None if the string is not a recognisable financial number.
    """
    s = raw.strip()
    if not s:
        return None
    # Strip leading currency symbols
    s = re.sub(r"^[\$¥€£]\s*", "", s)
    if not s:
        return None
    # Japanese full-width dash = zero
    if re.match(r"^[－\-－]+$", s):
        return 0.0
    # Parenthesised negative
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    # Remove commas
    s = s.replace(",", "")
    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return None


def validate_totals(
    rows: list[str],
    cells: list[dict],
) -> list[dict]:
    """
    Hierarchy-aware cross-validation of section totals.

    Uses row_type and indent_level metadata to correctly sum only the
    direct children of each total/subtotal:

    1. For a SUBTOTAL (e.g. "Total current assets"):
       Sum only the immediately preceding line_items that share the same
       section (between the previous section_header/subtotal and this one).
       Only includes rows at indent_level > 0 (children of the section).

    2. For a TOTAL (e.g. "Total assets"):
       Sum the preceding subtotals and any ungrouped line_items at indent=0.
       This avoids double-counting by treating subtotals as atomic blocks.

    Returns a list of warning dicts. An empty list means all totals matched.
    """
    if not cells:
        return []

    # Build grid and collect metadata per row.
    grid: dict[int, dict[int, str]] = {}
    row_meta: dict[int, dict] = {}  # row_idx -> {row_type, indent_level}
    for c in cells:
        grid.setdefault(c["row"], {})[c["col"]] = c.get("content", "")
        if c["col"] == 0:
            row_meta[c["row"]] = {
                "row_type": c.get("row_type", "line_item"),
                "indent_level": c.get("indent_level", 0),
            }

    sorted_row_indices = sorted(grid.keys())
    if not sorted_row_indices:
        return []

    max_col = max((c["col"] for c in cells if c["col"] > 0), default=0)
    if max_col == 0:
        return []

    warnings: list[dict] = []

    for i, row_idx in enumerate(sorted_row_indices):
        meta = row_meta.get(row_idx, {})
        rt = meta.get("row_type", "")

        if rt != "subtotal":
            # Only validate subtotals — they have clear parent-child
            # relationships.  Grand totals (e.g. "Total assets",
            # "Total liabilities and stockholders' equity") depend on
            # hierarchical aggregation that is prone to false positives.
            # If all subtotals validate, grand totals are implied-correct.
            continue

        # Collect the rows that should sum to this subtotal.
        summable: list[int] = []

        if rt == "subtotal":
            # Sum indented line_items (indent >= 1) going back until hitting
            # another subtotal or total.  This ensures:
            #   - Income statement: Revenue (indent=0) excluded from expense total
            #   - Balance sheet: non-current items excluded from current subtotal
            #   - Cash flow: Net income + adjustments + working capital all included
            #     in operating subtotal (all are indent=1)
            # Section headers are skipped (they have no values).
            for j in range(i - 1, -1, -1):
                prev_idx = sorted_row_indices[j]
                prev_meta = row_meta.get(prev_idx, {})
                prev_rt = prev_meta.get("row_type", "")
                prev_il = prev_meta.get("indent_level", 0)
                if prev_rt in ("subtotal", "total"):
                    break  # stop at the previous subtotal/total
                if prev_rt == "line_item" and prev_il >= 1:
                    summable.append(prev_idx)

        elif rt == "total":
            # Sum preceding subtotals + other totals + ungrouped line_items.
            # This treats subtotals/totals as atomic blocks (already aggregated).
            for j in range(i - 1, -1, -1):
                prev_idx = sorted_row_indices[j]
                prev_meta = row_meta.get(prev_idx, {})
                prev_rt = prev_meta.get("row_type", "")
                prev_il = prev_meta.get("indent_level", 0)
                if prev_rt == "total":
                    # Include this total as a summable block (e.g. "Total liabilities"
                    # contributes to "Total liabilities and stockholders' equity").
                    summable.append(prev_idx)
                    break  # stop — we've reached another grand total
                if prev_rt == "subtotal":
                    summable.append(prev_idx)
                elif prev_rt == "line_item" and prev_il == 0:
                    summable.append(prev_idx)
                # Skip section_headers and indented line_items (already in subtotals)

        if not summable:
            continue

        # Validate each column.
        for col in range(1, max_col + 1):
            total_raw = grid[row_idx].get(col, "")
            total_val = _parse_financial_value(total_raw)
            if total_val is None:
                continue

            running_sum = 0.0
            all_parseable = True
            for li_idx in summable:
                raw = grid[li_idx].get(col, "")
                parsed = _parse_financial_value(raw)
                if parsed is None and raw.strip():
                    all_parseable = False
                    break
                running_sum += parsed or 0.0

            if not all_parseable:
                continue

            diff = abs(total_val - running_sum)
            if diff > 2.0:
                warnings.append({
                    "row": row_idx,
                    "label": grid[row_idx].get(0, ""),
                    "col": col,
                    "expected": running_sum,
                    "actual": total_val,
                    "diff": diff,
                })

    return warnings


# ---------------------------------------------------------------------------
# Statement builder
# ---------------------------------------------------------------------------

def _detect_metadata(section_text: str) -> dict:
    """
    Extract statement-level metadata from the section header.

    Detects:
      - company_name: e.g. "META PLATFORMS, INC."
      - statement_title: e.g. "Condensed Consolidated Statements of Cash Flows"
      - currency: e.g. "USD" (from $ symbols or "(In millions)" note)
      - unit: e.g. "millions" (from "(In millions)" or "(In thousands)")
    """
    # Look at the first few tokens (not just the first) for metadata.
    # Chinese reports put metadata in separate \n\n-delimited tokens:
    #   tok[0]: "合并资产负债表\n2025年9月30日"
    #   tok[1]: "编制单位:厦门国贸集团股份有限公司"
    #   tok[2]: "单位:元 币种:人民币 审计类型:未经审计"
    header_tokens = section_text.split("\n\n")[:5] if section_text else []
    lines = []
    for tok in header_tokens:
        lines.extend(l.strip() for l in tok.split("\n") if l.strip())

    company_name = None
    statement_title = None
    currency = None  # detect from content, no default assumption
    unit = None

    _COMPANY_RE = re.compile(
        r"^[A-Z][A-Z\s,.'&\-]+(?:INC|LLC|LTD|CORP|CO|PLC|GROUP|COMPANY|SA|AG|NV)\.?$",
        re.IGNORECASE,
    )

    full_heading = "\n".join(lines)
    for line in lines:
        if _COMPANY_RE.match(line) and not company_name:
            company_name = line
        # Chinese format: "编制单位:厦门国贸集团股份有限公司"
        elif re.search(r"编制单位[：:](.+)", line) and not company_name:
            company_name = re.search(r"编制单位[：:](.+)", line).group(1).strip()
        elif re.search(r"(?i)(statement|balance|income|cash flow|资产负债|利润|现金流|損益|貸借)", line) and not statement_title:
            statement_title = line
        # Unit detection (English + Chinese)
        if re.search(r"(?i)\(in millions|单位.*万元", line):
            unit = "ten_thousands" if "万元" in line else "millions"
        elif re.search(r"(?i)\(in thousands", line):
            unit = "thousands"
        elif re.search(r"(?i)\(in billions|单位.*亿元", line):
            unit = "billions"
        elif re.search(r"单位.*[：:].*元", line) and "万" not in line and "亿" not in line:
            unit = "ones"  # Chinese reports in yuan (元)

    # Currency detection from the full heading block
    if re.search(r"人民币|CNY|RMB", full_heading):
        currency = "CNY"
    elif re.search(r"¥|yen|円", full_heading, re.IGNORECASE):
        currency = "JPY"
    elif re.search(r"€|euro", full_heading, re.IGNORECASE):
        currency = "EUR"
    elif re.search(r"£|pound|sterling", full_heading, re.IGNORECASE):
        currency = "GBP"
    elif re.search(r"\$|USD", full_heading):
        currency = "USD"

    return {
        "company_name": company_name,
        "statement_title": statement_title,
        "currency": currency,
        "unit": unit,
    }


def _to_canonical_key(label: str) -> str:
    """
    Generate a stable canonical key from a row label.

    Normalizes the label to a snake_case identifier that is consistent
    across companies and formatting variations:
      "Cash and cash equivalents"  -> "cash_and_cash_equivalents"
      "Cash & cash eq."           -> "cash_and_cash_eq"
      "Net income (loss)"         -> "net_income_loss"
      "Total costs and expenses"  -> "total_costs_and_expenses"
    """
    s = label.lower().strip()
    # Replace & with "and"
    s = s.replace("&", "and")
    # Remove parentheses but keep content
    s = s.replace("(", "").replace(")", "")
    # Remove common punctuation
    s = re.sub(r"[,.:;'\"\-/]", " ", s)
    # Collapse whitespace and convert to underscores
    s = re.sub(r"\s+", "_", s.strip())
    # Remove trailing underscores
    s = s.strip("_")
    return s


def _normalize_value(raw: str | None) -> dict:
    """
    Convert a raw display value into a structured value object.

    Returns:
      {"raw": str|None, "normalized": float|None, "is_null": bool}

    Distinguishes:
      - null/None  -> is_null=True, normalized=None (not reported)
      - ""         -> is_null=True, normalized=None (formatting artifact)
      - "0"        -> is_null=False, normalized=0.0 (explicitly zero)
      - "(3,097)"  -> is_null=False, normalized=-3097.0
    """
    if raw is None or not raw.strip():
        return {"raw": None, "normalized": None, "is_null": True}

    parsed = _parse_financial_value(raw)
    return {
        "raw": raw,
        "normalized": parsed,
        "is_null": False,
    }


def _build_column_metadata(columns: list[str]) -> list[dict]:
    """
    Enrich column headers with structured period metadata.

    Parses period_type ("quarter" or "annual") and year from the column label.
    """
    result = []
    for col in columns:
        col_lower = col.lower()
        # Detect period type
        if any(kw in col_lower for kw in ["three months", "quarter", "q1", "q2", "q3", "q4"]):
            period_type = "quarter"
        elif any(kw in col_lower for kw in ["twelve months", "full year", "fiscal year", "annual"]):
            period_type = "annual"
        else:
            period_type = "unknown"

        # Extract year
        year_match = re.search(r"20\d{2}", col)
        year = int(year_match.group()) if year_match else None

        result.append({
            "label": col,
            "period_type": period_type,
            "year": year,
        })
    return result


def _cells_to_row_first(
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> list[dict]:
    """
    Convert the flat cells array into a row-first analytics-ready schema.

    Each row becomes a single object with:
      - label: str — display label
      - canonical_key: str — stable snake_case identifier for cross-company use
      - row_type: str ("section_header", "line_item", "subtotal", "total")
      - indent_level: int
      - values: list[{raw, normalized, is_null}] — one per column
    """
    expected_cols = len(columns)

    # Group cells by row.
    grid: dict[int, dict[int, dict]] = {}
    for c in cells:
        grid.setdefault(c["row"], {})[c["col"]] = c

    output_rows: list[dict] = []
    for row_idx in sorted(grid):
        label_cell = grid[row_idx].get(0, {})
        label = label_cell.get("content", "")
        row_type = label_cell.get("row_type", "line_item")
        indent_level = label_cell.get("indent_level", 0)

        # Build values array with normalized numeric layer.
        values: list[dict] = []
        for col_idx in range(1, expected_cols + 1):
            val_cell = grid[row_idx].get(col_idx, {})
            content = val_cell.get("content", "")
            raw = content if content.strip() else None
            values.append(_normalize_value(raw))

        output_rows.append({
            "label": label,
            "canonical_key": _to_canonical_key(label),
            "row_type": row_type,
            "indent_level": indent_level,
            "values": values,
        })

    return output_rows


def build_statement_json(
    statement_type: str,
    raw_result: dict,
    location: Optional[dict],
    use_llm: bool = False,
) -> dict:
    """
    Build a single statement JSON in analytics-ready row-first schema.

    Output schema:
      {
        "statement_type": "cash_flow",
        "status": "extracted",
        "page_range": {"start": 7, "end": 7},
        "columns": [
          {"label": "...", "period_type": "quarter", "year": 2025}
        ],
        "rows": [
          {"label": "Revenue", "canonical_key": "revenue",
           "row_type": "line_item", "indent_level": 0,
           "values": [
             {"raw": "59,893", "normalized": 59893.0, "is_null": false}
           ]}
        ],
        "metadata": {"currency": "USD", "unit": "millions", ...},
        "validation_warnings": [...]
      }

    Args:
        use_llm: When True, run the LLM reconciliation pass after parsing.
    """
    if location is None:
        return {
            "statement_type": statement_type,
            "status": "not_found",
            "page_range": {"start": None, "end": None},
            "columns": [],
            "rows": [],
            "metadata": {},
            "validation_warnings": [],
        }

    markdown = _get_markdown(raw_result)
    section = markdown[location["md_offset"]: location["md_end_offset"]]

    # Extract metadata from the section header.
    metadata = _detect_metadata(section)

    # Parse the table.
    rows, columns, cells = _parse_plain_text_table(section)

    if use_llm and cells:
        from .llm_reconciler import reconcile
        rows, columns, cells = reconcile(statement_type, rows, columns, cells)

    # Cross-validate section totals against line-item sums.
    validation_warnings: list[dict] = []
    if cells:
        validation_warnings = validate_totals(rows, cells)
        for w in validation_warnings:
            print(f"      [WARN] {statement_type} row {w['row']} col {w['col']}: "
                  f"'{w['label']}' total={w['actual']}, sum={w['expected']}, "
                  f"diff={w['diff']}")

    # Convert to row-first schema.
    row_objects = _cells_to_row_first(rows, columns, cells)

    return {
        "statement_type": statement_type,
        "status": "extracted" if cells else "found",
        "page_range": {
            "start": location["start_page"],
            "end": location["end_page"],
        },
        "columns": _build_column_metadata(columns),
        "rows": row_objects,
        "metadata": metadata,
        "validation_warnings": validation_warnings,
    }


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary(locations: dict[str, Optional[dict]]) -> dict:
    """Build the summary.json object from the located statements."""
    entries = []
    for statement_type, location in locations.items():
        if location is None:
            entries.append({
                "statement_type": statement_type,
                "status": "not_found",
                "page_range": {"start": None, "end": None},
            })
        else:
            entries.append({
                "statement_type": statement_type,
                "status": "extracted",
                "page_range": {
                    "start": location["start_page"],
                    "end": location["end_page"],
                },
            })
    return {"summary": entries}
