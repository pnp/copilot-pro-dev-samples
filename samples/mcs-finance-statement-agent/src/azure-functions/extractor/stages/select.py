"""
Stage 2: Select — scoring-based statement selection.

Adapted from select_v2.py (experiments repo). Each candidate gets a score
based on how likely it is to be the primary statutory statement. Highest
score wins per statement type. Below -50 threshold: rejected.

Scoring signals:
  +50  Primary heading pattern (consolidated + temporal markers)
  +30  Temporal markers ("for the year ended", "as at")
  +20  is_consolidated flag
  +15  "Consolidated" keyword (any language)
  +10  Statement type keyword in raw title
  +5   Page >= 80 (financial statements section, not MD&A)
  -20  Single-page early page without consolidated markers
  -30  Incomplete page range (start but no end)
  -100 Non-primary patterns (notes, bridges, segments, parent company)
  -500 Empty title
  -1000 Ghost match (no page range)
"""
import logging
import re
from typing import Optional

from .contracts import (
    AnalyzeResult,
    CandidateStatement,
    ScoredCandidate,
    SelectResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_PRIMARY_HEADING_PATTERNS = [
    r"(?:consolidated\s+)?(?:statement|balance sheet|income statement).*(?:for the (?:year|period)|as at|as of)",
    r"consolidated\s+statement\s+of\s+(?:financial position|profit|income|cash|comprehensive)",
    r"consolidated\s+balance\s+sheet",
    r"consolidated\s+(?:income|p&l)\s+statement",
    r"consolidated\s+(?:statement\s+of\s+)?cash\s+flow",
    r"合并资产负债表",
    r"合并利润表",
    r"合并现金流量表",
    r"連結貸借対照表",
    r"連結損益計算書",
    r"連結キャッシュ・フロー計算書",
    r"bilan\s+consoli",
    r"compte\s+de\s+r[ée]sultat\s+consoli",
    r"tableau\s+des\s+flux\s+de\s+tr[ée]sorerie",
]

_NON_PRIMARY_PATTERNS = [
    r"\bnote\s+\d",
    r"\bnotes?\s+to\b",
    r"\bsegment\b",
    r"\breconciliation\b",
    r"\bbridge\b",
    r"\bebitda\b",
    r"\bnon.?gaap\b",
    r"\badjusted\b",
    r"\bsummary\b.*\b(?:aplng|subsidiary|joint venture)\b",
    r"\bparent\s+(?:company|entity)\b",
    r"母公司",
    r"\bunderlying\b",
    r"\b(?:c|d|e|f|g)\.\d+\b",
    r"\bcontinued\b",
    r"\bproperty,?\s+plant",
    r"\bintangible\s+assets\b",
    r"\bincome\s+tax\s+expense\b",
    r"\binterest.bearing\s+liabilities\b",
    r"\bderivatives?\b",
    r"\bdisclosure\s+statement\b",
    r"\bfinancial\s+summary\b",
]

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "balance_sheet": [r"financial position", r"balance sheet", r"资产负债", r"貸借対照", r"bilan"],
    "income_statement": [r"profit or loss", r"income statement", r"利润表", r"損益", r"compte de r"],
    "cash_flow": [r"cash flow", r"现金流量", r"キャッシュ", r"flux de tr"],
}

# Minimum score for a candidate to be selected (below this = rejected)
_MIN_SCORE_THRESHOLD = -50


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_statement(stmt: CandidateStatement, statement_type: str) -> float:
    """Score a candidate statement. Higher = more likely primary."""
    score = 0.0

    title_raw = (stmt.title_raw or "").strip()
    title_en = (stmt.title_english or "").strip()
    combined_title = f"{title_raw} {title_en}".lower()
    page_start = stmt.page_start or 0
    page_end = stmt.page_end or 0

    # --- Disqualifiers ---

    # Ghost match (no page range) — penalize but don't kill if title is good
    # CU Locator sometimes returns consolidated statements without page ranges.
    # The extract stage searches full markdown, so missing pages is recoverable.
    if page_start == 0 and page_end == 0:
        if stmt.is_consolidated and title_raw:
            score -= 40  # Penalty but still selectable if title scores high
        else:
            return -1000

    # Incomplete page range
    if page_start > 0 and page_end == 0:
        score -= 30

    # Empty title
    if not title_raw and not title_en:
        return -500

    # Non-primary patterns (notes, segments, bridges, parent company)
    for pattern in _NON_PRIMARY_PATTERNS:
        if re.search(pattern, combined_title, re.IGNORECASE):
            score -= 100
            break

    # --- Positive signals ---

    # is_consolidated flag
    if stmt.is_consolidated is True:
        score += 20

    # Primary heading pattern match
    for pattern in _PRIMARY_HEADING_PATTERNS:
        if re.search(pattern, combined_title, re.IGNORECASE):
            score += 50
            break

    # Temporal markers
    if re.search(r"for the (?:year|period|half.year|quarter)", combined_title, re.IGNORECASE):
        score += 30
    if re.search(r"as (?:at|of)\s+\d", combined_title, re.IGNORECASE):
        score += 30

    # "Consolidated" keyword (any language)
    if re.search(r"consoli|合并|連結|consolidé", combined_title, re.IGNORECASE):
        score += 15

    # Statement type keyword in title
    for kw in _TYPE_KEYWORDS.get(statement_type, []):
        if re.search(kw, combined_title, re.IGNORECASE):
            score += 10
            break

    # Penalty for single-page early match without consolidated markers
    if page_start == page_end and page_start < 60:
        if not re.search(r"consoli|statutory|合并|連結", combined_title, re.IGNORECASE):
            score -= 20

    # Prefer statements in the financial statements section
    if page_start >= 80:
        score += 5

    return score


def run_select(
    analyze_result: AnalyzeResult,
    requested_types: list[str],
) -> SelectResult:
    """Run Stage 2: score all candidates and select best per type."""
    # Group candidates by type
    by_type: dict[str, list[CandidateStatement]] = {}
    for c in analyze_result.candidates:
        if c.statement_type in requested_types:
            by_type.setdefault(c.statement_type, []).append(c)

    selected: dict[str, CandidateStatement] = {}
    rejected: dict[str, list[ScoredCandidate]] = {}
    all_scores: dict[str, list[ScoredCandidate]] = {}

    for stype in requested_types:
        candidates = by_type.get(stype, [])
        if not candidates:
            all_scores[stype] = []
            rejected[stype] = []
            continue

        scored = []
        for c in candidates:
            s = score_statement(c, stype)
            reason = None
            if s <= _MIN_SCORE_THRESHOLD:
                if s <= -1000:
                    reason = "ghost_match_no_pages"
                elif s <= -500:
                    reason = "empty_title"
                else:
                    reason = "below_score_threshold"
            scored.append(ScoredCandidate(candidate=c, score=s, rejection_reason=reason))

        scored.sort(key=lambda x: x.score, reverse=True)
        all_scores[stype] = scored

        best = scored[0]
        if best.score > _MIN_SCORE_THRESHOLD:
            selected[stype] = best.candidate
            rejected[stype] = [sc for sc in scored[1:]]
        else:
            rejected[stype] = scored

        # Logging
        logger.info(
            f"  Stage 2 (Select) {stype}: {len(candidates)} candidates, "
            f"best score={best.score:.0f}"
        )
        if len(scored) > 1:
            runner_up = scored[1]
            logger.info(
                f"    2nd: score={runner_up.score:.0f} "
                f"page {runner_up.candidate.page_start}-{runner_up.candidate.page_end}"
            )

    return SelectResult(selected=selected, rejected=rejected, scores=all_scores)
