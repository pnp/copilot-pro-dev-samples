"""
Tests for extractor/corrections.py — covers apply_corrections().

Each test builds a minimal v1.2-style statement dict and verifies
that the corrections dict is applied correctly.
"""

import pytest

from extractor.corrections import apply_corrections


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_statement(rows):
    """Build a minimal v1.2 statement dict with the given rows."""
    return {
        "rows": rows,
        "columns": [],
        "validation": {},
    }


def _make_row(row_index, label_raw, values=None, section="assets",
              canonical_group="assets", row_type="line_item",
              is_derived_total=False):
    """Build a minimal row dict."""
    if values is None:
        values = []
    return {
        "row_index": row_index,
        "label_raw": label_raw,
        "values": values,
        "section": section,
        "canonical_group": canonical_group,
        "row_type": row_type,
        "is_derived_total": is_derived_total,
    }


def _make_value_cell(raw, normalized, is_null=False, is_zero=None):
    """Build a minimal value cell dict."""
    return {
        "raw": raw,
        "normalized": normalized,
        "is_null": is_null,
        "is_zero": is_zero,
    }


# ---------------------------------------------------------------------------
# Test 1: label correction
# ---------------------------------------------------------------------------

class TestApplyLabelCorrection:
    def test_apply_label_correction(self):
        """Correcting a label updates label_raw; other rows are unchanged."""
        rows = [
            _make_row(0, "Cassh and cash equivalents"),
            _make_row(1, "Trade receivables"),
        ]
        statement = _make_statement(rows)

        corrections = {
            "row_0": {"label": "Cash and cash equivalents"},
        }

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Cash and cash equivalents"
        # Row 1 must be untouched
        assert result["rows"][1]["label_raw"] == "Trade receivables"

    def test_only_target_row_label_changes(self):
        """Only the targeted row's label changes; siblings are not modified."""
        rows = [
            _make_row(0, "Inventorie"),
            _make_row(1, "Prepaid expenses"),
            _make_row(2, "Other assets"),
        ]
        statement = _make_statement(rows)
        corrections = {"row_1": {"label": "Prepaid expenses (corrected)"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Inventorie"
        assert result["rows"][1]["label_raw"] == "Prepaid expenses (corrected)"
        assert result["rows"][2]["label_raw"] == "Other assets"


# ---------------------------------------------------------------------------
# Test 2: value correction re-parses
# ---------------------------------------------------------------------------

class TestApplyValueCorrectionReparses:
    def test_apply_value_correction_reparses(self):
        """Correcting value '(3,200)' should re-parse to normalized=-3200.0."""
        rows = [
            _make_row(0, "Finance costs", values=[
                _make_value_cell("3,200", 3200.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": "(3,200)"}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["raw"] == "(3,200)"
        assert cell["normalized"] == -3200.0
        assert cell["is_null"] is False
        assert cell["is_zero"] is False

    def test_positive_value_reparsed(self):
        """A plain positive value is re-parsed correctly."""
        rows = [
            _make_row(0, "Revenue", values=[
                _make_value_cell("0", 0.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": "1,500,000"}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["normalized"] == 1_500_000.0
        assert cell["is_null"] is False
        assert cell["is_zero"] is False


# ---------------------------------------------------------------------------
# Test 3: section correction updates canonical_group
# ---------------------------------------------------------------------------

class TestApplySectionCorrectionUpdatesGroup:
    def test_apply_section_correction_updates_group(self):
        """Correcting section to 'current_liabilities' sets canonical_group='liabilities'."""
        rows = [
            _make_row(0, "Trade payables", section="current_assets",
                      canonical_group="assets"),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"section": "current_liabilities"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["section"] == "current_liabilities"
        assert result["rows"][0]["canonical_group"] == "liabilities"

    def test_non_current_liabilities_maps_to_liabilities(self):
        """Section 'non_current_liabilities' maps to canonical_group 'liabilities'."""
        rows = [_make_row(0, "Long-term debt", section="current_assets", canonical_group="assets")]
        statement = _make_statement(rows)
        corrections = {"row_0": {"section": "non_current_liabilities"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["canonical_group"] == "liabilities"


# ---------------------------------------------------------------------------
# Test 4: empty value sets null
# ---------------------------------------------------------------------------

class TestApplyEmptyValueSetsNull:
    def test_apply_empty_value_sets_null(self):
        """Empty string correction sets is_null=True and normalized=None."""
        rows = [
            _make_row(0, "Deferred tax", values=[
                _make_value_cell("500", 500.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": ""}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["raw"] is None
        assert cell["normalized"] is None
        assert cell["is_null"] is True
        assert cell["is_zero"] is None

    def test_whitespace_only_value_sets_null(self):
        """Whitespace-only correction string also sets is_null=True."""
        rows = [
            _make_row(0, "Other income", values=[
                _make_value_cell("100", 100.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": "   "}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["is_null"] is True
        assert cell["normalized"] is None


# ---------------------------------------------------------------------------
# Test 5: dash value sets zero
# ---------------------------------------------------------------------------

class TestApplyDashValueSetsZero:
    def test_apply_dash_value_sets_zero(self):
        """'-' correction → normalized=0.0, is_zero=True, is_null=False."""
        rows = [
            _make_row(0, "Goodwill", values=[
                _make_value_cell("500", 500.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": "-"}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["normalized"] == 0.0
        assert cell["is_zero"] is True
        assert cell["is_null"] is False

    def test_full_width_dash_sets_zero(self):
        """Japanese full-width dash '－' also resolves to 0.0."""
        rows = [
            _make_row(0, "Investments", values=[
                _make_value_cell("1,000", 1000.0),
            ]),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"val_0": "－"}}

        result = apply_corrections(statement, corrections)

        cell = result["rows"][0]["values"][0]
        assert cell["normalized"] == 0.0
        assert cell["is_zero"] is True


# ---------------------------------------------------------------------------
# Test 6: row_type correction
# ---------------------------------------------------------------------------

class TestApplyRowTypeCorrection:
    def test_apply_row_type_correction(self):
        """Changing row_type to 'subtotal' sets is_derived_total=True."""
        rows = [
            _make_row(0, "Total current assets", row_type="line_item",
                      is_derived_total=False),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"row_type": "subtotal"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["row_type"] == "subtotal"
        assert result["rows"][0]["is_derived_total"] is True

    def test_row_type_total_sets_is_derived_total(self):
        """Changing row_type to 'total' also sets is_derived_total=True."""
        rows = [_make_row(0, "Total assets", row_type="line_item", is_derived_total=False)]
        statement = _make_statement(rows)
        corrections = {"row_0": {"row_type": "total"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["is_derived_total"] is True

    def test_row_type_line_item_clears_is_derived_total(self):
        """Changing row_type back to 'line_item' sets is_derived_total=False."""
        rows = [_make_row(0, "Mislabelled total", row_type="total", is_derived_total=True)]
        statement = _make_statement(rows)
        corrections = {"row_0": {"row_type": "line_item"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["is_derived_total"] is False


# ---------------------------------------------------------------------------
# Test 7: section "other" maps to canonical_group "other"
# ---------------------------------------------------------------------------

class TestApplyOtherSectionMapsToOtherGroup:
    def test_apply_other_section_maps_to_other_group(self):
        """Section='other' → canonical_group='other' (not in _SECTION_TO_GROUP)."""
        rows = [
            _make_row(0, "Miscellaneous", section="assets", canonical_group="assets"),
        ]
        statement = _make_statement(rows)
        corrections = {"row_0": {"section": "other"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["section"] == "other"
        assert result["rows"][0]["canonical_group"] == "other"

    def test_unknown_section_also_maps_to_other_group(self):
        """An unrecognised section string falls back to canonical_group='other'."""
        rows = [_make_row(0, "Exotic item", section="assets", canonical_group="assets")]
        statement = _make_statement(rows)
        corrections = {"row_0": {"section": "completely_unknown_section"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["canonical_group"] == "other"


# ---------------------------------------------------------------------------
# Test 8: no corrections returns statement unchanged
# ---------------------------------------------------------------------------

class TestNoCorrectionsReturnsUnchanged:
    def test_no_corrections_returns_unchanged(self):
        """Empty corrections dict returns the statement dict without modification."""
        rows = [
            _make_row(0, "Cash", values=[_make_value_cell("1,000", 1000.0)],
                      section="current_assets", canonical_group="assets"),
        ]
        statement = _make_statement(rows)
        # Take a snapshot of values before calling
        original_label = statement["rows"][0]["label_raw"]
        original_normalized = statement["rows"][0]["values"][0]["normalized"]

        result = apply_corrections(statement, {})

        assert result["rows"][0]["label_raw"] == original_label
        assert result["rows"][0]["values"][0]["normalized"] == original_normalized

    def test_returns_same_object(self):
        """apply_corrections returns the same dict object (in-place mutation)."""
        rows = [_make_row(0, "Cash")]
        statement = _make_statement(rows)

        result = apply_corrections(statement, {})

        assert result is statement


# ---------------------------------------------------------------------------
# Test 9: invalid row key is silently ignored
# ---------------------------------------------------------------------------

class TestInvalidRowKeyIgnored:
    def test_invalid_row_key_ignored(self):
        """A correction key that doesn't start with 'row_' is silently skipped."""
        rows = [_make_row(0, "Revenue")]
        statement = _make_statement(rows)
        corrections = {"invalid_key": {"label": "Should not apply"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Revenue"

    def test_row_prefix_with_non_integer_suffix_ignored(self):
        """A key like 'row_abc' (non-integer suffix) is silently skipped."""
        rows = [_make_row(0, "Revenue")]
        statement = _make_statement(rows)
        corrections = {"row_abc": {"label": "Should not apply"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Revenue"

    def test_empty_key_ignored(self):
        """An empty string key is silently skipped."""
        rows = [_make_row(0, "Revenue")]
        statement = _make_statement(rows)
        corrections = {"": {"label": "Should not apply"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Revenue"


# ---------------------------------------------------------------------------
# Test 10: nonexistent row index is silently ignored
# ---------------------------------------------------------------------------

class TestNonexistentRowIndexIgnored:
    def test_nonexistent_row_index_ignored(self):
        """Correction for row_999 (not in rows) is silently skipped."""
        rows = [_make_row(0, "Cash")]
        statement = _make_statement(rows)
        corrections = {"row_999": {"label": "Ghost row"}}

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Cash"
        assert len(result["rows"]) == 1

    def test_correction_applies_when_row_exists_skips_when_not(self):
        """Mixed corrections: existing row updated, missing row skipped."""
        rows = [
            _make_row(0, "Cash"),
            _make_row(1, "Receivables"),
        ]
        statement = _make_statement(rows)
        corrections = {
            "row_0": {"label": "Cash and equivalents"},
            "row_50": {"label": "Should be ignored"},
        }

        result = apply_corrections(statement, corrections)

        assert result["rows"][0]["label_raw"] == "Cash and equivalents"
        assert result["rows"][1]["label_raw"] == "Receivables"
        assert len(result["rows"]) == 2
