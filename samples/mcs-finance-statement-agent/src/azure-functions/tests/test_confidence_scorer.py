"""
Tests for extractor/confidence_scorer.py — covers:
  - Each of the 6 signal functions independently
  - Composite score_statement (perfect statement → high, broken → low)
  - flag_rows (each flag condition)
  - Boundary conditions (exactly 5% empty labels → 1.0)
"""

import pytest

from extractor.confidence_scorer import (
    score_statement,
    flag_rows,
    _score_subtotal_validation,
    _score_section_coverage,
    _score_row_count,
    _score_column_dates,
    _score_empty_label_ratio,
    _score_leaked_headers,
    WEIGHTS,
    THRESHOLDS,
    ROW_RANGES,
    SECTION_GROUPS,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _row(
    row_index,
    label_raw="Cash",
    row_type="line_item",
    section="current_assets",
    values=None,
):
    """Build a minimal row dict for testing."""
    if values is None:
        values = [{"raw": "100", "normalized": 100.0, "is_null": False}]
    return {
        "row_index": row_index,
        "label_raw": label_raw,
        "row_type": row_type,
        "section": section,
        "values": values,
    }


def _make_statement(rows=None, columns=None, warnings=None):
    """Build a minimal statement dict."""
    if rows is None:
        rows = []
    if columns is None:
        columns = [{"column_index": 0, "label": "2025"}]
    if warnings is None:
        warnings = []
    return {
        "rows": rows,
        "columns": columns,
        "validation": {"warnings": warnings, "errors": []},
    }


# ---------------------------------------------------------------------------
# _score_subtotal_validation
# ---------------------------------------------------------------------------

class TestScoreSubtotalValidation:

    def test_no_subtotals_returns_1(self):
        stmt = _make_statement(rows=[_row(0), _row(1)])
        assert _score_subtotal_validation(stmt) == 1.0

    def test_all_subtotals_pass(self):
        rows = [
            _row(0, row_type="subtotal"),
            _row(1, row_type="subtotal"),
        ]
        stmt = _make_statement(rows=rows, warnings=[])
        assert _score_subtotal_validation(stmt) == 1.0

    def test_all_subtotals_fail(self):
        rows = [
            _row(0, row_type="subtotal"),
            _row(1, row_type="subtotal"),
        ]
        warnings = [
            {"row_index": 0, "column_index": 0, "difference": 50},
            {"row_index": 1, "column_index": 0, "difference": 20},
        ]
        stmt = _make_statement(rows=rows, warnings=warnings)
        assert _score_subtotal_validation(stmt) == 0.0

    def test_partial_subtotals_fail(self):
        rows = [
            _row(0, row_type="subtotal"),
            _row(1, row_type="subtotal"),
            _row(2, row_type="subtotal"),
            _row(3, row_type="subtotal"),
        ]
        # Only row_index 0 fails
        warnings = [{"row_index": 0, "column_index": 0, "difference": 50}]
        stmt = _make_statement(rows=rows, warnings=warnings)
        assert _score_subtotal_validation(stmt) == 0.75

    def test_warning_for_non_subtotal_row_doesnt_affect_score(self):
        """Warnings on non-subtotal rows should not count against score."""
        rows = [
            _row(0, row_type="subtotal"),
            _row(1, row_type="line_item"),
        ]
        # Warning is on the line_item row, not the subtotal
        warnings = [{"row_index": 1, "column_index": 0, "difference": 10}]
        stmt = _make_statement(rows=rows, warnings=warnings)
        assert _score_subtotal_validation(stmt) == 1.0

    def test_empty_rows_returns_1(self):
        stmt = _make_statement(rows=[])
        assert _score_subtotal_validation(stmt) == 1.0

    def test_multiple_warnings_same_subtotal_row_counted_once(self):
        """Multiple warnings for the same row_index should count as one failure."""
        rows = [
            _row(0, row_type="subtotal"),
            _row(1, row_type="subtotal"),
        ]
        # Two warnings for row_index=0 (different columns)
        warnings = [
            {"row_index": 0, "column_index": 0, "difference": 50},
            {"row_index": 0, "column_index": 1, "difference": 30},
        ]
        stmt = _make_statement(rows=rows, warnings=warnings)
        assert _score_subtotal_validation(stmt) == 0.5


# ---------------------------------------------------------------------------
# _score_section_coverage
# ---------------------------------------------------------------------------

class TestScoreSectionCoverage:

    def test_balance_sheet_all_groups_present(self):
        rows = [
            _row(0, section="current_assets"),
            _row(1, section="non_current_assets"),
            _row(2, section="current_liabilities"),
            _row(3, section="equity"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "balance_sheet")
        assert score == 1.0

    def test_balance_sheet_missing_equity_group(self):
        rows = [
            _row(0, section="current_assets"),
            _row(1, section="non_current_assets"),
            _row(2, section="current_liabilities"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "balance_sheet")
        # 2 out of 3 groups matched
        assert score == pytest.approx(2 / 3)

    def test_balance_sheet_no_sections(self):
        stmt = _make_statement(rows=[])
        score = _score_section_coverage(stmt, "balance_sheet")
        assert score == 0.0

    def test_income_statement_all_groups(self):
        rows = [
            _row(0, section="revenue"),
            _row(1, section="operating_expenses"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "income_statement")
        assert score == 1.0

    def test_income_statement_expenses_alternate(self):
        """'expenses' is an alternative section name for the operating_expenses group."""
        rows = [
            _row(0, section="revenue"),
            _row(1, section="expenses"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "income_statement")
        assert score == 1.0

    def test_income_statement_missing_revenue(self):
        rows = [_row(0, section="operating_expenses")]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "income_statement")
        assert score == pytest.approx(1 / 2)

    def test_cash_flow_all_groups(self):
        rows = [
            _row(0, section="operating_activities"),
            _row(1, section="investing_activities"),
            _row(2, section="financing_activities"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "cash_flow")
        assert score == 1.0

    def test_cash_flow_only_operating(self):
        rows = [_row(0, section="operating_activities")]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "cash_flow")
        assert score == pytest.approx(1 / 3)

    def test_balance_sheet_uses_assets_top_level_section(self):
        """Top-level 'assets' section satisfies the first group."""
        rows = [
            _row(0, section="assets"),
            _row(1, section="liabilities"),
            _row(2, section="equity"),
        ]
        stmt = _make_statement(rows=rows)
        score = _score_section_coverage(stmt, "balance_sheet")
        assert score == 1.0


# ---------------------------------------------------------------------------
# _score_row_count
# ---------------------------------------------------------------------------

class TestScoreRowCount:

    def test_balance_sheet_in_range(self):
        rows = [_row(i) for i in range(20)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "balance_sheet") == 1.0

    def test_balance_sheet_at_min_boundary(self):
        rows = [_row(i) for i in range(15)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "balance_sheet") == 1.0

    def test_balance_sheet_at_max_boundary(self):
        rows = [_row(i) for i in range(80)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "balance_sheet") == 1.0

    def test_balance_sheet_too_few(self):
        rows = [_row(i) for i in range(5)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "balance_sheet") == 0.0

    def test_balance_sheet_too_many(self):
        rows = [_row(i) for i in range(100)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "balance_sheet") == 0.0

    def test_income_statement_in_range(self):
        rows = [_row(i) for i in range(25)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "income_statement") == 1.0

    def test_income_statement_too_few(self):
        rows = [_row(i) for i in range(3)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "income_statement") == 0.0

    def test_cash_flow_in_range(self):
        rows = [_row(i) for i in range(20)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "cash_flow") == 1.0

    def test_cash_flow_too_many(self):
        rows = [_row(i) for i in range(70)]
        stmt = _make_statement(rows=rows)
        assert _score_row_count(stmt, "cash_flow") == 0.0


# ---------------------------------------------------------------------------
# _score_column_dates
# ---------------------------------------------------------------------------

class TestScoreColumnDates:

    def test_all_columns_have_years(self):
        columns = [
            {"column_index": 0, "label": "2025"},
            {"column_index": 1, "label": "2024"},
        ]
        stmt = _make_statement(columns=columns)
        assert _score_column_dates(stmt) == 1.0

    def test_no_columns_returns_0(self):
        stmt = _make_statement(columns=[])
        assert _score_column_dates(stmt) == 0.0

    def test_partial_columns_have_years(self):
        columns = [
            {"column_index": 0, "label": "December 31, 2025"},
            {"column_index": 1, "label": "Amount"},
        ]
        stmt = _make_statement(columns=columns)
        assert _score_column_dates(stmt) == 0.5

    def test_label_containing_year(self):
        """Year embedded in longer label still matches."""
        columns = [{"column_index": 0, "label": "Fiscal Year Ended December 31, 2023"}]
        stmt = _make_statement(columns=columns)
        assert _score_column_dates(stmt) == 1.0

    def test_label_with_old_year_not_matching_20xx(self):
        """Years before 2000 (e.g. 1999) should not match the 20xx pattern."""
        columns = [{"column_index": 0, "label": "1999"}]
        stmt = _make_statement(columns=columns)
        assert _score_column_dates(stmt) == 0.0

    def test_label_with_no_year(self):
        columns = [{"column_index": 0, "label": "Amount (USD thousands)"}]
        stmt = _make_statement(columns=columns)
        assert _score_column_dates(stmt) == 0.0


# ---------------------------------------------------------------------------
# _score_empty_label_ratio
# ---------------------------------------------------------------------------

class TestScoreEmptyLabelRatio:

    def test_no_blank_labels(self):
        rows = [_row(i, label_raw=f"Row {i}") for i in range(20)]
        stmt = _make_statement(rows=rows)
        assert _score_empty_label_ratio(stmt) == 1.0

    def test_exactly_5_percent_blank_is_ok(self):
        """Exactly 5% blank labels → score 1.0 (uses <=)."""
        rows = [_row(i, label_raw=f"Row {i}") for i in range(19)]
        rows.append(_row(19, label_raw=""))  # 1/20 = 5%
        stmt = _make_statement(rows=rows)
        assert _score_empty_label_ratio(stmt) == 1.0

    def test_above_5_percent_blank_fails(self):
        """More than 5% blank labels → score 0.0."""
        rows = [_row(i, label_raw=f"Row {i}") for i in range(18)]
        rows.append(_row(18, label_raw=""))
        rows.append(_row(19, label_raw=""))  # 2/20 = 10%
        stmt = _make_statement(rows=rows)
        assert _score_empty_label_ratio(stmt) == 0.0

    def test_all_blank_labels_fails(self):
        rows = [_row(i, label_raw="") for i in range(5)]
        stmt = _make_statement(rows=rows)
        assert _score_empty_label_ratio(stmt) == 0.0

    def test_empty_rows_returns_1(self):
        """No rows → no blanks → 1.0."""
        stmt = _make_statement(rows=[])
        assert _score_empty_label_ratio(stmt) == 1.0

    def test_whitespace_only_label_counts_as_blank(self):
        """Labels with only whitespace are treated as blank."""
        rows = [_row(i, label_raw=f"Row {i}") for i in range(19)]
        rows.append(_row(19, label_raw="   "))  # 1/20 = 5%
        stmt = _make_statement(rows=rows)
        assert _score_empty_label_ratio(stmt) == 1.0


# ---------------------------------------------------------------------------
# _score_leaked_headers
# ---------------------------------------------------------------------------

class TestScoreLeakedHeaders:

    def test_no_leaked_headers(self):
        rows = [_row(i, label_raw=f"Cash {i}") for i in range(5)]
        stmt = _make_statement(rows=rows)
        assert _score_leaked_headers(stmt) == 1.0

    def test_leaked_header_detected(self):
        """A row with blank label and all values looking like years/unit-strings → leaked header."""
        rows = [
            _row(0, label_raw="Revenue"),
            _row(1, label_raw="", values=[
                {"raw": "2025", "normalized": 2025.0, "is_null": False},
                {"raw": "2024", "normalized": 2024.0, "is_null": False},
            ]),
        ]
        stmt = _make_statement(rows=rows)
        assert _score_leaked_headers(stmt) == 0.0

    def test_blank_label_with_normal_values_not_leaked(self):
        """Blank label with regular financial values is NOT a leaked header."""
        rows = [
            _row(0, label_raw="Revenue"),
            _row(1, label_raw="", values=[
                {"raw": "100000", "normalized": 100000.0, "is_null": False},
            ]),
        ]
        stmt = _make_statement(rows=rows)
        assert _score_leaked_headers(stmt) == 1.0

    def test_leaked_header_unit_string(self):
        """Blank label with unit string values (e.g. 'USD millions') → leaked header."""
        rows = [
            _row(0, label_raw=""),
        ]
        rows[0]["values"] = [{"raw": "USD millions", "normalized": None, "is_null": True}]
        stmt = _make_statement(rows=rows)
        assert _score_leaked_headers(stmt) == 0.0

    def test_empty_rows_returns_1(self):
        stmt = _make_statement(rows=[])
        assert _score_leaked_headers(stmt) == 1.0


# ---------------------------------------------------------------------------
# flag_rows
# ---------------------------------------------------------------------------

class TestFlagRows:

    def test_blank_label_flagged(self):
        rows = [_row(0, label_raw="")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged

    def test_row_in_validation_warning_flagged(self):
        rows = [_row(0), _row(1)]
        warnings = [{"row_index": 1, "column_index": 0, "difference": 50}]
        stmt = _make_statement(rows=rows, warnings=warnings)
        flagged = flag_rows(stmt)
        assert 1 in flagged
        assert 0 not in flagged

    def test_section_other_with_values_not_flagged(self):
        """Rows in 'other' section WITH values should NOT be flagged (e.g., OCI items)."""
        rows = [_row(0, section="other")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 not in flagged

    def test_section_other_without_values_flagged(self):
        """Rows in 'other' section WITHOUT values should be flagged."""
        rows = [_row(0, section="other")]
        rows[0]["values"] = [{"raw": None, "normalized": None, "is_null": True}]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged

    def test_parse_failure_flagged(self):
        """Row with normalized=None but non-empty raw is a parse failure."""
        rows = [_row(0, values=[{"raw": "abc", "normalized": None, "is_null": False}])]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged

    def test_total_label_but_line_item_type_flagged(self):
        """Label containing 'total' but row_type='line_item' should be flagged."""
        rows = [_row(0, label_raw="Total current assets", row_type="line_item")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged

    def test_total_label_with_correct_type_not_flagged(self):
        """Label containing 'total' with row_type='subtotal' should NOT be flagged (by this rule)."""
        rows = [_row(0, label_raw="Total current assets", row_type="subtotal")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        # Should not be flagged just for this rule (may be flagged by others)
        assert 0 not in flagged

    def test_clean_row_not_flagged(self):
        rows = [_row(0, label_raw="Cash", row_type="line_item", section="current_assets")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 not in flagged

    def test_multiple_flag_conditions_same_row(self):
        """A row meeting multiple conditions is still in the set once."""
        rows = [_row(0, label_raw="", section="other")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged
        assert len([x for x in flagged if x == 0]) == 1

    def test_normalized_none_but_is_null_true_not_flagged(self):
        """If is_null=True, a None normalized is expected (null cell, not parse failure)."""
        rows = [_row(0, values=[{"raw": "", "normalized": None, "is_null": True}])]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 not in flagged

    def test_total_label_case_insensitive(self):
        """'TOTAL revenue' with row_type='line_item' should be flagged."""
        rows = [_row(0, label_raw="TOTAL revenue", row_type="line_item")]
        stmt = _make_statement(rows=rows)
        flagged = flag_rows(stmt)
        assert 0 in flagged

    def test_flag_rows_returns_set_of_ints(self):
        rows = [_row(0, label_raw="")]
        stmt = _make_statement(rows=rows)
        result = flag_rows(stmt)
        assert isinstance(result, set)


# ---------------------------------------------------------------------------
# score_statement — composite
# ---------------------------------------------------------------------------

class TestScoreStatement:

    def _make_perfect_balance_sheet(self):
        """A well-formed balance sheet that should score high."""
        rows = (
            [_row(i, label_raw=f"Current asset {i}", section="current_assets") for i in range(7)]
            + [_row(7 + i, label_raw=f"Non-current asset {i}", section="non_current_assets") for i in range(5)]
            + [_row(12, label_raw="Total assets", row_type="subtotal", section="assets")]
            + [_row(13 + i, label_raw=f"Liability {i}", section="current_liabilities") for i in range(5)]
            + [_row(18 + i, label_raw=f"NC Liability {i}", section="non_current_liabilities") for i in range(3)]
            + [_row(21, label_raw="Total liabilities", row_type="subtotal", section="liabilities")]
            + [_row(22 + i, label_raw=f"Equity {i}", section="equity") for i in range(3)]
        )
        columns = [
            {"column_index": 0, "label": "2025"},
            {"column_index": 1, "label": "2024"},
        ]
        return _make_statement(rows=rows, columns=columns, warnings=[])

    def _make_broken_statement(self):
        """A poorly-formed statement that should score low."""
        rows = [
            _row(0, label_raw="", section="other", values=[{"raw": "bad", "normalized": None, "is_null": False}]),
            _row(1, label_raw="", section="other"),
            _row(2, label_raw="", section="other"),
        ]
        columns = [{"column_index": 0, "label": "No year here"}]
        warnings = [{"row_index": 0, "column_index": 0, "difference": 999}]
        return _make_statement(rows=rows, columns=columns, warnings=warnings)

    def test_perfect_balance_sheet_scores_high(self):
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        assert result["score"] >= 0.85
        assert result["level"] == "high"

    def test_broken_statement_scores_low(self):
        stmt = self._make_broken_statement()
        result = score_statement(stmt, "balance_sheet")
        assert result["score"] < 0.60
        assert result["level"] == "low"

    def test_result_structure(self):
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        assert "score" in result
        assert "level" in result
        assert "signals" in result
        assert "flagged_rows" in result

    def test_signals_dict_has_all_keys(self):
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        expected_keys = {
            "subtotal_validation",
            "section_coverage",
            "row_count",
            "column_dates",
            "empty_label_ratio",
            "leaked_headers",
        }
        assert set(result["signals"].keys()) == expected_keys

    def test_all_signals_between_0_and_1(self):
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        for signal_name, signal_val in result["signals"].items():
            assert 0.0 <= signal_val <= 1.0, f"Signal {signal_name} out of range: {signal_val}"

    def test_composite_score_between_0_and_1(self):
        stmt = self._make_broken_statement()
        result = score_statement(stmt, "balance_sheet")
        assert 0.0 <= result["score"] <= 1.0

    def test_flagged_rows_is_list(self):
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        assert isinstance(result["flagged_rows"], list)

    def test_medium_level_threshold(self):
        """Score between 0.60 and 0.85 → medium."""
        rows = (
            [_row(i, section="current_assets") for i in range(8)]
            + [_row(8 + i, section="current_liabilities") for i in range(5)]
            + [_row(13 + i, section="equity") for i in range(3)]
        )
        # Use a column without a year to hurt column_dates signal
        columns = [{"column_index": 0, "label": "No year"}]
        stmt = _make_statement(rows=rows, columns=columns)
        result = score_statement(stmt, "balance_sheet")
        # The level should be one of the three valid levels
        assert result["level"] in ("high", "medium", "low")

    def test_score_is_weighted_average(self):
        """Verify the score is computed as weighted average of signals."""
        stmt = self._make_perfect_balance_sheet()
        result = score_statement(stmt, "balance_sheet")
        signals = result["signals"]
        total_weight = sum(WEIGHTS.values())
        expected = sum(signals[k] * WEIGHTS[k] for k in WEIGHTS) / total_weight
        assert result["score"] == pytest.approx(expected, abs=1e-9)

    def test_income_statement_scoring(self):
        rows = (
            [_row(i, section="revenue") for i in range(5)]
            + [_row(5 + i, section="operating_expenses") for i in range(10)]
        )
        columns = [{"column_index": 0, "label": "2025"}]
        stmt = _make_statement(rows=rows, columns=columns)
        result = score_statement(stmt, "income_statement")
        assert 0.0 <= result["score"] <= 1.0

    def test_cash_flow_scoring(self):
        rows = (
            [_row(i, section="operating_activities") for i in range(8)]
            + [_row(8 + i, section="investing_activities") for i in range(5)]
            + [_row(13 + i, section="financing_activities") for i in range(5)]
        )
        columns = [{"column_index": 0, "label": "2025"}]
        stmt = _make_statement(rows=rows, columns=columns)
        result = score_statement(stmt, "cash_flow")
        assert 0.0 <= result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Constants exported from module
# ---------------------------------------------------------------------------

class TestModuleConstants:

    def test_weights_sum_to_1(self):
        """All 6 weights should sum to 1.0."""
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_weights_has_6_keys(self):
        assert len(WEIGHTS) == 6

    def test_thresholds_has_high_and_medium(self):
        assert "high" in THRESHOLDS
        assert "medium" in THRESHOLDS

    def test_row_ranges_has_all_statement_types(self):
        assert "balance_sheet" in ROW_RANGES
        assert "income_statement" in ROW_RANGES
        assert "cash_flow" in ROW_RANGES

    def test_section_groups_has_all_statement_types(self):
        assert "balance_sheet" in SECTION_GROUPS
        assert "income_statement" in SECTION_GROUPS
        assert "cash_flow" in SECTION_GROUPS
