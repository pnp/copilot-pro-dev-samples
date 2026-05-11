"""
tests/test_textract_adapter.py
-------------------------------
Unit tests for extractor/textract_adapter.py.

Covers the four block-conversion functions (no LLM tests):
  - _build_block_index
  - _table_to_html
  - reconstruct_markdown
  - build_page_map

Import strategy: uses importlib to load textract_adapter directly, bypassing
extractor/__init__.py (which eagerly imports azure_cu_client and requires
AZURE_CU_ENDPOINT). This adapter has no module-level extractor imports.
"""

import importlib
import importlib.util
import json
import pathlib

import pytest


# ---------------------------------------------------------------------------
# Module-level import: load textract_adapter without going through __init__
# ---------------------------------------------------------------------------

def _load_adapter():
    """Import extractor.textract_adapter bypassing extractor/__init__.py."""
    spec = importlib.util.spec_from_file_location(
        "extractor.textract_adapter",
        pathlib.Path(__file__).parent.parent / "extractor" / "textract_adapter.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


adapter = _load_adapter()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_PATH = (
    pathlib.Path(__file__).parent / "fixtures" / "textract_sample_response.json"
)


@pytest.fixture(scope="module")
def textract_response() -> dict:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def blocks(textract_response) -> list[dict]:
    return textract_response["Blocks"]


# ── TestBlockIndex ───────────────────────────────────────────────────────────

class TestBlockIndex:
    def test_builds_block_lookup_by_id(self, blocks):
        index = adapter._build_block_index(blocks)

        # TABLE block is indexed
        assert "block-table-001" in index
        assert index["block-table-001"]["BlockType"] == "TABLE"

        # CELL blocks are indexed
        assert "block-cell-r1c1" in index
        assert index["block-cell-r1c1"]["BlockType"] == "CELL"

        # WORD blocks are indexed
        assert "block-word-2024" in index
        assert index["block-word-2024"]["Text"] == "2024"

        # Every block is indexed
        assert len(index) == len(blocks)


# ── TestTableToHtml ──────────────────────────────────────────────────────────

class TestTableToHtml:
    def test_converts_table_block_to_html_string(self, blocks):
        index = adapter._build_block_index(blocks)
        table_block = index["block-table-001"]

        html = adapter._table_to_html(table_block, index)

        assert "<table>" in html
        assert "</table>" in html
        # Column headers present
        assert "2024" in html
        assert "2023" in html
        # Data values present
        assert "Total Assets" in html
        assert "125,435" in html

    def test_header_cells_use_th_tag(self, blocks):
        index = adapter._build_block_index(blocks)
        table_block = index["block-table-001"]

        html = adapter._table_to_html(table_block, index)

        # Header row cells should use <th> tags
        assert "<th>" in html or "<th " in html
        # Verify header values are wrapped in <th>
        assert "<th>2024</th>" in html
        assert "<th>2023</th>" in html

    def test_data_cells_use_td_tag(self, blocks):
        index = adapter._build_block_index(blocks)
        table_block = index["block-table-001"]

        html = adapter._table_to_html(table_block, index)

        # Data row values should use <td> tags
        assert "<td>125,435</td>" in html
        assert "<td>118,290</td>" in html


# ── TestReconstructMarkdown ──────────────────────────────────────────────────

class TestReconstructMarkdown:
    def test_produces_markdown_with_embedded_tables(self, blocks):
        md = adapter.reconstruct_markdown(blocks)

        # Heading text appears
        assert "CONSOLIDATED BALANCE SHEET" in md
        # Table HTML is embedded
        assert "<table>" in md
        assert "</table>" in md

    def test_lines_appear_before_their_table(self, blocks):
        md = adapter.reconstruct_markdown(blocks)

        heading_pos = md.index("CONSOLIDATED BALANCE SHEET")
        table_pos = md.index("<table>")

        assert heading_pos < table_pos, (
            f"Heading at {heading_pos} should appear before table at {table_pos}"
        )

    def test_page_markers_are_present(self, blocks):
        md = adapter.reconstruct_markdown(blocks)

        # At least one page marker for page 1
        assert "<!-- PAGE 1 -->" in md


# ── TestBuildPageMap ─────────────────────────────────────────────────────────

class TestBuildPageMap:
    def test_builds_page_map_from_reconstructed_markdown(self, blocks):
        md = adapter.reconstruct_markdown(blocks)
        page_map = adapter.build_page_map(blocks, md)

        assert len(page_map) >= 1, "Should have at least one page entry"

        for start, end, page_num in page_map:
            assert start < end, f"start ({start}) should be < end ({end})"
            assert page_num >= 1, f"page_num ({page_num}) should be >= 1"

    def test_page_map_covers_full_markdown(self, blocks):
        md = adapter.reconstruct_markdown(blocks)
        page_map = adapter.build_page_map(blocks, md)

        # The last entry's end should be the end of the markdown
        if page_map:
            last_end = page_map[-1][1]
            assert last_end == len(md), (
                f"Last page_map end ({last_end}) should equal markdown length ({len(md)})"
            )
