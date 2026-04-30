"""Tests for Adaptive Card builder module."""

import json
import pytest
from extractor.card_builder import (
    build_navigator_card,
    build_statement_review_card,
    parse_card_submission,
    init_session_state,
    advance_session_state,
)


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_test_statement(num_rows=5, columns=None):
    cols = columns or [
        {"column_index": 0, "label": "2025"},
        {"column_index": 1, "label": "2024"},
    ]
    rows = []
    for i in range(num_rows):
        rows.append(
            {
                "row_index": i,
                "label_raw": f"Item {i}",
                "row_type": "line_item",
                "indent_level": 0,
                "section": "current_assets",
                "canonical_group": "assets",
                "values": [
                    {
                        "raw": str((i + 1) * 100),
                        "normalized": float((i + 1) * 100),
                        "is_null": False,
                        "column_index": j,
                    }
                    for j in range(len(cols))
                ],
            }
        )
    return {
        "rows": rows,
        "columns": cols,
        "statement_metadata": {"page_range": {"start": 1, "end": 2}},
        "validation": {"warnings": [], "errors": []},
    }


def _make_test_confidence(level="medium", flagged=None):
    return {
        "score": {"high": 0.92, "medium": 0.72, "low": 0.45}[level],
        "level": level,
        "flagged_rows": flagged or [],
        "signals": {},
    }


def _make_summary():
    return [
        {"statement": "balance_sheet", "rows": 42},
        {"statement": "income_statement", "rows": 20},
        {"statement": "cash_flow", "rows": 15},
    ]


def _make_confidence_map():
    return {
        "balance_sheet": {
            "score": 0.72,
            "level": "medium",
            "flagged_rows": [5, 12],
            "signals": {},
        },
        "income_statement": {
            "score": 0.92,
            "level": "high",
            "flagged_rows": [],
            "signals": {},
        },
        "cash_flow": {
            "score": 0.45,
            "level": "low",
            "flagged_rows": [1, 3, 7],
            "signals": {},
        },
    }


# ── helpers for card introspection ───────────────────────────────────────────


def _collect_texts(obj):
    """Recursively collect all 'text' values in a nested dict/list structure."""
    texts = []
    if isinstance(obj, dict):
        if "text" in obj:
            texts.append(obj["text"])
        for v in obj.values():
            texts.extend(_collect_texts(v))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_collect_texts(item))
    return texts


def _collect_elements(obj, element_type):
    """Recursively collect all elements matching a given 'type'."""
    results = []
    if isinstance(obj, dict):
        if obj.get("type") == element_type:
            results.append(obj)
        for v in obj.values():
            results.extend(_collect_elements(v, element_type))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_collect_elements(item, element_type))
    return results


def _collect_actions(obj):
    """Recursively collect all action objects (type starts with 'Action.')."""
    results = []
    if isinstance(obj, dict):
        t = obj.get("type", "")
        if isinstance(t, str) and t.startswith("Action."):
            results.append(obj)
        for v in obj.values():
            results.extend(_collect_actions(v))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_collect_actions(item))
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Navigator card tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNavigatorCard:
    def test_navigator_card_structure(self):
        card = build_navigator_card("Acme", "GBP", "thousands", _make_confidence_map(), _make_summary())
        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.5"
        assert "body" in card
        assert "actions" in card

    def test_navigator_shows_all_statements(self):
        card = build_navigator_card("Acme", "GBP", "thousands", _make_confidence_map(), _make_summary())
        texts = _collect_texts(card)
        all_text = " ".join(texts)
        assert "Balance Sheet" in all_text
        assert "Income Statement" in all_text
        assert "Cash Flow" in all_text

    def test_navigator_high_confidence_shows_checkmark(self):
        card = build_navigator_card("Acme", "GBP", "thousands", _make_confidence_map(), _make_summary())
        texts = _collect_texts(card)
        found = [t for t in texts if "High" in t and "\u2713" in t]
        assert len(found) >= 1, "Expected at least one '✓ High' text"

    def test_navigator_medium_shows_warning(self):
        card = build_navigator_card("Acme", "GBP", "thousands", _make_confidence_map(), _make_summary())
        texts = _collect_texts(card)
        found = [t for t in texts if "Medium" in t and "\u26a0" in t and "issues" in t.lower()]
        assert len(found) >= 1, "Expected at least one '⚠ Medium (N issues)' text"

    def test_navigator_actions(self):
        card = build_navigator_card("Acme", "GBP", "thousands", _make_confidence_map(), _make_summary())
        actions = card.get("actions", [])
        titles = [a["title"] for a in actions]
        assert "Start Review" in titles
        assert "Skip Review & Generate Excel" in titles


# ═══════════════════════════════════════════════════════════════════════════════
# Statement review card tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestStatementReviewCard:
    def test_review_card_has_header(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        texts = _collect_texts(card)
        all_text = " ".join(texts)
        assert "Balance Sheet" in all_text
        assert "Medium" in all_text

    def test_flagged_rows_have_input_fields(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0, 1])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        inputs = _collect_elements(card, "Input.Text")
        # flagged rows 0 and 1 should each have label + N value inputs
        ids = [inp["id"] for inp in inputs]
        assert "row_0_label" in ids
        assert "row_1_label" in ids
        assert "row_0_val_0" in ids

    def test_flagged_rows_have_section_dropdown(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        choice_sets = _collect_elements(card, "Input.ChoiceSet")
        ids = [cs["id"] for cs in choice_sets]
        assert "row_0_section" in ids

    def test_flagged_row_ids_match_pattern(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [2])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        inputs = _collect_elements(card, "Input.Text")
        choice_sets = _collect_elements(card, "Input.ChoiceSet")
        all_ids = [el["id"] for el in inputs + choice_sets]
        # All IDs for row 2 should start with "row_2_"
        row2_ids = [i for i in all_ids if i.startswith("row_2_")]
        assert len(row2_ids) >= 3  # label + val_0 + val_1 at minimum

    def test_rows_in_original_order(self):
        """Rows render in row_index order, not flagged-first."""
        stmt = _make_test_statement(num_rows=6)
        conf = _make_test_confidence("medium", [1, 3])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        # All rows are inside a single Table element as TableRows.
        # The first TableRow is the header; data rows follow in order.
        tables = _collect_elements(card, "Table")
        assert len(tables) == 1, "Expected exactly one Table element"
        data_rows = tables[0]["rows"][1:]  # skip header row
        row_order = []
        for tr in data_rows:
            # Editable rows have Input.Text with id row_N_label
            inputs = _collect_elements(tr, "Input.Text")
            for inp in inputs:
                m = __import__("re").match(r"row_(\d+)_label", inp.get("id", ""))
                if m:
                    row_order.append(int(m.group(1)))
                    break
            else:
                # Read-only rows have TextBlock text matching "Item N"
                texts = _collect_texts(tr)
                for t in texts:
                    if t.startswith("Item "):
                        try:
                            row_order.append(int(t.split(" ")[1]))
                        except (ValueError, IndexError):
                            pass
                        break
        assert row_order == [0, 1, 2, 3, 4, 5], f"Expected rows in order, got {row_order}"

    def test_flagged_editable_clean_readonly(self):
        """Flagged rows have Input fields, clean rows only have TextBlocks."""
        stmt = _make_test_statement(num_rows=5)
        conf = _make_test_confidence("medium", [1, 3])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        inputs = _collect_elements(card, "Input.Text")
        ids = [inp["id"] for inp in inputs]
        # Flagged rows 1 and 3 should have input fields
        assert "row_1_label" in ids
        assert "row_3_label" in ids
        # Clean rows 0, 2, 4 should NOT have input fields
        assert "row_0_label" not in ids
        assert "row_2_label" not in ids
        assert "row_4_label" not in ids

    def test_high_confidence_readonly(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("high")
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3, editable=False)
        inputs = _collect_elements(card, "Input.Text")
        # Only the hidden 'action' input should exist — no editable row inputs
        visible_inputs = [i for i in inputs if i.get("isVisible") is not False]
        assert len(visible_inputs) == 0, "Read-only card should have no visible Input.Text elements"
        text_blocks = _collect_elements(card, "TextBlock")
        assert len(text_blocks) > 0

    def test_high_confidence_has_edit_anyway_button(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("high")
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3, editable=False)
        actions = _collect_actions(card)
        titles = [a.get("title", "") for a in actions]
        assert "Edit Anyway" in titles

    def test_edit_all_button_present(self):
        """Standard editable mode should have an Edit All button."""
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        actions = card.get("actions", [])
        titles = [a["title"] for a in actions]
        assert "Edit All" in titles

    def test_edit_all_all_rows_editable(self):
        """edit_all=True makes every row editable."""
        stmt = _make_test_statement(num_rows=5)
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3, edit_all=True)
        inputs = _collect_elements(card, "Input.Text")
        ids = [inp["id"] for inp in inputs]
        for i in range(5):
            assert f"row_{i}_label" in ids, f"row_{i}_label missing in edit_all mode"

    def test_edit_all_pagination(self):
        """With 40 rows, edit_all page 1 should render only rows 20-39."""
        stmt = _make_test_statement(num_rows=40)
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3, edit_all=True, edit_all_page=1)
        inputs = _collect_elements(card, "Input.Text")
        ids = [inp["id"] for inp in inputs]
        # Page 1 should have rows 20-39
        assert "row_20_label" in ids
        assert "row_39_label" in ids
        # Page 0 rows should not be present
        assert "row_0_label" not in ids
        assert "row_19_label" not in ids

    def test_edit_all_page_navigation_actions(self):
        """Edit All with multiple pages should have page navigation."""
        stmt = _make_test_statement(num_rows=40)
        conf = _make_test_confidence("medium", [0])
        # Page 0 of 2 — should have "Page →" but no "← Page"
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3, edit_all=True, edit_all_page=0)
        actions = card.get("actions", [])
        action_data = [a.get("data", {}).get("action") for a in actions]
        assert "edit_all_page_next" in action_data
        assert "edit_all_page_prev" not in action_data

    def test_corrections_prepopulate_values(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        corrections = {"row_0": {"label": "Trade debtors"}}
        card = build_statement_review_card("balance_sheet", stmt, conf, corrections, 1, 3)
        inputs = _collect_elements(card, "Input.Text")
        label_input = [inp for inp in inputs if inp["id"] == "row_0_label"]
        assert len(label_input) == 1
        assert label_input[0]["value"] == "Trade debtors"

    def test_navigation_actions_step1(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        actions = card.get("actions", [])
        titles = [a["title"] for a in actions]
        assert any("Next" in t for t in titles)
        assert not any("Previous" in t for t in titles)

    def test_navigation_actions_step2(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("income_statement", stmt, conf, {}, 2, 3)
        actions = card.get("actions", [])
        titles = [a["title"] for a in actions]
        assert any("Previous" in t for t in titles)
        assert any("Next" in t for t in titles)

    def test_navigation_actions_last_step(self):
        stmt = _make_test_statement()
        conf = _make_test_confidence("medium", [0])
        card = build_statement_review_card("cash_flow", stmt, conf, {}, 3, 3)
        actions = card.get("actions", [])
        titles = [a["title"] for a in actions]
        assert any("Previous" in t for t in titles)
        assert any("Submit" in t for t in titles)
        assert not any("Next" in t for t in titles)

    def test_empty_statement_shows_no_data(self):
        stmt = _make_test_statement(num_rows=0)
        conf = _make_test_confidence("medium")
        card = build_statement_review_card("balance_sheet", stmt, conf, {}, 1, 3)
        texts = _collect_texts(card)
        all_text = " ".join(texts)
        assert "No data extracted" in all_text


# ═══════════════════════════════════════════════════════════════════════════════
# Parse submission tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseSubmission:
    def test_parse_extracts_action(self):
        stmt = _make_test_statement()
        payload = {"action": "next"}
        action, corrections = parse_card_submission(payload, stmt)
        assert action == "next"

    def test_parse_detects_changed_label(self):
        stmt = _make_test_statement()
        payload = {"action": "next", "row_0_label": "Trade debtors"}
        action, corrections = parse_card_submission(payload, stmt)
        assert "row_0" in corrections
        assert corrections["row_0"]["label"] == "Trade debtors"

    def test_parse_ignores_unchanged_values(self):
        stmt = _make_test_statement()
        # Original label for row 0 is "Item 0", original val_0 is "100"
        payload = {"action": "next", "row_0_label": "Item 0", "row_0_val_0": "100"}
        action, corrections = parse_card_submission(payload, stmt)
        assert "row_0" not in corrections

    def test_parse_detects_changed_value(self):
        stmt = _make_test_statement()
        payload = {"action": "next", "row_0_val_0": "999"}
        action, corrections = parse_card_submission(payload, stmt)
        assert "row_0" in corrections
        assert corrections["row_0"]["val_0"] == "999"

    def test_parse_detects_changed_section(self):
        stmt = _make_test_statement()
        payload = {"action": "next", "row_0_section": "equity"}
        action, corrections = parse_card_submission(payload, stmt)
        assert "row_0" in corrections
        assert corrections["row_0"]["section"] == "equity"

    def test_parse_empty_payload_no_corrections(self):
        stmt = _make_test_statement()
        payload = {"action": "next"}
        action, corrections = parse_card_submission(payload, stmt)
        assert corrections == {}


# ═══════════════════════════════════════════════════════════════════════════════
# Session state tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestInitSessionState:
    def test_basic_init(self):
        conf = _make_confidence_map()
        state_str = init_session_state(conf, job_id="job-123")
        state = json.loads(state_str)
        assert state["jobId"] == "job-123"
        assert state["phase"] == "navigator"
        assert state["step"] == 0
        assert state["statements"] == ["balance_sheet", "income_statement", "cash_flow"]
        assert state["corrections"] == {}

    def test_filters_not_found(self):
        conf = _make_confidence_map()
        conf["cash_flow"]["level"] = "not_found"
        state = json.loads(init_session_state(conf))
        assert "cash_flow" not in state["statements"]
        assert state["statements"] == ["balance_sheet", "income_statement"]

    def test_filters_missing_key(self):
        conf = {
            "balance_sheet": {"score": 0.9, "level": "high", "flagged_rows": []},
        }
        state = json.loads(init_session_state(conf))
        assert state["statements"] == ["balance_sheet"]

    def test_empty_confidence(self):
        state = json.loads(init_session_state({}))
        assert state["statements"] == []

    def test_available_statements_overrides_confidence(self):
        """When available_statements is provided, confidence levels are ignored."""
        conf = _make_confidence_map()  # all 3 have scores
        # Only BS and CF actually have data
        state = json.loads(init_session_state(
            conf, available_statements=["balance_sheet", "cash_flow"]
        ))
        assert state["statements"] == ["balance_sheet", "cash_flow"]

    def test_available_statements_empty(self):
        conf = _make_confidence_map()
        state = json.loads(init_session_state(conf, available_statements=[]))
        assert state["statements"] == []

    def test_available_statements_preserves_canonical_order(self):
        """Even if available_statements is passed in reverse, output follows STATEMENT_ORDER."""
        conf = _make_confidence_map()
        state = json.loads(init_session_state(
            conf, available_statements=["cash_flow", "balance_sheet"]
        ))
        assert state["statements"] == ["balance_sheet", "cash_flow"]


class TestAdvanceSessionState:
    def _init(self, stmts=None):
        """Create a review-ready state at step 1."""
        stmts = stmts or ["balance_sheet", "income_statement", "cash_flow"]
        return json.dumps({
            "jobId": "j1",
            "phase": "review",
            "step": 1,
            "statements": stmts,
            "corrections": {},
            "editable": False,
            "editAll": False,
            "editAllPage": 0,
        })

    def _nav(self):
        return json.dumps({
            "jobId": "j1",
            "phase": "navigator",
            "step": 0,
            "statements": ["balance_sheet", "income_statement"],
            "corrections": {},
            "editable": False,
            "editAll": False,
            "editAllPage": 0,
        })

    # ── Navigator phase ──

    def test_skip_review(self):
        action, state_str = advance_session_state(self._nav(), {"action": "skip_review"})
        assert action == "skip"

    def test_start_review(self):
        action, state_str = advance_session_state(self._nav(), {"action": "start_review"})
        assert action == "continue"
        state = json.loads(state_str)
        assert state["phase"] == "review"
        assert state["step"] == 1

    # ── Review phase: navigation ──

    def test_next_advances_step(self):
        action, state_str = advance_session_state(self._init(), {"action": "next"})
        assert action == "continue"
        state = json.loads(state_str)
        assert state["step"] == 2

    def test_next_past_last_returns_done(self):
        s = json.loads(self._init())
        s["step"] = 3  # last of 3 statements
        action, state_str = advance_session_state(json.dumps(s), {"action": "next"})
        assert action == "done"
        state = json.loads(state_str)
        assert state["phase"] == "export"

    def test_previous_decrements_step(self):
        s = json.loads(self._init())
        s["step"] = 2
        action, state_str = advance_session_state(json.dumps(s), {"action": "previous"})
        assert action == "continue"
        state = json.loads(state_str)
        assert state["step"] == 1

    def test_previous_at_step1_stays(self):
        action, state_str = advance_session_state(self._init(), {"action": "previous"})
        state = json.loads(state_str)
        assert state["step"] == 1

    def test_submit_returns_done(self):
        action, _ = advance_session_state(self._init(), {"action": "submit"})
        assert action == "done"

    # ── Review phase: edit toggles ──

    def test_edit_enables_editable(self):
        action, state_str = advance_session_state(self._init(), {"action": "edit"})
        assert action == "continue"
        state = json.loads(state_str)
        assert state["editable"] is True
        assert state["editAll"] is False

    def test_edit_all_enables_both(self):
        action, state_str = advance_session_state(self._init(), {"action": "edit_all"})
        state = json.loads(state_str)
        assert state["editable"] is True
        assert state["editAll"] is True

    def test_edit_all_page_next(self):
        s = json.loads(self._init())
        s["editAll"] = True
        s["editAllPage"] = 0
        action, state_str = advance_session_state(json.dumps(s), {"action": "edit_all_page_next"})
        state = json.loads(state_str)
        assert state["editAllPage"] == 1

    def test_edit_all_page_prev_floors_at_zero(self):
        s = json.loads(self._init())
        s["editAllPage"] = 0
        action, state_str = advance_session_state(json.dumps(s), {"action": "edit_all_page_prev"})
        state = json.loads(state_str)
        assert state["editAllPage"] == 0

    # ── Corrections accumulation ──

    def test_corrections_captured(self):
        stmt = _make_test_statement()
        payload = {"action": "next", "row_0_label": "Trade debtors"}
        action, state_str = advance_session_state(self._init(), payload, stmt)
        state = json.loads(state_str)
        assert "balance_sheet" in state["corrections"]
        assert state["corrections"]["balance_sheet"]["row_0"]["label"] == "Trade debtors"

    def test_corrections_accumulate_across_calls(self):
        stmt = _make_test_statement()
        # First call: correct row 0
        _, state_str = advance_session_state(
            self._init(), {"action": "edit", "row_0_label": "Corrected"}, stmt
        )
        # Second call on same step: correct row 1
        _, state_str = advance_session_state(
            state_str, {"action": "next", "row_1_val_0": "999"}, stmt
        )
        state = json.loads(state_str)
        bs = state["corrections"]["balance_sheet"]
        assert bs["row_0"]["label"] == "Corrected"
        assert bs["row_1"]["val_0"] == "999"

    # ── Unknown action fallback ──

    def test_unknown_action_returns_continue(self):
        action, _ = advance_session_state(self._init(), {"action": "bogus"})
        assert action == "continue"
