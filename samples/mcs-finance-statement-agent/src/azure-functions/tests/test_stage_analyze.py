"""Tests for Stage 1: Analyze."""
import pytest
from extractor.stages.contracts import CandidateStatement, PipelineOptions
from extractor.stages.analyze import parse_locator_statements


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_locator_response(statements: list[dict]) -> dict:
    """Build a minimal CU Locator response."""
    value_array = []
    for s in statements:
        obj = {}
        for key, val in s.items():
            if isinstance(val, bool):
                obj[key] = {"valueBoolean": val}
            elif isinstance(val, str):
                obj[key] = {"valueString": val}
            elif isinstance(val, int):
                obj[key] = {"valueInteger": val}
        value_array.append({"valueObject": obj})

    return {
        "result": {
            "contents": [{
                "fields": {
                    "statements": {"valueArray": value_array}
                },
                "markdown": "# Test",
                "pages": [],
            }]
        }
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseLocatorStatements:
    def test_empty_response(self):
        assert parse_locator_statements({}) == []
        assert parse_locator_statements({"result": {"contents": []}}) == []

    def test_single_statement(self):
        resp = _mock_locator_response([{
            "statement_type": "balance_sheet",
            "title_raw": "Consolidated Balance Sheet",
            "title_english": "Consolidated Balance Sheet",
            "page_start": 45,
            "page_end": 46,
            "company_name": "Acme Corp",
            "is_consolidated": True,
            "currency": "USD",
        }])
        candidates = parse_locator_statements(resp)
        assert len(candidates) == 1
        c = candidates[0]
        assert c.statement_type == "balance_sheet"
        assert c.page_start == 45
        assert c.page_end == 46
        assert c.is_consolidated is True
        assert c.currency == "USD"

    def test_multiple_statements(self):
        resp = _mock_locator_response([
            {"statement_type": "balance_sheet", "page_start": 10, "page_end": 11},
            {"statement_type": "income_statement", "page_start": 12, "page_end": 13},
            {"statement_type": "cash_flow", "page_start": 14, "page_end": 16},
        ])
        candidates = parse_locator_statements(resp)
        assert len(candidates) == 3
        types = [c.statement_type for c in candidates]
        assert "balance_sheet" in types
        assert "income_statement" in types
        assert "cash_flow" in types

    def test_to_dict_round_trip(self):
        resp = _mock_locator_response([{
            "statement_type": "cash_flow",
            "title_raw": "Cash Flow",
            "page_start": 5,
            "page_end": 7,
        }])
        c = parse_locator_statements(resp)[0]
        d = c.to_dict()
        assert d["statement_type"] == "cash_flow"
        assert d["page_start"] == 5
        assert d["page_end"] == 7
