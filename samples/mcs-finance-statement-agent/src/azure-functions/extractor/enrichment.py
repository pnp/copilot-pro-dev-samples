"""
extractor/enrichment.py
-----------------------
Joins the CU extractor's enrichment data (canonical keys, English labels,
sections) with the Python parser's precise row extraction.

Three enrichment sources, tried in order:
  1. CU extractor lookup (best quality — canonical keys + sections from Azure)
  2. LLM batch translation (for non-English labels not covered by CU extractor)
  3. Fallback heuristics (snake_case from label text, character-based language)
"""

import json
import os
import re
import unicodedata
from typing import Optional


# ---------------------------------------------------------------------------
# Language detection (fix #4)
# ---------------------------------------------------------------------------

def detect_label_language(text: str) -> str:
    """
    Detect ISO 639-1 language code from the label's characters.

    Uses Unicode script detection — no external libraries needed.
    """
    for char in text:
        if char.isalpha():
            name = unicodedata.name(char, "").upper()
            if "CJK" in name:
                return "zh"
            if "HIRAGANA" in name or "KATAKANA" in name:
                return "ja"
            if "HANGUL" in name:
                return "ko"
            if "ARABIC" in name:
                return "ar"
            if "DEVANAGARI" in name:
                return "hi"
            if "THAI" in name:
                return "th"
            # Latin script — default to English
            if "LATIN" in name:
                return "en"
    return "en"


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_for_matching(text: str) -> str:
    """Normalize a label for fuzzy matching."""
    s = text.lower().strip()
    s = re.sub(r"[,.:;'\"\-/()（）：、]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _fallback_canonical_key(label: str) -> str:
    """Generate a snake_case key from a label when no enrichment is available."""
    s = label.lower().strip()
    s = s.replace("&", "and")
    s = re.sub(r"[,.:;'\"\-/()（）：、]", " ", s)
    s = re.sub(r"\s+", "_", s.strip()).strip("_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s or "unknown"


# ---------------------------------------------------------------------------
# Section inference (fix #2)
# ---------------------------------------------------------------------------

_SECTION_KEYWORDS: dict[str, list[str]] = {
    # English — IFRS + US GAAP + UK GAAP / Companies Act
    "current_assets": [
        "current assets", "cash and cash", "receivable", "prepaid",
        "marketable securities", "inventori",
        # UK GAAP
        "debtors", "trade debtors", "amounts owed by group",
        "prepayments and accrued income", "stock",
        "cash at bank", "restricted cash",
    ],
    "non_current_assets": [
        "property", "equipment", "goodwill", "intangible",
        "right-of-use", "long-term invest", "non-current asset",
        # UK GAAP
        "tangible fixed asset", "fixed asset", "investment",
        "amounts falling due after",
    ],
    "current_liabilities": [
        "current liabilit", "accounts payable", "accrued", "short-term",
        # UK GAAP
        "creditors", "trade creditors", "amounts owed to group",
        "falling due within one year", "other creditors",
        "accruals and deferred income", "taxation and social security",
        "corporation tax",
    ],
    "non_current_liabilities": [
        "long-term debt", "long-term income", "non-current liabilit",
        "operating lease liabilit",
        # UK GAAP
        "falling due after more than one year", "provisions for liabilities",
        "deferred tax", "pension",
    ],
    "equity": [
        "equity", "stockholder", "shareholder", "retained earning",
        "common stock", "paid-in capital",
        # UK GAAP
        "called up share capital", "share premium", "profit and loss account",
        "capital and reserves", "capital redemption reserve",
        "share-based payment reserve",
    ],
    "revenue": ["revenue", "sales", "turnover", "income from operation"],
    "operating_expenses": [
        "cost of revenue", "research and develop", "marketing",
        "general and admin", "selling", "operating expense",
        # UK GAAP
        "cost of sales", "administrative expense", "distribution cost",
        "wages and salaries", "staff cost", "social security",
        "depreciation", "amortisation", "amortization",
        "directors' emoluments", "directors emoluments",
        "audit fee", "impairment",
    ],
    "tax": [
        "income tax", "provision for", "tax rate",
        # UK GAAP
        "corporation tax", "deferred tax", "current tax",
        "tax charge", "tax on profit", "tax on ordinary",
    ],
    "eps": ["per share", "earnings per", "eps"],
    "shares": ["shares used", "weighted-average", "shares outstanding"],
    "operating_activities": [
        "operating activit", "net income", "depreciation",
        "amortization", "share-based comp", "deferred income",
        "working capital", "changes in assets",
    ],
    "investing_activities": [
        "investing activit", "purchases of property",
        "purchases of investment", "purchases of marketable",
        "acquisitions", "proceeds from sale",
    ],
    "financing_activities": [
        "financing activit", "repurchase", "dividend", "borrowing",
        "issuance of", "finance lease",
    ],
    "cash_reconciliation": [
        "cash and cash equivalents at", "net increase", "net decrease",
        "free cash flow",
    ],
    "supplemental_disclosures": ["supplemental", "cash paid for"],
    # Chinese
    # NOTE: keys that appear again extend the lists above via _merge below
}

# Chinese keywords (merged separately to avoid overwriting English lists)
_SECTION_KEYWORDS_ZH: dict[str, list[str]] = {
    "current_assets": ["流动资产", "货币资金", "交易性金融", "应收", "预付", "存货"],
    "non_current_assets": ["非流动资产", "固定资产", "无形资产", "商誉", "长期股权", "在建工程", "使用权资产", "投资性房地产"],
    "current_liabilities": ["流动负债", "应付", "短期借款", "预收"],
    "non_current_liabilities": ["非流动负债", "长期借款", "长期应付"],
    "equity": ["所有者权益", "股本", "资本公积", "盈余公积", "未分配利润", "其他综合收益"],
    "revenue": ["营业收入", "营业总收入"],
    "operating_expenses": ["营业成本", "营业总成本", "销售费用", "管理费用", "研发费用", "财务费用", "税金及附加"],
    "tax": ["所得税", "利润总额"],
    "operating_activities": ["经营活动", "销售商品", "购买商品", "支付给职工", "支付的各项税费"],
    "investing_activities": ["投资活动", "购建固定资产", "取得投资收益", "处置固定资产"],
    "financing_activities": ["筹资活动", "取得借款", "偿还债务", "分配股利"],
    "cash_reconciliation": ["现金及现金等价物", "期末现金", "期初现金"],
}

# Merge Chinese keywords into the main dict
for _sec, _kws in _SECTION_KEYWORDS_ZH.items():
    _SECTION_KEYWORDS.setdefault(_sec, []).extend(_kws)


def infer_section(label: str, statement_type: str) -> str:
    """
    Infer section from label text using keyword matching.

    Works for both English and Chinese labels.  Uses longest-match scoring
    to prefer more specific sections (e.g. "current_liabilities" over
    "current_assets" for "creditors: amounts falling due within one year").
    """
    label_lower = label.lower()
    if not label_lower.strip():
        return "other"

    # Score each section by sum of matched keyword lengths (longer = more specific)
    best_section = "other"
    best_score = 0
    for section, keywords in _SECTION_KEYWORDS.items():
        score = sum(len(kw) for kw in keywords if kw in label_lower)
        if score > best_score:
            best_score = score
            best_section = section

    # If no match, use statement_type as a broad default — but only for
    # labels that are clearly financial.  Empty or unknown labels get "other".
    if best_section == "other" and best_score == 0:
        defaults = {
            "balance_sheet": "assets",
            "income_statement": "other",
            "cash_flow": "operating_activities",
        }
        best_section = defaults.get(statement_type, "other")

    return best_section


# ---------------------------------------------------------------------------
# CU extractor lookup
# ---------------------------------------------------------------------------

def build_enrichment_lookup(cu_extractor_result: dict) -> dict[str, dict]:
    """Build a label -> enrichment lookup from the CU extractor response."""
    lookup: dict[str, dict] = {}

    contents = cu_extractor_result.get("result", {}).get("contents", [])
    if not contents:
        return lookup

    fields = contents[0].get("fields", {})
    rows = fields.get("rows", {}).get("valueArray", [])

    for r in rows:
        props = r.get("valueObject", {})
        label_raw = props.get("label_raw", {}).get("valueString", "")
        if not label_raw:
            continue

        key = _normalize_for_matching(label_raw)
        if key in lookup:
            continue

        lookup[key] = {
            "canonical_key": props.get("canonical_key", {}).get("valueString", ""),
            "label_normalized": props.get("label_normalized", {}).get("valueString", ""),
            "label_language": props.get("label_language", {}).get("valueString", ""),
            "section": props.get("section", {}).get("valueString", "other"),
            "row_type_hint": props.get("row_type", {}).get("valueString", ""),
        }

    return lookup


# ---------------------------------------------------------------------------
# LLM batch translation (fix #1)
# ---------------------------------------------------------------------------

def translate_labels_batch(
    labels: list[str],
    statement_type: str,
) -> dict[str, dict]:
    """
    Send unenriched labels to the LLM for English translation,
    canonical key generation, and section classification.

    One LLM call per batch. Returns a dict keyed by normalized label.
    """
    if not labels:
        return {}

    try:
        from .llm_reconciler import _get_client, _DEPLOYMENT
    except Exception:
        return {}  # LLM not available

    # Deduplicate
    unique_labels = list(dict.fromkeys(labels))

    prompt = (
        f"You are translating financial statement row labels to English.\n"
        f"Statement type: {statement_type.replace('_', ' ')}\n\n"
        f"For each label below, return:\n"
        f"- label_normalized: the standard English IFRS/GAAP equivalent\n"
        f"- canonical_key: English snake_case identifier (e.g. cash_and_cash_equivalents)\n"
        f"- section: one of: current_assets, non_current_assets, assets, "
        f"current_liabilities, non_current_liabilities, liabilities, equity, "
        f"revenue, operating_expenses, non_operating, tax, eps, shares, "
        f"operating_activities, investing_activities, financing_activities, "
        f"cash_reconciliation, supplemental_disclosures, other\n\n"
        f"Labels to translate:\n"
        f"{json.dumps(unique_labels, ensure_ascii=False, indent=1)}\n\n"
        f"Return ONLY a JSON object:\n"
        f'  {{"translations": [{{"label": "original", "label_normalized": "English", '
        f'"canonical_key": "snake_case", "section": "section_name"}}]}}'
    )

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial data expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        result = json.loads(response.choices[0].message.content)
        translations = result.get("translations", [])
    except Exception as e:
        print(f"      [LLM] translation failed: {e}")
        return {}

    lookup: dict[str, dict] = {}
    for t in translations:
        original = t.get("label", "")
        key = _normalize_for_matching(original)
        if not key:
            continue
        lookup[key] = {
            "canonical_key": t.get("canonical_key", ""),
            "label_normalized": t.get("label_normalized", ""),
            "label_language": detect_label_language(original),
            "section": t.get("section", "other"),
        }

    return lookup


# ---------------------------------------------------------------------------
# Section-to-group mapping
# ---------------------------------------------------------------------------

_SECTION_TO_GROUP = {
    "current_assets": "assets",
    "non_current_assets": "assets",
    "assets": "assets",
    "current_liabilities": "liabilities",
    "non_current_liabilities": "liabilities",
    "liabilities": "liabilities",
    "equity": "equity",
    "revenue": "revenue",
    "operating_expenses": "expenses",
    "non_operating": "profitability",
    "tax": "tax",
    "eps": "eps",
    "shares": "shares",
    "operating_activities": "operating_cash_flow",
    "investing_activities": "investing_cash_flow",
    "financing_activities": "financing_cash_flow",
    "cash_reconciliation": "cash_reconciliation",
    "supplemental_disclosures": "supplemental",
}


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------

def enrich_row(
    label_raw: str,
    row_type: str,
    lookup: dict[str, dict],
    statement_type: str = "",
) -> dict:
    """
    Enrich a single row with the best available data.

    Tries: CU extractor lookup -> LLM translation lookup -> fallback.
    """
    key = _normalize_for_matching(label_raw)
    match = lookup.get(key)

    if match and match.get("canonical_key"):
        canonical_key = match["canonical_key"]
        label_normalized = match.get("label_normalized") or None
        label_language = match.get("label_language") or detect_label_language(label_raw)
        section = match.get("section") or infer_section(label_raw, statement_type)
    else:
        # Fallback
        canonical_key = _fallback_canonical_key(label_raw)
        label_normalized = None
        label_language = detect_label_language(label_raw)
        section = infer_section(label_raw, statement_type)

    canonical_group = _SECTION_TO_GROUP.get(section, "other")

    return {
        "canonical_key": canonical_key,
        "label_normalized": label_normalized,
        "label_language": label_language,
        "section": section,
        "canonical_group": canonical_group,
    }


def enrich_all_rows(
    labels: list[str],
    row_types: list[str],
    cu_lookup: dict[str, dict],
    statement_type: str,
) -> list[dict]:
    """
    Enrich all rows, using LLM translation for any labels not in the CU lookup.

    This is the main entry point. It:
      1. Checks each label against the CU lookup
      2. Collects unmatched non-English labels
      3. Sends them to the LLM for batch translation
      4. Merges LLM results into the lookup
      5. Returns enrichment for every row
    """
    # First pass: identify unmatched labels
    unmatched: list[str] = []
    for label in labels:
        key = _normalize_for_matching(label)
        match = cu_lookup.get(key)
        if not match or not match.get("canonical_key"):
            lang = detect_label_language(label)
            if lang != "en" and label.strip():
                unmatched.append(label)

    # LLM batch translation for non-English unmatched labels
    if unmatched:
        print(f"      [LLM] Translating {len(unmatched)} non-English labels...")
        llm_translations = translate_labels_batch(unmatched, statement_type)
        # Merge into the lookup
        cu_lookup.update(llm_translations)
        matched = sum(1 for l in unmatched if _normalize_for_matching(l) in llm_translations)
        print(f"      [LLM] Translated {matched}/{len(unmatched)} labels")

    # Second pass: enrich all rows
    results = []
    for label, rtype in zip(labels, row_types):
        enrichment = enrich_row(label, rtype, cu_lookup, statement_type)
        results.append(enrichment)

    return results
