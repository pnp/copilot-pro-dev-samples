"""
Stage 5: Validate — structural validation gates.

7 checks with weighted scoring:
  1. Required anchors (25%) — critical rows present
  2. Subtotal arithmetic (20%) — children sum ≈ subtotal
  3. Balance equation (15%) — Assets ≈ Liabilities + Equity
  4. Min row count (15%) — BS>=15, IS>=8, CF>=12
  5. Cross-statement (10%) — NI on IS ≈ NI on CF
  6. Value density (10%) — >=60% of line items have non-null values
  7. Period/currency (5%) — consistent across statements

Quality thresholds:
  >= 0.90 → accepted
  >= 0.70 → review
  < 0.70  → rejected
"""
import logging
from typing import Optional

from .contracts import (
    EnrichedStatement,
    EnrichResult,
    QualityStatus,
    ValidatedStatement,
    ValidateResult,
    ValidationCheck,
)

logger = logging.getLogger(__name__)

_MIN_ROW_COUNTS: dict[str, int] = {
    "balance_sheet": 15,
    "income_statement": 8,
    "cash_flow": 12,
}

_REQUIRED_ANCHORS: dict[str, list[list[str]]] = {
    "balance_sheet": [
        ["total_assets", "total_general"],
        ["total_liabilities", "total_liabilities_and_equity"],
    ],
    "income_statement": [
        ["revenue", "net_revenue", "total_revenue", "turnover", "operating_income",
         "net_sales", "chiffre_d_affaires"],
    ],
    "cash_flow": [
        ["net_cash_from_operating_activities", "net_cash_provided_by_operating_activities"],
        ["net_cash_used_in_investing_activities", "net_cash_from_investing_activities"],
        ["net_cash_used_in_financing_activities", "net_cash_from_financing_activities"],
    ],
}

# Fallback: also check by label text when canonical keys don't match
# (for French/non-English reports where canonical key mapping may be incomplete)
_REQUIRED_ANCHOR_LABELS: dict[str, list[list[str]]] = {
    "balance_sheet": [
        ["total assets", "total general", "total actif"],
        ["total liabilities", "total passif", "total general (i"],
    ],
    "income_statement": [
        ["revenue", "net sales", "turnover", "chiffre d'affaires", "net turnover",
         "operating revenue", "total operating revenue"],
    ],
    "cash_flow": [
        ["cash from operating", "cash flows from operating", "net cash from operating"],
        ["cash from investing", "cash flows from investing", "net cash from investing"],
        ["cash from financing", "cash flows from financing", "net cash from financing"],
    ],
}

_QUALITY_THRESHOLDS = {
    "accepted": 0.90,
    "review": 0.70,
}


def _check_required_anchors(v12_doc: dict, statement_type: str) -> ValidationCheck:
    """Check that required anchor rows are present (by canonical key OR label text)."""
    anchor_groups = _REQUIRED_ANCHORS.get(statement_type, [])
    label_groups = _REQUIRED_ANCHOR_LABELS.get(statement_type, [])
    if not anchor_groups:
        return ValidationCheck("required_anchors", True, 1.0, 0.25)

    rows = v12_doc.get("rows", [])
    present_keys = {r.get("canonical_key", "") for r in rows}
    present_labels = {
        (r.get("label_normalized") or r.get("label_raw", "")).lower()
        for r in rows
    }

    groups_found = 0
    missing_groups = []
    for i, group in enumerate(anchor_groups):
        # Check by canonical key first
        if any(key in present_keys for key in group):
            groups_found += 1
            continue
        # Fallback: check by label text
        label_group = label_groups[i] if i < len(label_groups) else []
        if any(any(lbl in pl for pl in present_labels) for lbl in label_group):
            groups_found += 1
            continue
        missing_groups.append(group)

    score = groups_found / len(anchor_groups) if anchor_groups else 1.0
    details = f"Missing: {missing_groups}" if missing_groups else None
    return ValidationCheck(name="required_anchors", passed=score == 1.0, score=score, weight=0.25, details=details)


def _check_subtotal_arithmetic(v12_doc: dict) -> ValidationCheck:
    rows = v12_doc.get("rows", [])
    warnings = v12_doc.get("validation", {}).get("warnings", [])
    subtotal_indices = {r["row_index"] for r in rows if r.get("row_type") == "subtotal"}
    if not subtotal_indices:
        return ValidationCheck("subtotal_arithmetic", True, 1.0, 0.20)
    warned_indices = {w["row_index"] for w in warnings if w.get("code") == "SUBTOTAL_MISMATCH"}
    failed = subtotal_indices & warned_indices
    score = (len(subtotal_indices) - len(failed)) / len(subtotal_indices)
    return ValidationCheck(name="subtotal_arithmetic", passed=len(failed) == 0, score=score, weight=0.20, details=f"{len(failed)}/{len(subtotal_indices)} subtotals mismatched" if failed else None)


def _check_balance_equation(v12_doc: dict, statement_type: str) -> ValidationCheck:
    if statement_type != "balance_sheet":
        return ValidationCheck("balance_equation", True, 1.0, 0.15)
    rows = v12_doc.get("rows", [])
    key_values: dict[str, Optional[float]] = {}

    # Look up by canonical key
    for r in rows:
        key = r.get("canonical_key", "")
        if key in ("total_assets", "total_liabilities", "total_equity",
                    "total_liabilities_and_equity", "total_general"):
            vals = r.get("values", [])
            if vals and vals[0].get("normalized") is not None:
                key_values[key] = vals[0]["normalized"]

    # Fallback: look up by label text (for French/non-English reports)
    if not key_values:
        _LABEL_MAP = {
            "total_assets": ["total assets", "total actif", "total general (i"],
            "total_liabilities_and_equity": ["total liabilities and equity", "total passif",
                                              "total general (i à v", "total general (i to v"],
        }
        for r in rows:
            label = (r.get("label_normalized") or r.get("label_raw", "")).lower()
            for target_key, patterns in _LABEL_MAP.items():
                if any(p in label for p in patterns) and target_key not in key_values:
                    vals = r.get("values", [])
                    if vals and vals[0].get("normalized") is not None:
                        key_values[target_key] = vals[0]["normalized"]

    total_assets = key_values.get("total_assets") or key_values.get("total_general")
    total_le = key_values.get("total_liabilities_and_equity")
    total_l = key_values.get("total_liabilities")
    total_e = key_values.get("total_equity")
    if total_assets is not None and total_le is not None:
        diff = abs(total_assets - total_le)
        tolerance = abs(total_assets) * 0.01 if total_assets else 1.0
        passed = diff <= tolerance
        score = 1.0 if passed else max(0.0, 1.0 - diff / max(abs(total_assets), 1))
        return ValidationCheck("balance_equation", passed, score, 0.15, f"Assets={total_assets}, L+E={total_le}, diff={diff}" if not passed else None)
    if total_assets is not None and total_l is not None and total_e is not None:
        computed_le = total_l + total_e
        diff = abs(total_assets - computed_le)
        tolerance = abs(total_assets) * 0.01 if total_assets else 1.0
        passed = diff <= tolerance
        score = 1.0 if passed else max(0.0, 1.0 - diff / max(abs(total_assets), 1))
        return ValidationCheck("balance_equation", passed, score, 0.15, f"Assets={total_assets}, L+E={computed_le}, diff={diff}" if not passed else None)
    return ValidationCheck("balance_equation", False, 0.5, 0.15, "Missing anchor values")


def _check_min_row_count(v12_doc: dict, statement_type: str) -> ValidationCheck:
    rows = v12_doc.get("rows", [])
    count = len(rows)
    min_count = _MIN_ROW_COUNTS.get(statement_type, 8)
    passed = count >= min_count
    score = min(1.0, count / min_count) if min_count > 0 else 1.0
    return ValidationCheck("min_row_count", passed, score, 0.15, f"{count} rows (min {min_count})" if not passed else None)


def _check_cross_statement(v12_doc: dict, statement_type: str, all_docs: dict[str, dict]) -> ValidationCheck:
    if statement_type not in ("income_statement", "cash_flow"):
        return ValidationCheck("cross_statement", True, 1.0, 0.10)
    is_doc = all_docs.get("income_statement", {})
    cf_doc = all_docs.get("cash_flow", {})
    if not is_doc or not cf_doc:
        return ValidationCheck("cross_statement", True, 0.5, 0.10, "Missing paired statement")
    is_ni = None
    for r in is_doc.get("rows", []):
        if r.get("canonical_key") in ("net_income", "profit_for_the_period", "net_profit"):
            vals = r.get("values", [])
            if vals and vals[0].get("normalized") is not None:
                is_ni = vals[0]["normalized"]
                break
    cf_ni = None
    for r in cf_doc.get("rows", []):
        if r.get("canonical_key") in ("net_income", "profit_for_the_period", "net_profit"):
            vals = r.get("values", [])
            if vals and vals[0].get("normalized") is not None:
                cf_ni = vals[0]["normalized"]
                break
    if is_ni is None or cf_ni is None:
        return ValidationCheck("cross_statement", True, 0.5, 0.10, "Net income not found in both")
    diff = abs(is_ni - cf_ni)
    tolerance = max(abs(is_ni) * 0.01, 1.0)
    passed = diff <= tolerance
    score = 1.0 if passed else max(0.0, 1.0 - diff / max(abs(is_ni), 1))
    return ValidationCheck("cross_statement", passed, score, 0.10, f"IS NI={is_ni}, CF NI={cf_ni}, diff={diff}" if not passed else None)


def _check_value_density(v12_doc: dict) -> ValidationCheck:
    rows = v12_doc.get("rows", [])
    line_items = [r for r in rows if r.get("row_type") == "line_item"]
    if not line_items:
        return ValidationCheck("value_density", True, 1.0, 0.10)
    with_values = 0
    for r in line_items:
        vals = r.get("values", [])
        if any(not v.get("is_null", True) for v in vals):
            with_values += 1
    density = with_values / len(line_items)
    passed = density >= 0.60
    score = min(1.0, density / 0.60) if density < 0.60 else 1.0
    return ValidationCheck("value_density", passed, score, 0.10, f"{density:.0%} density ({with_values}/{len(line_items)})" if not passed else None)


def _check_period_currency(v12_doc: dict, all_docs: dict[str, dict]) -> ValidationCheck:
    currencies = set()
    for stype, doc in all_docs.items():
        if doc:
            cur = doc.get("statement_metadata", {}).get("currency")
            if cur:
                currencies.add(cur)
    passed = len(currencies) <= 1
    score = 1.0 if passed else 0.5
    return ValidationCheck("period_currency", passed, score, 0.05, f"Multiple currencies: {currencies}" if not passed else None)


def run_validate(enrich_result: EnrichResult) -> ValidateResult:
    all_docs: dict[str, dict] = {stype: es.v12_doc for stype, es in enrich_result.statements.items()}
    statements: dict[str, ValidatedStatement] = {}
    for stype, enriched in enrich_result.statements.items():
        v12_doc = enriched.v12_doc
        checks = [
            _check_required_anchors(v12_doc, stype),
            _check_subtotal_arithmetic(v12_doc),
            _check_balance_equation(v12_doc, stype),
            _check_min_row_count(v12_doc, stype),
            _check_cross_statement(v12_doc, stype, all_docs),
            _check_value_density(v12_doc),
            _check_period_currency(v12_doc, all_docs),
        ]
        total_weight = sum(c.weight for c in checks)
        quality_score = sum(c.score * c.weight for c in checks) / total_weight if total_weight > 0 else 0.0
        if quality_score >= _QUALITY_THRESHOLDS["accepted"]:
            status = QualityStatus.ACCEPTED
        elif quality_score >= _QUALITY_THRESHOLDS["review"]:
            status = QualityStatus.REVIEW
        else:
            status = QualityStatus.REJECTED
        logger.info(f"  Stage 5 (Validate) {stype}: quality={quality_score:.2f} status={status.value} checks={[c.name for c in checks if not c.passed]}")
        statements[stype] = ValidatedStatement(statement_type=stype, v12_doc=v12_doc, quality_score=quality_score, status=status, checks=checks)
    return ValidateResult(statements=statements)
