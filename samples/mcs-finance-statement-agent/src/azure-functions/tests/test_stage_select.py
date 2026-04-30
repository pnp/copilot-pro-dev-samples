"""Tests for Stage 2: Select — scoring-based statement selection."""
import pytest
from extractor.stages.contracts import (
    AnalyzeResult,
    CandidateStatement,
)
from extractor.stages.select import score_statement, run_select


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate(
    stype="balance_sheet",
    title_raw="",
    title_english="",
    page_start=0,
    page_end=0,
    is_consolidated=None,
) -> CandidateStatement:
    return CandidateStatement(
        statement_type=stype,
        title_raw=title_raw,
        title_english=title_english,
        page_start=page_start,
        page_end=page_end,
        is_consolidated=is_consolidated,
    )


def _analyze_result(candidates: list[CandidateStatement]) -> AnalyzeResult:
    return AnalyzeResult(
        candidates=candidates,
        markdown="",
        pages=[],
        page_map=[],
    )


# ---------------------------------------------------------------------------
# Score tests
# ---------------------------------------------------------------------------

class TestScoreStatement:
    def test_ghost_match_returns_negative_1000(self):
        c = _candidate(page_start=0, page_end=0, title_raw="Balance Sheet")
        assert score_statement(c, "balance_sheet") == -1000

    def test_empty_title_returns_negative_500(self):
        c = _candidate(page_start=10, page_end=11)
        assert score_statement(c, "balance_sheet") == -500

    def test_consolidated_flag_adds_20(self):
        c = _candidate(
            title_raw="Balance Sheet",
            page_start=10, page_end=11,
            is_consolidated=True,
        )
        score_with = score_statement(c, "balance_sheet")
        c2 = _candidate(
            title_raw="Balance Sheet",
            page_start=10, page_end=11,
            is_consolidated=False,
        )
        score_without = score_statement(c2, "balance_sheet")
        assert score_with - score_without == 20

    def test_primary_heading_pattern_adds_50(self):
        c = _candidate(
            title_raw="Consolidated Statement of Financial Position",
            page_start=85, page_end=86,
            is_consolidated=True,
        )
        score = score_statement(c, "balance_sheet")
        # Should get: +50 (pattern) +20 (is_consolidated) +15 (consolidated kw) +10 (type kw) +5 (page>=80) = 100
        assert score >= 95

    def test_non_primary_pattern_subtracts_100(self):
        c = _candidate(
            title_raw="Note D.5 Balance Sheet Details",
            page_start=90, page_end=91,
        )
        score = score_statement(c, "balance_sheet")
        assert score < -50

    def test_parent_company_disqualified(self):
        c = _candidate(
            title_raw="母公司资产负债表",
            page_start=50, page_end=51,
        )
        score = score_statement(c, "balance_sheet")
        assert score < -50

    def test_chinese_consolidated_scores_high(self):
        c = _candidate(
            title_raw="合并资产负债表",
            page_start=45, page_end=46,
            is_consolidated=True,
        )
        score = score_statement(c, "balance_sheet")
        assert score > 50

    def test_temporal_marker_adds_30(self):
        c = _candidate(
            title_raw="Balance Sheet for the year ended December 31, 2025",
            page_start=40, page_end=41,
        )
        score = score_statement(c, "balance_sheet")
        assert score >= 30

    def test_incomplete_page_range_penalty(self):
        c = _candidate(
            title_raw="Cash Flow Statement",
            page_start=10, page_end=0,
        )
        score = score_statement(c, "cash_flow")
        assert score < score_statement(
            _candidate(title_raw="Cash Flow Statement", page_start=10, page_end=12),
            "cash_flow",
        )


# ---------------------------------------------------------------------------
# Selection tests
# ---------------------------------------------------------------------------

class TestRunSelect:
    def test_selects_highest_scoring_candidate(self):
        candidates = [
            _candidate("balance_sheet", "Note D.5 Details", "", 90, 91),
            _candidate("balance_sheet", "Consolidated Balance Sheet", "", 85, 86, True),
        ]
        result = run_select(_analyze_result(candidates), ["balance_sheet"])
        assert "balance_sheet" in result.selected
        assert result.selected["balance_sheet"].title_raw == "Consolidated Balance Sheet"

    def test_rejects_all_below_threshold(self):
        candidates = [
            _candidate("balance_sheet", "Note D.5", "", 0, 0),
        ]
        result = run_select(_analyze_result(candidates), ["balance_sheet"])
        assert "balance_sheet" not in result.selected
        assert len(result.rejected.get("balance_sheet", [])) == 1

    def test_selects_one_per_type(self):
        candidates = [
            _candidate("balance_sheet", "Consolidated Balance Sheet", "", 85, 86, True),
            _candidate("income_statement", "Consolidated Income Statement", "", 87, 88, True),
            _candidate("cash_flow", "Consolidated Cash Flow", "", 89, 91, True),
        ]
        result = run_select(
            _analyze_result(candidates),
            ["balance_sheet", "income_statement", "cash_flow"],
        )
        assert len(result.selected) == 3

    def test_empty_candidates_for_type(self):
        result = run_select(
            _analyze_result([]),
            ["balance_sheet"],
        )
        assert "balance_sheet" not in result.selected
        assert result.scores.get("balance_sheet") == []

    def test_consolidated_beats_parent(self):
        """Xiamen ITG scenario: consolidated should beat parent company."""
        candidates = [
            _candidate("cash_flow", "母公司现金流量表", "", 55, 57),
            _candidate("cash_flow", "合并现金流量表", "", 50, 53, True),
        ]
        result = run_select(_analyze_result(candidates), ["cash_flow"])
        assert "cash_flow" in result.selected
        assert "合并" in result.selected["cash_flow"].title_raw
