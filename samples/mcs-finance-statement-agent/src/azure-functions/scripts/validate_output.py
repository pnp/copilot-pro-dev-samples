"""
scripts/validate_output.py
--------------------------
Strict validation agent: validates output JSONs against the analytics-ready
schema and spot-checks accuracy against known Meta report values.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# === Schema definition ===
REQUIRED_TOP_KEYS = ["statement_type", "status", "page_range", "columns", "rows", "metadata", "validation_warnings"]
REQUIRED_COL_KEYS = ["label", "period_type", "year"]
REQUIRED_ROW_KEYS = ["label", "canonical_key", "row_type", "indent_level", "values"]
REQUIRED_VAL_KEYS = ["raw", "normalized", "is_null"]
VALID_ROW_TYPES = {"section_header", "line_item", "subtotal", "total"}
VALID_PERIOD_TYPES = {"quarter", "annual", "unknown"}

# === Known Meta report values for accuracy checks ===
ACCURACY_CHECKS = {
    "income_statement": {
        "revenue": [59893.0, 48385.0, 200966.0, 164501.0],
        "net_income": [22768.0, 20838.0, 60458.0, 62360.0],
        "total_costs_and_expenses": [35148.0, 25020.0, 117690.0, 95121.0],
    },
    "balance_sheet": {
        "total_assets": [366021.0, 276054.0],
        "total_liabilities": [148778.0, 93417.0],
        "cash_and_cash_equivalents": [35873.0, 43889.0],
    },
    "cash_flow": {
        "impairment_charges_for_facilities_consolidation": [None, 94.0, None, 383.0],
        "repurchases_of_class_a_common_stock": [None, None, -26248.0, -30125.0],
        "net_cash_provided_by_operating_activities": [36214.0, 27988.0, 115800.0, 91328.0],
        "payments_for_held_for_sale_assets": [-635.0, None, -2432.0, None],
        "proceeds_from_venture_distribution": [2554.0, None, 2554.0, None],
        "net_income": [22768.0, 20838.0, 60458.0, 62360.0],
    },
}


def find_row(stmt, key):
    for r in stmt["rows"]:
        if r.get("canonical_key") == key:
            return r
    return None


def validate():
    issues = []
    suggested_fixes = []
    schema_valid = True
    json_valid = True
    accuracy_valid = True

    stmts = {}
    for stype in ["income_statement", "balance_sheet", "cash_flow"]:
        path = OUTPUT_DIR / f"{stype}.json"
        if not path.exists():
            issues.append({"issue_type": "missing_file", "field": stype, "description": f"{path} not found"})
            json_valid = False
            continue
        try:
            stmts[stype] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append({"issue_type": "invalid_json", "field": stype, "description": str(e)})
            json_valid = False

    for stype, stmt in stmts.items():
        # --- Top-level keys ---
        for k in REQUIRED_TOP_KEYS:
            if k not in stmt:
                issues.append({"issue_type": "missing_field", "field": f"{stype}.{k}", "description": f"Missing required key: {k}"})
                schema_valid = False

        # --- Columns ---
        for ci, col in enumerate(stmt.get("columns", [])):
            for k in REQUIRED_COL_KEYS:
                if k not in col:
                    issues.append({"issue_type": "missing_field", "field": f"{stype}.columns[{ci}].{k}", "description": f"Missing: {k}"})
                    schema_valid = False
            if col.get("period_type") not in VALID_PERIOD_TYPES:
                issues.append({"issue_type": "unsupported_value", "field": f"{stype}.columns[{ci}].period_type", "description": f"Invalid: {col.get('period_type')}"})
                schema_valid = False
            if col.get("year") is not None and not isinstance(col.get("year"), int):
                issues.append({"issue_type": "type_mismatch", "field": f"{stype}.columns[{ci}].year", "description": f"Expected int, got {type(col.get('year')).__name__}"})
                schema_valid = False

        n_cols = len(stmt.get("columns", []))

        # --- Rows ---
        for ri, row in enumerate(stmt.get("rows", [])):
            for k in REQUIRED_ROW_KEYS:
                if k not in row:
                    issues.append({"issue_type": "missing_field", "field": f"{stype}.rows[{ri}].{k}", "description": f"Missing: {k}"})
                    schema_valid = False
            if row.get("row_type") not in VALID_ROW_TYPES:
                issues.append({"issue_type": "unsupported_value", "field": f"{stype}.rows[{ri}].row_type", "description": f"Invalid: {row.get('row_type')}"})
                schema_valid = False
            if not isinstance(row.get("indent_level", 0), int):
                issues.append({"issue_type": "type_mismatch", "field": f"{stype}.rows[{ri}].indent_level", "description": "Must be int"})
                schema_valid = False

            vals = row.get("values", [])
            if len(vals) != n_cols:
                issues.append({"issue_type": "length_mismatch", "field": f"{stype}.rows[{ri}].values", "description": f"Expected {n_cols}, got {len(vals)}"})
                schema_valid = False

            for vi, v in enumerate(vals):
                for k in REQUIRED_VAL_KEYS:
                    if k not in v:
                        issues.append({"issue_type": "missing_field", "field": f"{stype}.rows[{ri}].values[{vi}].{k}", "description": f"Missing: {k}"})
                        schema_valid = False
                if not isinstance(v.get("is_null"), bool):
                    issues.append({"issue_type": "type_mismatch", "field": f"{stype}.rows[{ri}].values[{vi}].is_null", "description": "Must be bool"})
                    schema_valid = False
                if v.get("normalized") is not None and not isinstance(v.get("normalized"), (int, float)):
                    issues.append({"issue_type": "type_mismatch", "field": f"{stype}.rows[{ri}].values[{vi}].normalized", "description": f"Must be number, got {type(v.get('normalized')).__name__}"})
                    schema_valid = False
                # Consistency
                if v.get("is_null") and v.get("raw") is not None:
                    issues.append({"issue_type": "inconsistency", "field": f"{stype}.rows[{ri}].values[{vi}]", "description": "is_null=true but raw is not null"})
                if not v.get("is_null") and v.get("raw") is None:
                    issues.append({"issue_type": "inconsistency", "field": f"{stype}.rows[{ri}].values[{vi}]", "description": "is_null=false but raw is null"})

        # --- Metadata ---
        if not isinstance(stmt.get("metadata", {}), dict):
            issues.append({"issue_type": "type_mismatch", "field": f"{stype}.metadata", "description": "Must be object"})
            schema_valid = False

    # --- ACCURACY CHECKS ---
    for stype, checks in ACCURACY_CHECKS.items():
        stmt = stmts.get(stype)
        if not stmt:
            continue
        for key, expected in checks.items():
            row = find_row(stmt, key)
            if not row:
                issues.append({"issue_type": "missing_row", "field": f"{stype}.{key}", "description": f"Row with canonical_key '{key}' not found"})
                accuracy_valid = False
                continue
            actual = [v["normalized"] for v in row["values"]]
            if actual != expected:
                issues.append({
                    "issue_type": "accuracy",
                    "field": f"{stype}.{key}",
                    "description": f"Expected {expected}, got {actual}",
                })
                accuracy_valid = False

    result = {
        "schema_valid": schema_valid,
        "json_valid": json_valid,
        "accuracy_valid": accuracy_valid,
        "issues": issues,
        "suggested_fixes": suggested_fixes,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    validate()
