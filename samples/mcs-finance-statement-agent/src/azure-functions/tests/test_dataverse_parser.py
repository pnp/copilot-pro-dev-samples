import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extractor.dataverse_parser import parse_job_row, parse_statement_row, parse_line_item_rows

SAMPLE_RESULT = {
    "balance_sheet": {
        "schema_version": "1.2.0",
        "document_metadata": {
            "source_file_name": "test.pdf", "company_name": "Acme Corp",
            "company_name_raw": "Acme Corporation", "report_type": "other",
            "report_language": "en", "source_country": None, "source_exchange": None,
            "ticker": None, "identifier": None, "source_file_hash": None,
        },
        "statement_metadata": {
            "statement_type": "balance_sheet", "statement_title": "Consolidated Balance Sheet",
            "statement_title_raw": "Consolidated Balance Sheet", "accounting_standard": "IFRS",
            "currency": "USD", "currency_symbol": "$", "unit": "millions", "unit_raw": None,
            "is_consolidated": True, "is_audited": True,
            "page_range": {"start": 10, "end": 12}, "bbox_coordinate_system": "normalized_0_1",
        },
        "columns": [
            {"column_index": 0, "label": "2023", "label_raw": "2023", "period_type": "instant", "fiscal_year": 2023, "fiscal_quarter": None, "start_date": None, "end_date": None, "is_comparative": False},
            {"column_index": 1, "label": "2024", "label_raw": "2024", "period_type": "instant", "fiscal_year": 2024, "fiscal_quarter": None, "start_date": None, "end_date": None, "is_comparative": True},
        ],
        "rows": [{
            "row_index": 0, "label_raw": "Total Assets", "label_normalized": "Total Assets", "label_language": "en",
            "canonical_key": "total_assets", "canonical_group": "assets", "row_type": "total",
            "indent_level": 0, "section": "assets", "parent_canonical_key": None, "sign_hint": None,
            "is_derived_total": False, "is_required_anchor": True, "source_page": 10, "source_bbox": None,
            "values": [
                {"raw": "1,000", "normalized": 1000.0, "is_null": False, "is_zero": False, "value_kind": "currency", "confidence": 0.95, "column_index": 0},
                {"raw": "1,200", "normalized": 1200.0, "is_null": False, "is_zero": False, "value_kind": "currency", "confidence": 0.98, "column_index": 1},
            ],
        }],
        "validation": {"status": "passed", "warnings": [], "errors": []},
    },
    "summary": [{"statement_type": "balance_sheet", "status": "extracted", "row_count": 1, "column_count": 2}],
    "confidence": {"balance_sheet": {"score": 0.95, "level": "high"}},
}


def test_parse_job_row():
    row = parse_job_row("job-123", SAMPLE_RESULT)
    assert row["cree1_jobid"] == "job-123"
    assert row["cree1_companyname"] == "Acme Corp"
    assert row["cree1_reportlanguage"] == "en"
    assert row["cree1_currency"] == "USD"
    assert row["cree1_currencyunit"] == "millions"
    assert row["cree1_statementsfound"] == 1
    assert row["cree1_status"] == 833060002
    assert row["cree1_avgconfidence"] == 0.95


def test_parse_statement_row():
    row = parse_statement_row("balance_sheet", SAMPLE_RESULT["balance_sheet"])
    assert row["cree1_statementtitle"] == "Consolidated Balance Sheet"
    assert row["cree1_statementname"] == "balance_sheet"
    assert row["cree1_statementtype"] == 833060001
    assert row["cree1_pagerangestart"] == 10
    assert row["cree1_pagerangeend"] == 12
    assert row["cree1_isconsolidated"] is True
    assert row["cree1_isaudited"] is True
    assert row["cree1_reviewcomplete"] is False
    assert "schema_version" in row["cree1_rawstatementjson"]


def test_parse_line_item_rows():
    items = parse_line_item_rows("balance_sheet", SAMPLE_RESULT["balance_sheet"])
    assert len(items) == 2
    assert items[0]["cree1_lineitemname"] == "Total Assets"
    assert items[0]["cree1_rowindex"] == 0
    assert items[0]["cree1_rowtype"] == 833060003  # Total
    assert items[0]["cree1_canonicalkey"] == "total_assets"
    assert items[0]["cree1_period"] == "2023"
    assert items[0]["cree1_valueraw"] == "1,000"
    assert items[0]["cree1_valuenormalized"] == 1000.0
    assert items[0]["cree1_aiconfidence"] == 0.95
    assert items[0]["cree1_reviewstatus"] == 833060000
    assert items[1]["cree1_period"] == "2024"
    assert items[1]["cree1_valuenormalized"] == 1200.0


def test_parse_line_item_rows_null_values():
    stmt = {
        **SAMPLE_RESULT["balance_sheet"],
        "rows": [{
            "row_index": 0, "label_raw": "Header", "label_normalized": "Header", "label_language": "en",
            "canonical_key": "header", "canonical_group": "assets", "row_type": "section_header",
            "indent_level": 0, "section": "assets", "parent_canonical_key": None, "sign_hint": None,
            "is_derived_total": False, "is_required_anchor": False, "source_page": None, "source_bbox": None,
            "values": [{"raw": None, "normalized": None, "is_null": True, "is_zero": None, "value_kind": "currency", "confidence": None, "column_index": 0}],
        }],
    }
    items = parse_line_item_rows("balance_sheet", stmt)
    assert len(items) == 1
    assert items[0]["cree1_valuenormalized"] is None
    assert items[0]["cree1_rowtype"] == 833060000  # SectionHeader
