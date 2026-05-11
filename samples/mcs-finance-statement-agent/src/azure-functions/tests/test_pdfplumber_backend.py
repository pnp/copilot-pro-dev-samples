"""Tests for pdfplumber backend — client, adapter, and integration."""
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# --- Client tests ---

class TestPdfplumberClient:
    def test_extracts_pages_and_tables(self):
        """Test with the actual Xiamen PDF if available."""
        pdf_path = Path(__file__).parent.parent.parent / "docs" / "samples" / "Xiamen ITG Group Corp.,Ltd_QR_2025-09-30T00_00_00_Chinese.pdf"
        if not pdf_path.exists():
            pytest.skip("Xiamen sample PDF not available")

        from extractor.pdfplumber_client import extract_document
        result = extract_document(str(pdf_path))

        assert "pages" in result
        assert len(result["pages"]) == 16

        # Check that tables were found
        total_tables = sum(len(p["tables"]) for p in result["pages"])
        assert total_tables > 10  # Xiamen has ~20 tables

        # Check page 7 has balance sheet data
        page7 = result["pages"][6]
        assert len(page7["tables"]) > 0
        first_table = page7["tables"][0]
        # Should have Chinese headers
        header = first_table[0]
        assert any("项目" in str(cell) or "2025" in str(cell) for cell in header)


# --- Adapter tests ---

class TestTableToHtml:
    def test_converts_simple_table(self):
        from extractor.pdfplumber_adapter import _table_to_html

        table = [
            ["项目", "2025年9月30日", "2024年12月31日"],
            ["货币资金", "9,228,601,780.33", "8,479,400,167.04"],
            ["交易性金融资产", "10,355,932,397.72", "3,410,092,562.51"],
        ]
        html = _table_to_html(table)

        assert "<table>" in html
        assert "<th>项目</th>" in html
        assert "<td>货币资金</td>" in html
        assert "<td>9,228,601,780.33</td>" in html

    def test_handles_none_cells(self):
        from extractor.pdfplumber_adapter import _table_to_html

        table = [
            ["项目", "2025", "2024"],
            ["流动资产：", None, None],
        ]
        html = _table_to_html(table)
        assert "<td>流动资产：</td>" in html
        assert "<td></td>" in html  # None becomes empty string

    def test_replaces_newlines_in_cells(self):
        from extractor.pdfplumber_adapter import _table_to_html

        table = [
            ["项目", "2025年前三季度\n（1-9月）"],
            ["营业收入", "100"],
        ]
        html = _table_to_html(table)
        assert "\n" not in html.split("<table>")[1]  # No newlines inside table

    def test_empty_table_returns_empty_string(self):
        from extractor.pdfplumber_adapter import _table_to_html

        assert _table_to_html([]) == ""
        assert _table_to_html([[]]) == ""

    def test_single_row_table(self):
        from extractor.pdfplumber_adapter import _table_to_html

        table = [["Header1", "Header2"]]
        html = _table_to_html(table)
        assert "<th>Header1</th>" in html
        assert "<th>Header2</th>" in html
        assert "<td>" not in html


class TestReconstructMarkdown:
    def test_produces_markdown_with_tables(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown

        result = {
            "pages": [
                {
                    "page_number": 1,
                    "text": "CONSOLIDATED BALANCE SHEET\nCompany XYZ",
                    "tables": [
                        [["Item", "2025", "2024"], ["Assets", "100", "90"]],
                    ],
                }
            ]
        }
        md = reconstruct_markdown(result)

        assert "<!-- PAGE 1 -->" in md
        assert "CONSOLIDATED BALANCE SHEET" in md
        assert "<table>" in md
        assert "Assets" in md

    def test_page_markers_present_for_each_page(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown

        result = {
            "pages": [
                {"page_number": 1, "text": "page one", "tables": []},
                {"page_number": 2, "text": "page two", "tables": []},
            ]
        }
        md = reconstruct_markdown(result)
        assert "<!-- PAGE 1 -->" in md
        assert "<!-- PAGE 2 -->" in md

    def test_empty_pages_produce_markers_only(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown

        result = {
            "pages": [
                {"page_number": 1, "text": "", "tables": []},
            ]
        }
        md = reconstruct_markdown(result)
        assert "<!-- PAGE 1 -->" in md
        assert "<table>" not in md

    def test_multiple_tables_on_one_page(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown

        result = {
            "pages": [
                {
                    "page_number": 1,
                    "text": "Some text",
                    "tables": [
                        [["A", "B"], ["1", "2"]],
                        [["C", "D"], ["3", "4"]],
                    ],
                }
            ]
        }
        md = reconstruct_markdown(result)
        assert md.count("<table>") == 2


class TestBuildPageMap:
    def test_builds_correct_page_map(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown, build_page_map

        result = {
            "pages": [
                {"page_number": 1, "text": "page one", "tables": []},
                {"page_number": 2, "text": "page two", "tables": []},
            ]
        }
        md = reconstruct_markdown(result)
        page_map = build_page_map(result, md)

        assert len(page_map) == 2
        for start, end, page_num in page_map:
            assert start < end
            assert page_num >= 1

    def test_page_map_covers_full_markdown(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown, build_page_map

        result = {
            "pages": [
                {"page_number": 1, "text": "page one", "tables": []},
                {"page_number": 2, "text": "page two", "tables": []},
                {"page_number": 3, "text": "page three", "tables": []},
            ]
        }
        md = reconstruct_markdown(result)
        page_map = build_page_map(result, md)

        assert len(page_map) == 3
        # First page starts at 0
        assert page_map[0][0] == 0
        # Last page ends at len(markdown)
        assert page_map[-1][1] == len(md)
        # Pages are contiguous
        for i in range(len(page_map) - 1):
            assert page_map[i][1] == page_map[i + 1][0]

    def test_single_page_map(self):
        from extractor.pdfplumber_adapter import reconstruct_markdown, build_page_map

        result = {
            "pages": [
                {"page_number": 1, "text": "only page", "tables": []},
            ]
        }
        md = reconstruct_markdown(result)
        page_map = build_page_map(result, md)

        assert len(page_map) == 1
        assert page_map[0][2] == 1
        assert page_map[0][0] == 0
        assert page_map[0][1] == len(md)


class TestClassifyStatementsWithLlm:
    def test_returns_empty_when_llm_unavailable(self):
        """Should gracefully return empty list when LLM is not configured."""
        from extractor.pdfplumber_adapter import classify_statements_with_llm

        with patch("extractor.pdfplumber_adapter.logger"):
            # This will fail because env vars are not set in test
            result = classify_statements_with_llm("some markdown text")
            assert isinstance(result, list)


# --- Integration with real PDF ---

class TestPdfplumberIntegration:
    def test_full_extraction_on_xiamen(self):
        """Run full pdfplumber extraction on Xiamen PDF and verify quality."""
        pdf_path = Path(__file__).parent.parent.parent / "docs" / "samples" / "Xiamen ITG Group Corp.,Ltd_QR_2025-09-30T00_00_00_Chinese.pdf"
        if not pdf_path.exists():
            pytest.skip("Xiamen sample PDF not available")

        from extractor.pdfplumber_client import extract_document
        from extractor.pdfplumber_adapter import reconstruct_markdown, build_page_map

        result = extract_document(str(pdf_path))
        markdown = reconstruct_markdown(result)
        page_map = build_page_map(result, markdown)

        # Verify Chinese characters are preserved
        assert "项目" in markdown
        assert "货币资金" in markdown
        assert "营业收入" in markdown or "营业总收入" in markdown

        # Verify numbers are preserved
        assert "9,228,601,780.33" in markdown or "9,741,696,217.26" in markdown

        # Verify HTML tables present
        assert "<table>" in markdown
        assert markdown.count("<table>") > 10

        # Verify page map
        assert len(page_map) == 16


# --- Analyze stage integration ---

class TestAnalyzeStageIntegration:
    def test_run_analyze_dispatches_to_pdfplumber(self):
        """Verify that run_analyze routes to pdfplumber when backend='pdfplumber'."""
        from extractor.stages.contracts import PipelineOptions

        with patch("extractor.stages.analyze._run_analyze_pdfplumber") as mock_plumber:
            mock_plumber.return_value = MagicMock()
            from extractor.stages.analyze import run_analyze

            opts = PipelineOptions(backend="pdfplumber")
            run_analyze("/tmp/test.pdf", opts)

            mock_plumber.assert_called_once_with("/tmp/test.pdf", opts)

    def test_run_analyze_still_dispatches_to_textract(self):
        """Verify textract dispatch still works after pdfplumber addition."""
        from extractor.stages.contracts import PipelineOptions

        with patch("extractor.stages.analyze._run_analyze_textract") as mock_textract:
            mock_textract.return_value = MagicMock()
            from extractor.stages.analyze import run_analyze

            opts = PipelineOptions(backend="textract")
            run_analyze("/tmp/test.pdf", opts)

            mock_textract.assert_called_once_with("/tmp/test.pdf", opts)

    def test_run_analyze_still_dispatches_to_cu(self):
        """Verify CU dispatch still works (default)."""
        from extractor.stages.contracts import PipelineOptions

        with patch("extractor.stages.analyze._run_analyze_cu") as mock_cu:
            mock_cu.return_value = MagicMock()
            from extractor.stages.analyze import run_analyze

            opts = PipelineOptions(backend="cu")
            run_analyze("/tmp/test.pdf", opts)

            mock_cu.assert_called_once_with("/tmp/test.pdf", opts)
