"""
Tests for extractor/statement_detector.py — covers:
  Fix 1 (this round): $ sign token merging in parser
  Fix 2 (this round): US GAAP section terminators
  Fix 3 (this round): Two-tier heading detection (exact + keyword)
  Fix 5: Dynamic column count detection
  Fix 6: Cross-validate totals
  Fix 7: Regex precedence in _SECTION_TOTAL_RE
"""

import re

from extractor.statement_detector import (
    _parse_plain_text_table,
    _SECTION_TOTAL_RE,
    _NOTES_TERMINATOR_RE,
    _VALUE_RE,
    _score_candidate,
    _KEYWORD_SCORES,
    _MIN_KEYWORD_SCORE,
    _tier1_heading_offsets,
    _tier2_keyword_offsets,
    _all_heading_offsets,
    _has_data_nearby,
    validate_totals,
    _parse_financial_value,
    HEADINGS,
)


# ===========================================================================
# Fix 7: _SECTION_TOTAL_RE regex precedence
# ===========================================================================

class TestSectionTotalRegex:
    """Verify anchored regex branches match correctly after the fix."""

    def test_matches_net_cash(self):
        assert _SECTION_TOTAL_RE.search("Net cash flows from operating activities")

    def test_matches_label_ending_in_activities(self):
        assert _SECTION_TOTAL_RE.search("Net cash flows from investing activities")

    def test_matches_cash_equivalents(self):
        assert _SECTION_TOTAL_RE.search("Cash and cash equivalents at end of period")

    def test_matches_financing_activities(self):
        assert _SECTION_TOTAL_RE.search("Net cash flows from financing activities")

    def test_does_not_match_mid_label_activities(self):
        """The word 'activities' in the middle of a label should not match."""
        assert not _SECTION_TOTAL_RE.search("Income from activities related to banking")

    def test_matches_net_increase_decrease(self):
        assert _SECTION_TOTAL_RE.search("Net increase (decrease) in cash and cash equivalents")


# ===========================================================================
# Fix 1 (this round): $ sign token merging
# ===========================================================================

class TestCurrencyTokenMerging:
    """Parser merges standalone $ tokens with the following numeric value."""

    def test_dollar_newline_value_merged(self):
        """'$\\n35,873' is normalised to '35,873' and parsed as a value."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Cash and cash equivalents\n\n"
            "$\n35,873\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        # Should have one row with "Cash and cash equivalents" and value "35,873"
        assert len(rows) >= 1
        assert rows[0] == "Cash and cash equivalents"
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 1
        assert val_cells[0]["content"] == "35,873"

    def test_standalone_dollar_followed_by_value(self):
        """A standalone '$' token followed by a numeric token is merged."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Revenue\n\n"
            "$\n\n"
            "59,893\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert len(rows) >= 1
        assert rows[0] == "Revenue"
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 1
        assert val_cells[0]["content"] == "59,893"

    def test_multiple_dollar_values_in_row(self):
        """Multiple $-prefixed values in a row are all parsed correctly."""
        section = (
            "Cash Flow\n\n"
            "December 31, 2025\n\n"
            "December 31, 2024\n\n"
            "Net income\n\n"
            "$\n22,768\n\n"
            "$\n20,838\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert rows[0] == "Net income"
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 2
        assert val_cells[0]["content"] == "22,768"
        assert val_cells[1]["content"] == "20,838"

    def test_value_re_matches_dollar_prefixed(self):
        """_VALUE_RE accepts values with optional leading $."""
        assert _VALUE_RE.match("$35,873")
        assert _VALUE_RE.match("$ 35,873")
        assert _VALUE_RE.match("$(42,391)")
        assert _VALUE_RE.match("35,873")
        assert _VALUE_RE.match("(42,391)")

    def test_non_dollar_values_unaffected(self):
        """Regular numeric tokens without $ are still parsed normally."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Marketable securities\n\n"
            "45,719\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert rows[0] == "Marketable securities"
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert val_cells[0]["content"] == "45,719"


class TestParseFinancialValueCurrency:
    """_parse_financial_value strips currency symbols before parsing."""

    def test_dollar_prefix(self):
        assert _parse_financial_value("$35,873") == 35873.0

    def test_dollar_negative_parens(self):
        assert _parse_financial_value("$(42,391)") == -42391.0

    def test_yen_prefix(self):
        assert _parse_financial_value("¥1,000") == 1000.0

    def test_euro_prefix(self):
        assert _parse_financial_value("€500") == 500.0


# ===========================================================================
# Fix 2 (this round): US GAAP section terminators
# ===========================================================================

class TestNotesTerminatorRegex:
    """_NOTES_TERMINATOR_RE catches both IFRS and US GAAP section boundaries."""

    def test_notes_to(self):
        assert _NOTES_TERMINATOR_RE.search("[Notes to the Financial Statements]")

    def test_comprehensive_income(self):
        assert _NOTES_TERMINATOR_RE.search("Consolidated Statement of Comprehensive Income")

    def test_changes_in_equity(self):
        assert _NOTES_TERMINATOR_RE.search("Statement of Changes in Stockholders' Equity")

    def test_segment_results(self):
        assert _NOTES_TERMINATOR_RE.search("Segment Results")

    def test_segment_information(self):
        assert _NOTES_TERMINATOR_RE.search("Segment Information")

    def test_reconciliation_of_gaap(self):
        assert _NOTES_TERMINATOR_RE.search("Reconciliation of GAAP to Non-GAAP Results")

    def test_supplemental_is_not_terminator(self):
        """'Supplemental cash flow data' is part of cash flow, NOT a terminator."""
        assert not _NOTES_TERMINATOR_RE.search("Supplemental cash flow data")

    def test_regular_label_no_match(self):
        """Normal financial labels should NOT trigger a terminator match."""
        assert not _NOTES_TERMINATOR_RE.search("Total current assets")
        assert not _NOTES_TERMINATOR_RE.search("Net cash from operating activities")


# ===========================================================================
# Fix 3 (this round): Two-tier heading detection
# ===========================================================================

class TestScoreCandidate:
    """_score_candidate sums keyword weights for matching terms."""

    def test_balance_sheet_keywords(self):
        keywords = _KEYWORD_SCORES["balance_sheet"]
        score = _score_candidate("Consolidated Balance Sheet", keywords)
        assert score >= 3.0  # "balance sheet" = 3.0

    def test_cash_flow_keywords(self):
        keywords = _KEYWORD_SCORES["cash_flow"]
        score = _score_candidate("Statement of Cash Flows", keywords)
        assert score >= 3.0  # "cash flows" = 3.0

    def test_income_statement_keywords(self):
        keywords = _KEYWORD_SCORES["income_statement"]
        score = _score_candidate("Consolidated Statement of Income", keywords)
        assert score >= 3.0  # "statement of income" = 3.0

    def test_narrative_text_low_score(self):
        """Narrative text mentioning one keyword should score below threshold."""
        keywords = _KEYWORD_SCORES["balance_sheet"]
        score = _score_candidate("The company reported equity growth this quarter", keywords)
        assert score < _MIN_KEYWORD_SCORE

    def test_nonstandard_heading_high_score(self):
        """A non-standard heading with enough keywords should score high."""
        keywords = _KEYWORD_SCORES["balance_sheet"]
        score = _score_candidate("Statement of Assets and Liabilities", keywords)
        # "assets" (2.0) + "liabilities" (2.0) = 4.0
        assert score >= _MIN_KEYWORD_SCORE


class TestTier1HeadingOffsets:
    """Tier 1 exact heading matching."""

    def test_finds_standard_heading(self):
        markdown = "Some intro text\n\n123,456\n\nConsolidated Balance Sheet\n\n100,000\n\n200,000"
        offsets = _tier1_heading_offsets(markdown, HEADINGS["balance_sheet"])
        assert len(offsets) == 1

    def test_no_match_without_data(self):
        """A heading without nearby numeric data is rejected (likely TOC)."""
        markdown = "Table of Contents\n\nConsolidated Balance Sheet\n\nSee next page for details"
        offsets = _tier1_heading_offsets(markdown, HEADINGS["balance_sheet"])
        assert offsets == []

    def test_priority_order(self):
        """More specific heading is preferred over shorter fallback."""
        markdown = (
            "Condensed Consolidated Balance Sheets\n\n100,000\n\n"
            "Balance Sheet\n\n200,000"
        )
        offsets = _tier1_heading_offsets(markdown, HEADINGS["balance_sheet"])
        assert len(offsets) == 1
        # Should match the more specific "Condensed Consolidated Balance Sheets"
        assert markdown[offsets[0]:].startswith("Condensed")


class TestTier2KeywordOffsets:
    """Tier 2 keyword-based semantic scoring for non-standard headings."""

    def test_finds_nonstandard_balance_sheet_heading(self):
        """A non-standard heading with enough keywords is detected."""
        markdown = (
            "Some narrative text about the company.\n\n"
            "Statement of Assets and Liabilities and Equity\n\n"
            "100,000\n\n200,000\n\n"
        )
        offsets = _tier2_keyword_offsets(markdown, "balance_sheet")
        assert len(offsets) >= 1

    def test_ignores_narrative_with_few_keywords(self):
        """Narrative text with only one keyword should not match."""
        markdown = (
            "The company owns significant assets in multiple countries.\n\n"
            "This paragraph discusses risk factors.\n\n"
        )
        offsets = _tier2_keyword_offsets(markdown, "balance_sheet")
        assert offsets == []


class TestAllHeadingOffsets:
    """_all_heading_offsets integrates both tiers."""

    def test_tier1_preferred_when_available(self):
        """When Tier 1 matches, Tier 2 is not needed."""
        markdown = "Consolidated Balance Sheet\n\n100,000\n\n200,000"
        offsets = _all_heading_offsets(markdown, HEADINGS["balance_sheet"], "balance_sheet")
        assert len(offsets) >= 1

    def test_tier2_fallback_when_tier1_fails(self):
        """When no exact heading matches, Tier 2 keyword scoring kicks in."""
        markdown = (
            "Some preamble text.\n\n"
            "Unaudited Statement of Assets and Liabilities and Equity\n\n"
            "100,000\n\n200,000\n\n300,000\n\n"
        )
        # Tier 1 won't match "Unaudited Statement of Assets and Liabilities"
        offsets = _all_heading_offsets(markdown, HEADINGS["balance_sheet"], "balance_sheet")
        assert len(offsets) >= 1


# ===========================================================================
# Fix 5: Dynamic column count
# ===========================================================================

class TestDynamicColumnCount:
    """_parse_plain_text_table derives column count from header tokens."""

    def test_two_period_headers(self):
        """Standard two-period report gets max_value_cols=2."""
        section = (
            "Consolidated Balance Sheet\n\n"
            "Note  Fiscal Year ended December 31, 2023\n\n"
            "Fiscal Year ended December 31, 2024\n\n"
            "Total assets\n\n"
            "1,000,000\n\n"
            "2,000,000\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert len(columns) == 2
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 2

    def test_three_period_headers(self):
        """Three-period comparative statement should capture all three values.

        Header tokens must contain a standalone year (e.g. '2022') for
        _HEADER_TOKEN_RE to recognise them — 'FY2022' would fail the \\b
        word-boundary check.
        """
        section = (
            "Income Statement\n\n"
            "Fiscal Year ended 2022\n\n"
            "Fiscal Year ended 2023\n\n"
            "Fiscal Year ended 2024\n\n"
            "Revenue\n\n"
            "100\n\n"
            "200\n\n"
            "300\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert len(columns) == 3
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 3
        assert val_cells[0]["content"] == "100"
        assert val_cells[1]["content"] == "200"
        assert val_cells[2]["content"] == "300"

    def test_fallback_when_no_year_headers(self):
        """When no year-like header is found, falls back to 2 columns."""
        section = (
            "Balance Sheet\n\n"
            "Label\n\n"
            "Amount\n\n"
            "Revenue\n\n"
            "100\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        assert len(rows) >= 1

    def test_four_period_meta_style(self):
        """Four-period report (Q4 + FY for two years) captures all four values."""
        section = (
            "Income Statement\n\n"
            "Three Months Ended December 31,\n\n"
            "Twelve Months Ended December 31,\n\n"
            "2025\n\n"
            "2024\n\n"
            "2025\n\n"
            "2024\n\n"
            "Revenue\n\n"
            "59,893\n\n"
            "48,385\n\n"
            "200,966\n\n"
            "164,501\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 4


# ===========================================================================
# Per-cell currency detection
# ===========================================================================

class TestPerCellCurrency:
    """Parser tracks currency symbols and attaches them to value cells."""

    def test_dollar_currency_on_value_cells(self):
        """Values from '$\\n35,873' tokens get currency='USD'."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Cash and cash equivalents\n\n"
            "$\n35,873\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert len(val_cells) == 1
        assert val_cells[0]["currency"] == "USD"

    def test_no_currency_on_plain_values(self):
        """Values without a $ prefix get currency=None."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Marketable securities\n\n"
            "45,719\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        val_cells = [c for c in cells if c["row"] == 0 and c["col"] > 0]
        assert val_cells[0]["currency"] is None

    def test_label_cells_have_no_currency(self):
        """Label cells (col=0) always have currency=None."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Revenue\n\n"
            "$\n59,893\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        label_cell = [c for c in cells if c["row"] == 0 and c["col"] == 0][0]
        assert label_cell["currency"] is None

    def test_mixed_currency_and_plain_in_same_statement(self):
        """Some rows have $, others don't — currency tracked per-cell."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Revenue\n\n"
            "$\n59,893\n\n"
            "Cost of revenue\n\n"
            "10,905\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        revenue_val = [c for c in cells if c["row"] == 0 and c["col"] == 1][0]
        cost_val = [c for c in cells if c["row"] == 1 and c["col"] == 1][0]
        assert revenue_val["currency"] == "USD"
        assert cost_val["currency"] is None


# ===========================================================================
# Row type and indent level metadata
# ===========================================================================

class TestRowTypeAndIndent:
    """Parser classifies rows and assigns indent levels."""

    def test_section_header_detected(self):
        """A label with no values is classified as section_header."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Costs and expenses:\n\n"
            "Cost of revenue\n\n"
            "10,905\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        header_cell = [c for c in cells if c["content"] == "Costs and expenses:"][0]
        assert header_cell["row_type"] == "section_header"

    def test_line_item_detected(self):
        """A regular data row is classified as line_item."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Revenue\n\n"
            "59,893\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        revenue_cell = [c for c in cells if c["content"] == "Revenue"][0]
        assert revenue_cell["row_type"] == "line_item"

    def test_subtotal_detected(self):
        """'Total costs and expenses' is classified as subtotal."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Total costs and expenses\n\n"
            "35,148\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        total_cell = [c for c in cells if c["content"] == "Total costs and expenses"][0]
        assert total_cell["row_type"] == "subtotal"

    def test_grand_total_detected(self):
        """'Total assets' is classified as total (grand total)."""
        section = (
            "Balance Sheet\n\n"
            "December 31, 2025\n\n"
            "Total assets\n\n"
            "366,021\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        total_cell = [c for c in cells if c["content"] == "Total assets"][0]
        assert total_cell["row_type"] == "total"

    def test_indent_level_within_section(self):
        """Line items between a section_header and subtotal get indent_level=1."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Costs and expenses:\n\n"
            "Cost of revenue\n\n"
            "10,905\n\n"
            "Research and development\n\n"
            "17,136\n\n"
            "Total costs and expenses\n\n"
            "28,041\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        cost_cell = [c for c in cells if c["content"] == "Cost of revenue" and c["col"] == 0][0]
        rd_cell = [c for c in cells if c["content"] == "Research and development" and c["col"] == 0][0]
        total_cell = [c for c in cells if c["content"] == "Total costs and expenses" and c["col"] == 0][0]

        assert cost_cell["indent_level"] == 1
        assert rd_cell["indent_level"] == 1
        assert total_cell["indent_level"] == 0  # subtotal is not indented

    def test_top_level_items_not_indented(self):
        """Items outside a section header block stay at indent_level=0."""
        section = (
            "Income Statement\n\n"
            "December 31, 2025\n\n"
            "Revenue\n\n"
            "59,893\n\n"
            "Income from operations\n\n"
            "24,745\n\n"
        )
        rows, columns, cells = _parse_plain_text_table(section)
        rev_cell = [c for c in cells if c["content"] == "Revenue" and c["col"] == 0][0]
        inc_cell = [c for c in cells if c["content"] == "Income from operations" and c["col"] == 0][0]
        assert rev_cell["indent_level"] == 0
        assert inc_cell["indent_level"] == 0


# ===========================================================================
# Fix 6: Cross-validate totals
# ===========================================================================

class TestParseFinancialValue:
    """_parse_financial_value handles all common financial number formats."""

    def test_plain_integer(self):
        assert _parse_financial_value("12345") == 12345.0

    def test_comma_separated(self):
        assert _parse_financial_value("1,234,567") == 1234567.0

    def test_parenthesised_negative(self):
        assert _parse_financial_value("(42,391)") == -42391.0

    def test_negative_sign(self):
        assert _parse_financial_value("-217,741") == -217741.0

    def test_decimal(self):
        assert _parse_financial_value("12.34") == 12.34

    def test_nil_dash(self):
        assert _parse_financial_value("－") == 0.0

    def test_empty_string(self):
        assert _parse_financial_value("") is None

    def test_non_numeric(self):
        assert _parse_financial_value("hello") is None


class TestValidateTotals:
    """validate_totals uses hierarchy-aware logic to check totals."""

    def _make_cells(self, data):
        """Build cells from [(row, label, vals, row_type, indent_level)].

        Short form: (row, label, vals) defaults to line_item/indent=1.
        """
        cells = []
        for entry in data:
            row_idx, label, vals = entry[0], entry[1], entry[2]
            row_type = entry[3] if len(entry) > 3 else "line_item"
            indent = entry[4] if len(entry) > 4 else (1 if row_type == "line_item" else 0)
            cells.append({
                "row": row_idx, "col": 0, "content": label,
                "kind": "content", "row_type": row_type, "indent_level": indent,
            })
            for vi, val in enumerate(vals):
                cells.append({
                    "row": row_idx, "col": vi + 1, "content": val,
                    "kind": "content", "row_type": row_type, "indent_level": indent,
                })
        rows = [d[1] for d in data]
        return rows, cells

    def test_subtotal_sums_indented_children(self):
        """Subtotal should equal sum of indented line_items in its section."""
        rows, cells = self._make_cells([
            (0, "Current assets:", [], "section_header", 0),
            (1, "Cash", ["100", "200"], "line_item", 1),
            (2, "Securities", ["30", "50"], "line_item", 1),
            (3, "Total current assets", ["130", "250"], "subtotal", 0),
        ])
        warnings = validate_totals(rows, cells)
        assert warnings == []

    def test_subtotal_mismatch_warns(self):
        """Subtotal that doesn't match its children triggers a warning."""
        rows, cells = self._make_cells([
            (0, "Current assets:", [], "section_header", 0),
            (1, "Cash", ["100", "200"], "line_item", 1),
            (2, "Securities", ["30", "50"], "line_item", 1),
            (3, "Total current assets", ["999", "250"], "subtotal", 0),
        ])
        warnings = validate_totals(rows, cells)
        assert len(warnings) >= 1
        assert warnings[0]["col"] == 1

    def test_total_sums_subtotals_not_children(self):
        """Grand total sums subtotals + ungrouped items, not individual children."""
        rows, cells = self._make_cells([
            (0, "Current assets:", [], "section_header", 0),
            (1, "Cash", ["100"], "line_item", 1),
            (2, "Securities", ["50"], "line_item", 1),
            (3, "Total current assets", ["150"], "subtotal", 0),
            (4, "Goodwill", ["50"], "line_item", 0),   # ungrouped
            (5, "Total assets", ["200"], "total", 0),   # = 150 + 50
        ])
        warnings = validate_totals(rows, cells)
        assert warnings == []

    def test_negative_values_handled(self):
        """Parenthesised negatives are parsed and summed correctly."""
        rows, cells = self._make_cells([
            (0, "Section:", [], "section_header", 0),
            (1, "Income", ["500"], "line_item", 1),
            (2, "Loss", ["(200)"], "line_item", 1),
            (3, "Total current assets", ["300"], "subtotal", 0),
        ])
        warnings = validate_totals(rows, cells)
        assert warnings == []

    def test_empty_cells_no_crash(self):
        """Empty cells list returns no warnings and does not crash."""
        warnings = validate_totals([], [])
        assert warnings == []

    def test_no_totals_found(self):
        """When no total rows exist, returns empty list."""
        rows, cells = self._make_cells([
            (0, "Revenue", ["100"], "line_item", 1),
            (1, "Cost", ["50"], "line_item", 1),
        ])
        warnings = validate_totals(rows, cells)
        assert warnings == []
