"""Tests for Stage 3: Extract — full-markdown search + anti-contamination merging."""
import pytest
from extractor.stages.contracts import CandidateStatement, SelectResult, ScoredCandidate
from extractor.stages.extract import (
    _find_heading_offset,
    _merge_continuation_tables,
    locate_table,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate(stype, title_raw="", page_start=0, page_end=0) -> CandidateStatement:
    return CandidateStatement(
        statement_type=stype,
        title_raw=title_raw,
        page_start=page_start,
        page_end=page_end,
    )


# ---------------------------------------------------------------------------
# _find_heading_offset (full-markdown search)
# ---------------------------------------------------------------------------

class TestFindHeadingOffset:
    def test_finds_known_heading_pattern(self):
        md = "   Some preamble   Consolidated Balance Sheet <table>...</table>"
        offset = _find_heading_offset("balance_sheet", "", md)
        assert offset is not None
        assert "Balance Sheet" in md[offset:offset + 50]

    def test_finds_chinese_heading(self):
        md = "Preamble 合并资产负债表 <table>data</table>"
        offset = _find_heading_offset("balance_sheet", "Some Other Title", md)
        assert offset is not None

    def test_falls_back_to_title_raw(self):
        md = "Some Custom Heading For Statement <table>data</table>"
        offset = _find_heading_offset("balance_sheet", "Some Custom Heading For Statement", md)
        assert offset is not None

    def test_returns_none_when_no_table(self):
        md = "Just plain text, no tables"
        offset = _find_heading_offset("balance_sheet", "Balance Sheet", md)
        assert offset is None

    def test_returns_none_when_no_heading(self):
        md = "Random text <table>data</table>"
        offset = _find_heading_offset("balance_sheet", "", md)
        assert offset is None


# ---------------------------------------------------------------------------
# _merge_continuation_tables (content-based anti-contamination)
# ---------------------------------------------------------------------------

class TestMergeContinuationTables:
    def test_merges_adjacent_tables(self):
        md = "<table>t1</table>  <table>t2</table>"
        end, count = _merge_continuation_tables(
            "balance_sheet", md, 0, md.index("</table>") + len("</table>"),
        )
        assert count == 2
        assert end == len(md)

    def test_stops_at_other_statement_heading(self):
        md = "<table>t1</table> INCOME STATEMENT <table>t2</table>"
        first_end = md.index("</table>") + len("</table>")
        end, count = _merge_continuation_tables(
            "balance_sheet", md, 0, first_end,
        )
        assert count == 1
        assert end == first_end

    def test_stops_at_note_heading(self):
        md = "<table>t1</table> Notes to the Financial Statements <table>t2</table>"
        first_end = md.index("</table>") + len("</table>")
        end, count = _merge_continuation_tables(
            "balance_sheet", md, 0, first_end,
        )
        assert count == 1

    def test_stops_at_parent_company_marker(self):
        md = "<table>t1</table> 母公司 <table>t2</table>"
        first_end = md.index("</table>") + len("</table>")
        end, count = _merge_continuation_tables(
            "cash_flow", md, 0, first_end,
        )
        assert count == 1

    def test_stops_at_max_continuation(self):
        md = "<table>t1</table><table>t2</table><table>t3</table><table>t4</table>"
        first_end = md.index("</table>") + len("</table>")
        end, count = _merge_continuation_tables(
            "balance_sheet", md, 0, first_end,
        )
        assert count == 3  # max is 3

    def test_stops_on_non_continuation_labels(self):
        md = '<table>t1</table><table><td>revenue</td><td>100</td></table>'
        first_end = md.index("</table>") + len("</table>")
        end, count = _merge_continuation_tables(
            "balance_sheet", md, 0, first_end,
        )
        assert count == 1  # "revenue" doesn't belong in a balance sheet


# ---------------------------------------------------------------------------
# locate_table integration
# ---------------------------------------------------------------------------

class TestLocateTable:
    def test_finds_table_with_heading(self):
        md = "Preamble\nConsolidated Balance Sheet\n<table><tr><td>Assets</td></tr></table>"
        c = _candidate("balance_sheet", "Consolidated Balance Sheet", 1, 1)
        result = locate_table("balance_sheet", c, md, [])
        assert result is not None
        assert result["md_offset"] >= 0
        assert result["md_end_offset"] > result["md_offset"]

    def test_returns_none_when_not_found(self):
        md = "No financial data here at all."
        c = _candidate("balance_sheet", "Something", 1, 1)
        result = locate_table("balance_sheet", c, md, [])
        assert result is None

    def test_finds_table_even_with_wrong_page_range(self):
        """The key test: locator says page 1, but real table is later in markdown."""
        md = (
            "Page 1 summary table <table><td>Summary</td></table>\n"
            "... lots of other content ...\n"
            "合并资产负债表\n"
            "<table><tr><td>Total Assets</td><td>1000</td></tr></table>"
        )
        c = _candidate("balance_sheet", "Balance Sheet", 1, 1)
        result = locate_table("balance_sheet", c, md, [])
        assert result is not None
        # Should find the real balance sheet heading, not the summary table
        assert "合并资产负债表" in md[result["md_offset"]:result["md_offset"] + 50]
