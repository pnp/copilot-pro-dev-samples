"""
tests/test_textract_integration.py
------------------------------------
End-to-end integration test for the Textract backend path through the full
extraction pipeline (Stages 1-5).

All external calls are mocked:
  - extractor.textract_client.analyze_document  → returns textract_sample_response.json
  - extractor.textract_adapter.classify_statements_with_llm  → returns a balance_sheet classification

A dummy AZURE_CU_ENDPOINT env var is monkeypatched so that importing the
extractor package (which eagerly loads azure_cu_client) does not fail.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

TESTS_DIR = Path(__file__).parent
EXTRACTOR_DIR = TESTS_DIR.parent / "extractor"
FIXTURE_PATH = TESTS_DIR / "fixtures" / "textract_sample_response.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def set_azure_cu_endpoint(monkeypatch):
    """Set a dummy AZURE_CU_ENDPOINT so extractor/__init__.py imports cleanly."""
    monkeypatch.setenv("AZURE_CU_ENDPOINT", "https://dummy.cognitiveservices.azure.com/")


@pytest.fixture()
def textract_response() -> dict:
    """Load the realistic Textract response fixture."""
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture()
def llm_classification():
    """Minimal LLM classification return for a balance sheet."""
    return [
        {
            "statement_type": "balance_sheet",
            "title_raw": "CONSOLIDATED BALANCE SHEET",
            "currency": "USD",
            "unit": "millions",
            "accounting_standard": "US_GAAP",
            "is_consolidated": True,
            "report_language": "en",
            "company_name": "Test Corp",
        }
    ]


@pytest.fixture()
def fake_pdf(tmp_path) -> str:
    """Create a minimal PDF-like file for the pipeline to receive."""
    p = tmp_path / "test_report.pdf"
    p.write_bytes(b"%PDF-1.4 fake content for testing")
    return str(p)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPipelineOptionsDefaults:
    """Verify PipelineOptions defaults independently of the extractor package."""

    def test_backend_defaults_to_cu(self, monkeypatch):
        """PipelineOptions.backend should default to 'cu'."""
        # Import after monkeypatching the env var (autouse fixture handles it)
        from extractor.stages.contracts import PipelineOptions

        opts = PipelineOptions()
        assert opts.backend == "cu"

    def test_backend_can_be_set_to_textract(self):
        """PipelineOptions.backend can be explicitly set to 'textract'."""
        from extractor.stages.contracts import PipelineOptions

        opts = PipelineOptions(backend="textract")
        assert opts.backend == "textract"


class TestTextractEndToEnd:
    """Full pipeline run through the Textract backend path (all external calls mocked)."""

    def test_pipeline_returns_summary_key(
        self, fake_pdf, textract_response, llm_classification
    ):
        """Output dict must contain a 'summary' key with a list."""
        from extractor.pipeline import run
        from extractor.stages.contracts import PipelineOptions

        options = PipelineOptions(
            backend="textract",
            use_enrichment=False,
            requested_types=["balance_sheet"],
        )

        with patch("extractor.textract_client.analyze_document", return_value=textract_response), \
             patch("extractor.textract_adapter.classify_statements_with_llm", return_value=llm_classification):
            result = run(fake_pdf, options)

        assert "summary" in result, "Pipeline output must contain 'summary' key"
        assert isinstance(result["summary"], list), "'summary' must be a list"

    def test_pipeline_returns_balance_sheet_key(
        self, fake_pdf, textract_response, llm_classification
    ):
        """Output dict must contain a 'balance_sheet' key when requested_types includes it."""
        from extractor.pipeline import run
        from extractor.stages.contracts import PipelineOptions

        options = PipelineOptions(
            backend="textract",
            use_enrichment=False,
            requested_types=["balance_sheet"],
        )

        with patch("extractor.textract_client.analyze_document", return_value=textract_response), \
             patch("extractor.textract_adapter.classify_statements_with_llm", return_value=llm_classification):
            result = run(fake_pdf, options)

        assert "balance_sheet" in result, "Pipeline output must contain 'balance_sheet' key"

    def test_textract_analyze_document_is_called(
        self, fake_pdf, textract_response, llm_classification
    ):
        """extractor.textract_client.analyze_document must be called exactly once."""
        from extractor.pipeline import run
        from extractor.stages.contracts import PipelineOptions

        options = PipelineOptions(
            backend="textract",
            use_enrichment=False,
            requested_types=["balance_sheet"],
        )

        with patch("extractor.textract_client.analyze_document", return_value=textract_response) as mock_analyze, \
             patch("extractor.textract_adapter.classify_statements_with_llm", return_value=llm_classification):
            run(fake_pdf, options)

        mock_analyze.assert_called_once_with(fake_pdf)

    def test_llm_classification_is_called(
        self, fake_pdf, textract_response, llm_classification
    ):
        """classify_statements_with_llm must be called once with the reconstructed markdown."""
        from extractor.pipeline import run
        from extractor.stages.contracts import PipelineOptions

        options = PipelineOptions(
            backend="textract",
            use_enrichment=False,
            requested_types=["balance_sheet"],
        )

        with patch("extractor.textract_client.analyze_document", return_value=textract_response), \
             patch("extractor.textract_adapter.classify_statements_with_llm", return_value=llm_classification) as mock_classify:
            run(fake_pdf, options)

        mock_classify.assert_called_once()
        # The argument must be a non-empty string (the reconstructed markdown)
        call_args = mock_classify.call_args
        markdown_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("markdown", "")
        assert isinstance(markdown_arg, str)
        assert len(markdown_arg) > 0, "Markdown passed to LLM classifier must not be empty"

    def test_cu_backend_is_not_called_for_textract(
        self, fake_pdf, textract_response, llm_classification
    ):
        """cu_client.analyze_document must NOT be called when backend='textract'."""
        from extractor.pipeline import run
        from extractor.stages.contracts import PipelineOptions

        options = PipelineOptions(
            backend="textract",
            use_enrichment=False,
            requested_types=["balance_sheet"],
        )

        with patch("extractor.textract_client.analyze_document", return_value=textract_response), \
             patch("extractor.textract_adapter.classify_statements_with_llm", return_value=llm_classification), \
             patch("extractor.cu_client.analyze_document") as mock_cu:
            run(fake_pdf, options)

        mock_cu.assert_not_called()
