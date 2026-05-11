"""Tests for Stage 5: Validate — structural validation gates."""
import pytest
from extractor.stages.contracts import (
    EnrichedStatement,
    EnrichResult,
    QualityStatus,
)
from extractor.stages.validate import (
    _check_required_anchors,
    _check_min_row_count,
    _check_value_density,
    _check_balance_equation,
    _check_cross_statement,
    _check_period_currency,
    run_validate,
)


def _row(canonical_key="cash", row_type="line_item", values=None, section="current_assets"):
    if values is None:
        values = [{"raw": "100", "normalized": 100.0, "is_null": False}]
    return {
        "row_index": 0,
        "canonical_key": canonical_key,
        "row_type": row_type,
        "section": section,
        "label_raw": canonical_key,
        "values": values,
    }


def _doc(rows=None, statement_type="balance_sheet", currency="USD", warnings=None):
    return {
        "rows": rows or [],
        "columns": [{"column_index": 0, "label": "2025"}],
        "validation": {"warnings": warnings or []},
        "statement_metadata": {"currency": currency, "statement_type": statement_type},
    }


class TestRequiredAnchors:
    def test_balance_sheet_all_present(self):
        doc = _doc([_row("total_assets", "total"), _row("total_liabilities", "total")])
        check = _check_required_anchors(doc, "balance_sheet")
        assert check.passed
        assert check.score == 1.0

    def test_balance_sheet_missing_one(self):
        doc = _doc([_row("total_assets", "total")])
        check = _check_required_anchors(doc, "balance_sheet")
        assert not check.passed
        assert check.score == 0.5

    def test_income_statement_revenue_present(self):
        doc = _doc([_row("revenue")])
        check = _check_required_anchors(doc, "income_statement")
        assert check.passed


class TestMinRowCount:
    def test_balance_sheet_below_minimum(self):
        doc = _doc([_row(f"row_{i}") for i in range(4)])
        check = _check_min_row_count(doc, "balance_sheet")
        assert not check.passed
        assert check.score < 1.0
        assert "4 rows" in check.details

    def test_balance_sheet_at_minimum(self):
        doc = _doc([_row(f"row_{i}") for i in range(15)])
        check = _check_min_row_count(doc, "balance_sheet")
        assert check.passed

    def test_income_statement_minimum_8(self):
        doc = _doc([_row(f"row_{i}") for i in range(8)])
        check = _check_min_row_count(doc, "income_statement")
        assert check.passed

    def test_cash_flow_minimum_12(self):
        doc = _doc([_row(f"row_{i}") for i in range(11)])
        check = _check_min_row_count(doc, "cash_flow")
        assert not check.passed


class TestValueDensity:
    def test_all_have_values(self):
        doc = _doc([_row(f"row_{i}") for i in range(10)])
        check = _check_value_density(doc)
        assert check.passed
        assert check.score == 1.0

    def test_below_60_percent(self):
        rows = [_row(f"row_{i}") for i in range(4)]
        rows += [_row(f"empty_{i}", values=[{"raw": None, "normalized": None, "is_null": True}]) for i in range(8)]
        doc = _doc(rows)
        check = _check_value_density(doc)
        assert not check.passed

    def test_exactly_60_percent(self):
        rows = [_row(f"row_{i}") for i in range(6)]
        rows += [_row(f"empty_{i}", values=[{"raw": None, "normalized": None, "is_null": True}]) for i in range(4)]
        doc = _doc(rows)
        check = _check_value_density(doc)
        assert check.passed


class TestBalanceEquation:
    def test_balanced(self):
        doc = _doc([
            _row("total_assets", "total", [{"raw": "1000", "normalized": 1000.0, "is_null": False}]),
            _row("total_liabilities_and_equity", "total", [{"raw": "1000", "normalized": 1000.0, "is_null": False}]),
        ])
        check = _check_balance_equation(doc, "balance_sheet")
        assert check.passed

    def test_imbalanced(self):
        doc = _doc([
            _row("total_assets", "total", [{"raw": "1000", "normalized": 1000.0, "is_null": False}]),
            _row("total_liabilities_and_equity", "total", [{"raw": "500", "normalized": 500.0, "is_null": False}]),
        ])
        check = _check_balance_equation(doc, "balance_sheet")
        assert not check.passed

    def test_non_balance_sheet_skipped(self):
        check = _check_balance_equation(_doc(), "income_statement")
        assert check.passed


class TestCrossStatement:
    def test_matching_net_income(self):
        is_doc = _doc([_row("net_income", values=[{"raw": "100", "normalized": 100.0, "is_null": False}])])
        cf_doc = _doc([_row("net_income", values=[{"raw": "100", "normalized": 100.0, "is_null": False}])])
        all_docs = {"income_statement": is_doc, "cash_flow": cf_doc}
        check = _check_cross_statement(is_doc, "income_statement", all_docs)
        assert check.passed

    def test_mismatched_net_income(self):
        is_doc = _doc([_row("net_income", values=[{"raw": "100", "normalized": 100.0, "is_null": False}])])
        cf_doc = _doc([_row("net_income", values=[{"raw": "500", "normalized": 500.0, "is_null": False}])])
        all_docs = {"income_statement": is_doc, "cash_flow": cf_doc}
        check = _check_cross_statement(is_doc, "income_statement", all_docs)
        assert not check.passed


class TestRunValidate:
    def test_global_reach_rejected(self):
        """Global Reach scenario: 4-row fragment should be rejected."""
        doc = _doc([_row(f"row_{i}") for i in range(4)])
        enrich_result = EnrichResult(statements={"balance_sheet": EnrichedStatement("balance_sheet", doc)})
        result = run_validate(enrich_result)
        vs = result.statements["balance_sheet"]
        assert vs.status == QualityStatus.REJECTED or vs.quality_score < 0.70

    def test_healthy_statement_accepted(self):
        """A well-formed statement should score high."""
        rows = [_row(f"item_{i}") for i in range(20)]
        rows.append(_row("total_assets", "total"))
        rows.append(_row("total_liabilities", "total"))
        doc = _doc(rows, currency="USD")
        enrich_result = EnrichResult(statements={"balance_sheet": EnrichedStatement("balance_sheet", doc)})
        result = run_validate(enrich_result)
        vs = result.statements["balance_sheet"]
        assert vs.quality_score >= 0.70
