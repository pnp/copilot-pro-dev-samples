"""
extractor/corrections.py
-------------------------
Applies analyst corrections from HITL Adaptive Cards to v1.2 statement dicts.
"""


def apply_corrections(statement: dict, corrections: dict) -> dict:
    """
    Apply analyst corrections to a v1.2 statement dict.

    Args:
        statement: v1.2 statement dict with rows, columns, validation
        corrections: dict of {"row_N": {"label": "...", "val_0": "...", "section": "..."}}

    Returns the statement dict with corrections applied in-place.
    """
    from .statement_detector import _parse_financial_value
    from .enrichment import _SECTION_TO_GROUP

    rows = statement.get("rows", [])
    row_by_index = {r["row_index"]: r for r in rows}

    for key, fields in corrections.items():
        if not key.startswith("row_"):
            continue
        try:
            row_idx = int(key.split("_", 1)[1])
        except (ValueError, IndexError):
            continue

        row = row_by_index.get(row_idx)
        if row is None:
            continue

        # Apply label correction
        if "label" in fields:
            row["label_raw"] = fields["label"]

        # Apply value corrections
        for fkey, fval in fields.items():
            if fkey.startswith("val_"):
                try:
                    col_idx = int(fkey.split("_", 1)[1])
                except (ValueError, IndexError):
                    continue
                if col_idx < len(row.get("values", [])):
                    val_cell = row["values"][col_idx]
                    raw = fval.strip() if fval else ""
                    if not raw:
                        val_cell["raw"] = None
                        val_cell["normalized"] = None
                        val_cell["is_null"] = True
                        val_cell["is_zero"] = None
                    else:
                        parsed = _parse_financial_value(raw)
                        val_cell["raw"] = raw
                        val_cell["normalized"] = parsed
                        val_cell["is_null"] = False
                        val_cell["is_zero"] = parsed == 0.0 if parsed is not None else None

        # Apply section correction
        if "section" in fields:
            row["section"] = fields["section"]
            row["canonical_group"] = _SECTION_TO_GROUP.get(fields["section"], "other")

        # Apply row_type correction
        if "row_type" in fields:
            row["row_type"] = fields["row_type"]
            row["is_derived_total"] = fields["row_type"] in ("subtotal", "total")

    return statement
