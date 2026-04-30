"""Integration test for the pipeline orchestrator."""
import pytest
from unittest.mock import patch, MagicMock
from extractor.stages.contracts import PipelineOptions


def _mock_locator_response():
    """Minimal CU Locator response with 3 statements."""
    def _stmt(stype, title, page_s, page_e):
        return {"valueObject": {
            "statement_type": {"valueString": stype},
            "title_raw": {"valueString": title},
            "title_english": {"valueString": title},
            "page_start": {"valueInteger": page_s},
            "page_end": {"valueInteger": page_e},
            "company_name": {"valueString": "Test Corp"},
            "is_consolidated": {"valueBoolean": True},
            "currency": {"valueString": "USD"},
            "unit": {"valueString": "millions"},
        }}

    md_tables = (
        "Page 1 content\n"
        "Consolidated Balance Sheet\n"
        "<table><tr><th>Item</th><th>2025</th></tr>"
        + "".join(f"<tr><td>Row {i}</td><td>{i * 100}</td></tr>" for i in range(20))
        + "</table>\n"
        "Consolidated Income Statement\n"
        "<table><tr><th>Item</th><th>2025</th></tr>"
        + "".join(f"<tr><td>Rev {i}</td><td>{i * 50}</td></tr>" for i in range(12))
        + "</table>\n"
        "Consolidated Cash Flow Statement\n"
        "<table><tr><th>Item</th><th>2025</th></tr>"
        + "".join(f"<tr><td>CF {i}</td><td>{i * 30}</td></tr>" for i in range(15))
        + "</table>\n"
    )

    return {
        "result": {
            "contents": [{
                "fields": {
                    "statements": {"valueArray": [
                        _stmt("balance_sheet", "Consolidated Balance Sheet", 1, 1),
                        _stmt("income_statement", "Consolidated Income Statement", 1, 1),
                        _stmt("cash_flow", "Consolidated Cash Flow Statement", 1, 1),
                    ]}
                },
                "markdown": md_tables,
                "pages": [{"pageNumber": 1, "spans": [{"offset": 0, "length": len(md_tables)}]}],
            }]
        }
    }


class TestPipelineRun:
    @patch("extractor.cu_client.analyze_document")
    def test_basic_pipeline_run(self, mock_analyze):
        mock_analyze.return_value = _mock_locator_response()

        from extractor.pipeline import run
        options = PipelineOptions(
            use_enrichment=False,
            requested_types=["balance_sheet", "income_statement", "cash_flow"],
            source_file_name="test.pdf",
        )
        result = run("/tmp/test.pdf", options)

        # Basic structure checks
        assert "summary" in result
        assert "confidence" in result
        assert len(result["summary"]) == 3

        # At least balance_sheet should be extracted (it has 20 rows)
        bs = result.get("balance_sheet")
        if bs:
            assert "rows" in bs
            assert "columns" in bs

    @patch("extractor.cu_client.analyze_document")
    def test_pipeline_preserves_output_shape(self, mock_analyze):
        """Output dict must have the exact keys the HTTP layer expects."""
        mock_analyze.return_value = _mock_locator_response()

        from extractor.pipeline import run
        result = run("/tmp/test.pdf", PipelineOptions(use_enrichment=False))

        required_keys = {"summary", "balance_sheet", "income_statement", "cash_flow", "confidence"}
        assert required_keys.issubset(result.keys())

        # Summary entries have required fields
        for entry in result["summary"]:
            assert "statement_type" in entry
            assert "status" in entry
            assert "page_range" in entry
