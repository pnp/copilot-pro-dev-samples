"""
tests/test_analyze_textract.py
-------------------------------
Tests for Stage 1 (Analyze) with Textract backend.

Verifies:
  1. Textract backend returns correct AnalyzeResult with mocked dependencies
  2. Default PipelineOptions still uses "cu" backend

Import strategy: loads modules inside fixtures/tests using importlib,
saving and restoring sys.modules to avoid polluting other test files.
This avoids the eager extractor/__init__.py import that requires
AZURE_CU_ENDPOINT.
"""

import importlib
import importlib.util
import json
import pathlib
import sys
import types
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STAGES_DIR = pathlib.Path(__file__).parent.parent / "extractor" / "stages"
_EXTRACTOR_DIR = pathlib.Path(__file__).parent.parent / "extractor"
_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "textract_sample_response.json"


# ---------------------------------------------------------------------------
# Context manager to temporarily inject modules for relative imports
# ---------------------------------------------------------------------------

class _StagesImportContext:
    """
    Temporarily injects extractor and extractor.stages into sys.modules
    so that analyze.py's relative import (from .contracts import ...) works.
    Restores original sys.modules state on exit.
    """
    KEYS = [
        "extractor",
        "extractor.stages",
        "extractor.stages.contracts",
        "extractor.stages.analyze",
    ]

    def __enter__(self):
        self._saved = {k: sys.modules[k] for k in self.KEYS if k in sys.modules}

        # Minimal extractor package
        extractor_pkg = types.ModuleType("extractor")
        extractor_pkg.__path__ = [str(_EXTRACTOR_DIR)]
        extractor_pkg.__package__ = "extractor"
        sys.modules["extractor"] = extractor_pkg

        # stages sub-package
        stages_spec = importlib.util.spec_from_file_location(
            "extractor.stages", _STAGES_DIR / "__init__.py",
        )
        stages_mod = importlib.util.module_from_spec(stages_spec)
        stages_mod.__path__ = [str(_STAGES_DIR)]
        stages_mod.__package__ = "extractor.stages"
        sys.modules["extractor.stages"] = stages_mod
        stages_spec.loader.exec_module(stages_mod)

        # contracts
        contracts_spec = importlib.util.spec_from_file_location(
            "extractor.stages.contracts", _STAGES_DIR / "contracts.py",
        )
        self.contracts = importlib.util.module_from_spec(contracts_spec)
        sys.modules["extractor.stages.contracts"] = self.contracts
        contracts_spec.loader.exec_module(self.contracts)

        # analyze
        analyze_spec = importlib.util.spec_from_file_location(
            "extractor.stages.analyze", _STAGES_DIR / "analyze.py",
        )
        self.analyze = importlib.util.module_from_spec(analyze_spec)
        sys.modules["extractor.stages.analyze"] = self.analyze
        analyze_spec.loader.exec_module(self.analyze)

        return self

    def __exit__(self, *exc):
        # Restore original modules
        for key in self.KEYS:
            if key in self._saved:
                sys.modules[key] = self._saved[key]
            elif key in sys.modules:
                del sys.modules[key]
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def textract_response() -> dict:
    with open(_FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


MOCK_LLM_CLASSIFICATIONS = [{
    "statement_type": "balance_sheet",
    "title_raw": "CONSOLIDATED BALANCE SHEET",
    "currency": "USD",
    "unit": "millions",
    "accounting_standard": "US_GAAP",
    "is_consolidated": True,
    "report_language": "en",
    "company_name": "Test Corp",
}]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTextractBackendReturnsAnalyzeResult:
    """Test that Textract backend produces a valid AnalyzeResult."""

    def test_textract_backend_returns_analyze_result(self, textract_response):
        """Mock textract_client and classify_statements_with_llm,
        call run_analyze with backend='textract', verify result."""

        with _StagesImportContext() as ctx:
            PipelineOptions = ctx.contracts.PipelineOptions
            AnalyzeResult = ctx.contracts.AnalyzeResult
            run_analyze = ctx.analyze.run_analyze

            # Load the real adapter for reconstruct_markdown and build_page_map
            adapter_path = _EXTRACTOR_DIR / "textract_adapter.py"
            adapter_spec = importlib.util.spec_from_file_location(
                "extractor.textract_adapter", adapter_path,
            )
            adapter_mod = importlib.util.module_from_spec(adapter_spec)
            sys.modules["extractor.textract_adapter"] = adapter_mod
            adapter_spec.loader.exec_module(adapter_mod)

            # Mock textract_client.analyze_document to return fixture
            mock_textract_client = MagicMock()
            mock_textract_client.analyze_document = MagicMock(
                return_value=textract_response
            )
            sys.modules["extractor.textract_client"] = mock_textract_client

            try:
                # Mock classify_statements_with_llm to return known classifications
                with patch.object(
                    adapter_mod,
                    "classify_statements_with_llm",
                    return_value=MOCK_LLM_CLASSIFICATIONS,
                ):
                    options = PipelineOptions(backend="textract")
                    result = run_analyze("/fake/path.pdf", options)

                # Verify result type
                assert isinstance(result, AnalyzeResult)

                # Verify candidates
                assert len(result.candidates) == 1
                c = result.candidates[0]
                assert c.statement_type == "balance_sheet"
                assert c.currency == "USD"
                assert c.company_name == "Test Corp"
                assert c.unit == "millions"
                assert c.accounting_standard == "US_GAAP"
                assert c.is_consolidated is True
                assert c.report_language == "en"
                assert c.title_raw == "CONSOLIDATED BALANCE SHEET"
                # title_english mirrors title_raw for Textract path
                assert c.title_english == "CONSOLIDATED BALANCE SHEET"

                # Verify markdown contains expected content
                assert "<table>" in result.markdown
                assert "Total Assets" in result.markdown

                # Verify page_map has entries
                assert len(result.page_map) >= 1

                # Verify Textract-specific defaults
                assert result.pages == []
                assert result.enrichment_lookup == {}

            finally:
                # Clean up adapter and client from sys.modules
                sys.modules.pop("extractor.textract_adapter", None)
                sys.modules.pop("extractor.textract_client", None)


class TestCuBackendDefault:
    """Test that default PipelineOptions uses CU backend."""

    def test_cu_backend_still_works_with_default(self):
        with _StagesImportContext() as ctx:
            options = ctx.contracts.PipelineOptions()
            assert options.backend == "cu"

    def test_textract_backend_option(self):
        with _StagesImportContext() as ctx:
            options = ctx.contracts.PipelineOptions(backend="textract")
            assert options.backend == "textract"
