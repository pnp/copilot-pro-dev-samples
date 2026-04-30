"""
Tests for extractor/llm_reconciler.py — covers:
  Fix 1: LLM row index validation
  Fix 2: rows[] / cells[] sync after ghost swap
  Fix 4: Heuristic-first matching before LLM calls
"""

import json
from unittest.mock import patch, MagicMock

from extractor.llm_reconciler import (
    suppress_noise_rows,
    reconcile_suspect_ghost,
    complete_truncated_labels,
    _heuristic_match_ghosts,
    _heuristic_complete_labels,
    _apply_ghost_matches,
    _apply_label_completions,
    _build_grid,
)


# ---------------------------------------------------------------------------
# Helpers — build minimal rows/columns/cells triples for testing
# ---------------------------------------------------------------------------

def _make_cells(data: list[tuple[int, str, list[str]]]) -> tuple[list[str], list[str], list[dict]]:
    """
    Build (rows, columns, cells) from a compact description.

    data: list of (row_index, label, [val1, val2, ...])
    """
    rows = []
    columns = ["Period 1", "Period 2"]
    cells = []
    for row_idx, label, vals in data:
        rows.append(label)
        cells.append({"row": row_idx, "col": 0, "content": label, "kind": "content"})
        for vi, val in enumerate(vals):
            cells.append({"row": row_idx, "col": vi + 1, "content": val, "kind": "content"})
    return rows, columns, cells


# ===========================================================================
# Fix 1: LLM row index validation
# ===========================================================================

class TestApplyGhostMatchesValidation:
    """_apply_ghost_matches must reject invalid row indices and duplicates."""

    def test_rejects_suspect_row_not_in_valid_set(self):
        """An LLM-returned suspect_row outside the known set is rejected."""
        rows, cols, cells = _make_cells([
            (0, "Total revenue", ["100", "200"]),
            (1, "fragment text", ["50", "60"]),     # suspect
            (2, "Real Label", []),                   # ghost
        ])
        grid = _build_grid(cells)
        valid_suspects = {1}
        valid_ghosts = {2}

        # LLM returns row 0 as suspect — that's a real row, not a suspect.
        matches = [{"suspect_row": 0, "ghost_row": 2}]
        drops = _apply_ghost_matches(
            matches, valid_suspects, valid_ghosts, grid, rows, cells, "test",
        )
        assert drops == set()  # rejected — row 0 not in valid_suspects
        # Original label on row 0 unchanged.
        assert rows[0] == "Total revenue"

    def test_rejects_ghost_row_not_in_valid_set(self):
        """An LLM-returned ghost_row outside the known set is rejected."""
        rows, cols, cells = _make_cells([
            (0, "Total revenue", ["100", "200"]),
            (1, "fragment text", ["50", "60"]),
            (2, "Real Label", []),
        ])
        grid = _build_grid(cells)
        valid_suspects = {1}
        valid_ghosts = {2}

        # LLM returns row 0 as ghost — that's a data row, not a ghost.
        matches = [{"suspect_row": 1, "ghost_row": 0}]
        drops = _apply_ghost_matches(
            matches, valid_suspects, valid_ghosts, grid, rows, cells, "test",
        )
        assert drops == set()  # rejected — row 0 not in valid_ghosts

    def test_rejects_duplicate_ghost_target(self):
        """Two suspects cannot map to the same ghost row."""
        rows, cols, cells = _make_cells([
            (0, "frag_a", ["10", "20"]),   # suspect
            (1, "frag_b", ["30", "40"]),   # suspect
            (2, "True Label", []),          # ghost
        ])
        grid = _build_grid(cells)
        valid_suspects = {0, 1}
        valid_ghosts = {2}

        matches = [
            {"suspect_row": 0, "ghost_row": 2},
            {"suspect_row": 1, "ghost_row": 2},  # duplicate ghost
        ]
        drops = _apply_ghost_matches(
            matches, valid_suspects, valid_ghosts, grid, rows, cells, "test",
        )
        # First match accepted, second rejected as duplicate.
        assert drops == {2}
        assert rows[0] == "True Label"
        assert rows[1] == "frag_b"  # unchanged — duplicate was rejected

    def test_accepts_valid_match(self):
        """A valid match within both sets is applied correctly."""
        rows, cols, cells = _make_cells([
            (0, "fragment", ["50", "60"]),
            (1, "Correct Label", []),
        ])
        grid = _build_grid(cells)

        matches = [{"suspect_row": 0, "ghost_row": 1}]
        drops = _apply_ghost_matches(
            matches, {0}, {1}, grid, rows, cells, "test",
        )
        assert drops == {1}
        assert rows[0] == "Correct Label"


# ===========================================================================
# Fix 2: rows[] / cells[] sync after ghost swap
# ===========================================================================

class TestRowsCellsSync:
    """After reconcile_suspect_ghost, rows[] and cells[] must agree."""

    @patch("extractor.llm_reconciler._get_client")
    def test_rows_and_cells_in_sync_after_reconcile(self, mock_get_client):
        """Both rows[i] and cells label for row i must contain the ghost label."""
        # Set up a mock LLM response that maps suspect→ghost.
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "matches": [{"suspect_row": 1, "ghost_row": 2}]
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        rows, cols, cells = _make_cells([
            (0, "Revenue", ["100", "200"]),
            (1, "securities borrowing", ["50", "60"]),   # suspect (lowercase)
            (2, "Net decrease in receivables", []),       # ghost (no values)
            (3, "Depreciation", ["30", "40"]),
        ])

        new_rows, new_cols, new_cells = reconcile_suspect_ghost(
            "cash_flow", rows, cols, cells,
        )

        # Find the label in cells for what was row 1.
        cell_labels = {c["row"]: c["content"] for c in new_cells if c["col"] == 0}

        # rows and cells must agree on the swapped label.
        assert "Net decrease in receivables" in new_rows
        assert cell_labels[1] == "Net decrease in receivables"


# ===========================================================================
# Fix 4: Heuristic-first matching
# ===========================================================================

class TestHeuristicMatchGhosts:
    """_heuristic_match_ghosts resolves unambiguous pairs without LLM."""

    def test_single_suspect_single_ghost(self):
        """Trivial case: 1 suspect + 1 ghost → matched directly."""
        suspects = [{"row": 5, "label": "borrowing transactions", "values": ["100"]}]
        ghosts = [{"row": 3, "label": "Net decrease in receivables under"}]

        matches, remaining_s, remaining_g = _heuristic_match_ghosts(suspects, ghosts)

        assert len(matches) == 1
        assert matches[0] == {"suspect_row": 5, "ghost_row": 3}
        assert remaining_s == []
        assert remaining_g == []

    def test_substring_match(self):
        """Fragment is a substring of exactly one ghost label → matched."""
        suspects = [
            {"row": 5, "label": "liabilities", "values": ["100"]},
            {"row": 8, "label": "securities", "values": ["200"]},
        ]
        ghosts = [
            {"row": 3, "label": "Increase and decrease in derivative assets and liabilities"},
            {"row": 7, "label": "Purchases of investment securities for banking"},
        ]

        matches, remaining_s, remaining_g = _heuristic_match_ghosts(suspects, ghosts)

        assert len(matches) == 2
        assert {"suspect_row": 5, "ghost_row": 3} in matches
        assert {"suspect_row": 8, "ghost_row": 7} in matches

    def test_ambiguous_not_matched(self):
        """Fragment matches multiple ghosts → left for LLM."""
        suspects = [{"row": 5, "label": "securities", "values": ["100"]}]
        ghosts = [
            {"row": 3, "label": "Purchases of investment securities for banking"},
            {"row": 7, "label": "Proceeds from sales of investment securities"},
        ]

        matches, remaining_s, remaining_g = _heuristic_match_ghosts(suspects, ghosts)

        assert len(matches) == 0
        assert len(remaining_s) == 1
        assert len(remaining_g) == 2

    @patch("extractor.llm_reconciler._get_client")
    def test_heuristic_skips_llm_when_all_resolved(self, mock_get_client):
        """When heuristics resolve everything, no LLM call is made."""
        rows, cols, cells = _make_cells([
            (0, "Revenue", ["100", "200"]),
            (1, "liabilities", ["50", "60"]),                        # suspect
            (2, "Increase in derivative assets and liabilities", []),  # ghost
        ])

        reconcile_suspect_ghost("balance_sheet", rows, cols, cells)

        # LLM client should never have been called.
        mock_get_client.assert_not_called()


class TestHeuristicCompleteLabels:
    """_heuristic_complete_labels resolves known IFRS phrases from lookup."""

    def test_known_phrase_completed(self):
        truncated = [
            {"row": 5, "label": "Proceeds from sales and redemption of investment"},
        ]
        completions, remaining = _heuristic_complete_labels(truncated)

        assert len(completions) == 1
        assert "securities" in completions[0]["completed_label"]
        assert remaining == []

    def test_unknown_phrase_left_for_llm(self):
        truncated = [
            {"row": 5, "label": "Some unusual financial label ending with and"},
        ]
        completions, remaining = _heuristic_complete_labels(truncated)

        assert completions == []
        assert len(remaining) == 1


class TestApplyLabelCompletionsValidation:
    """_apply_label_completions must reject row indices not in valid set."""

    def test_rejects_invalid_row(self):
        rows, cols, cells = _make_cells([
            (0, "Revenue", ["100"]),
            (1, "Proceeds from sales and", ["200"]),
        ])
        grid = _build_grid(cells)
        valid_rows = {1}  # only row 1 was truncated

        # Completion targets row 0 — should be rejected.
        completions = [{"row": 0, "completed_label": "CORRUPTED"}]
        _apply_label_completions(completions, valid_rows, grid, rows, cells, "test")

        assert rows[0] == "Revenue"  # unchanged

    def test_accepts_valid_row(self):
        rows, cols, cells = _make_cells([
            (0, "Revenue", ["100"]),
            (1, "Proceeds from sales and", ["200"]),
        ])
        grid = _build_grid(cells)
        valid_rows = {1}

        completions = [{"row": 1, "completed_label": "Proceeds from sales and redemption"}]
        _apply_label_completions(completions, valid_rows, grid, rows, cells, "test")

        assert rows[1] == "Proceeds from sales and redemption"


# ===========================================================================
# Noise suppression (existing functionality — regression test)
# ===========================================================================

class TestSuppressNoiseRows:
    """suppress_noise_rows removes syntactically impossible labels."""

    def test_removes_yen_header(self):
        rows, cols, cells = _make_cells([
            (0, "(Yen)", []),
            (1, "Revenue", ["100", "200"]),
        ])
        new_rows, _, new_cells = suppress_noise_rows(rows, cols, cells)
        labels = [c["content"] for c in new_cells if c["col"] == 0]
        assert "(Yen)" not in labels
        assert "Revenue" in labels

    def test_keeps_real_ghost_row(self):
        """A row with a proper label but no values must NOT be removed."""
        rows, cols, cells = _make_cells([
            (0, "Total Assets", []),
            (1, "Revenue", ["100"]),
        ])
        new_rows, _, new_cells = suppress_noise_rows(rows, cols, cells)
        labels = [c["content"] for c in new_cells if c["col"] == 0]
        assert "Total Assets" in labels
