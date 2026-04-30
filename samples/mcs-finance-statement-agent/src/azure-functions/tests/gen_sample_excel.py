"""Generate a sample Excel using the professional formatter for verification."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("AZURE_CU_ENDPOINT", "dummy")
os.environ.setdefault("AZURE_CU_KEY", "dummy")

from extractor.excel_formatter import build_professional_excel

sample_result = {
    "summary": [
        {"statement_type": "balance_sheet", "page_range": {"start": 45, "end": 46}, "quality_score": 0.95},
        {"statement_type": "income_statement", "page_range": {"start": 43, "end": 44}, "quality_score": 0.92},
        {"statement_type": "cash_flow", "page_range": {"start": 47, "end": 48}, "quality_score": 0.88},
    ],
    "balance_sheet": {
        "statement_metadata": {
            "statement_title": "Consolidated Balance Sheet",
            "statement_title_raw": "Consolidated Balance Sheet",
            "currency": "AUD", "currency_symbol": "$", "unit": "millions",
        },
        "columns": [{"label": "Item"}, {"label": "30 Jun 2024"}, {"label": "30 Jun 2023"}],
        "rows": [
            {"label_raw": "ASSETS", "label_normalized": "Assets", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Cash and cash equivalents", "label_normalized": "Cash and cash equivalents", "row_type": "line_item", "indent_level": 1, "canonical_key": "cash_and_equivalents", "values": [{"normalized": 12450.0, "raw": "12,450"}, {"normalized": 11230.0, "raw": "11,230"}]},
            {"label_raw": "Trading securities", "label_normalized": "Trading securities", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 8920.0, "raw": "8,920"}, {"normalized": 7650.0, "raw": "7,650"}]},
            {"label_raw": "Loans and advances", "label_normalized": "Loans and advances", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 215800.0, "raw": "215,800"}, {"normalized": 198500.0, "raw": "198,500"}]},
            {"label_raw": "Property and equipment", "label_normalized": "Property and equipment", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 3240.0, "raw": "3,240"}, {"normalized": 3180.0, "raw": "3,180"}]},
            {"label_raw": "Goodwill and intangibles", "label_normalized": "Goodwill and intangibles", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 9870.0, "raw": "9,870"}, {"normalized": 9870.0, "raw": "9,870"}]},
            {"label_raw": "Other assets", "label_normalized": "Other assets", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 15720.0, "raw": "15,720"}, {"normalized": 14570.0, "raw": "14,570"}]},
            {"label_raw": "Total Assets", "label_normalized": "Total Assets", "row_type": "total", "indent_level": 0, "canonical_key": "total_assets", "values": [{"normalized": 266000.0, "raw": "266,000"}, {"normalized": 245000.0, "raw": "245,000"}]},
            {"label_raw": "LIABILITIES", "label_normalized": "Liabilities", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Deposits", "label_normalized": "Deposits", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 185000.0, "raw": "185,000"}, {"normalized": 172000.0, "raw": "172,000"}]},
            {"label_raw": "Borrowings", "label_normalized": "Borrowings", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 42000.0, "raw": "42,000"}, {"normalized": 38500.0, "raw": "38,500"}]},
            {"label_raw": "Other liabilities", "label_normalized": "Other liabilities", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 12500.0, "raw": "12,500"}, {"normalized": 11200.0, "raw": "11,200"}]},
            {"label_raw": "Total Liabilities", "label_normalized": "Total Liabilities", "row_type": "total", "indent_level": 0, "canonical_key": "total_liabilities", "values": [{"normalized": 239500.0, "raw": "239,500"}, {"normalized": 221700.0, "raw": "221,700"}]},
            {"label_raw": "EQUITY", "label_normalized": "Equity", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Share capital", "label_normalized": "Share capital", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 12800.0, "raw": "12,800"}, {"normalized": 12400.0, "raw": "12,400"}]},
            {"label_raw": "Retained earnings", "label_normalized": "Retained earnings", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 13700.0, "raw": "13,700"}, {"normalized": 10900.0, "raw": "10,900"}]},
            {"label_raw": "Total Equity", "label_normalized": "Total Equity", "row_type": "total", "indent_level": 0, "canonical_key": "total_equity", "values": [{"normalized": 26500.0, "raw": "26,500"}, {"normalized": 23300.0, "raw": "23,300"}]},
        ],
    },
    "income_statement": {
        "statement_metadata": {
            "statement_title": "Consolidated Income Statement",
            "statement_title_raw": "Consolidated Income Statement",
            "currency": "AUD", "currency_symbol": "$", "unit": "millions",
        },
        "columns": [{"label": "Item"}, {"label": "FY2024"}, {"label": "FY2023"}],
        "rows": [
            {"label_raw": "REVENUE", "label_normalized": "Revenue", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Interest income", "label_normalized": "Interest income", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 18500.0, "raw": "18,500"}, {"normalized": 15200.0, "raw": "15,200"}]},
            {"label_raw": "Fee and commission income", "label_normalized": "Fee and commission income", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 3200.0, "raw": "3,200"}, {"normalized": 2900.0, "raw": "2,900"}]},
            {"label_raw": "Total operating revenue", "label_normalized": "Total operating revenue", "row_type": "subtotal", "indent_level": 0, "canonical_key": "total_operating_revenue", "values": [{"normalized": 21700.0, "raw": "21,700"}, {"normalized": 18100.0, "raw": "18,100"}]},
            {"label_raw": "EXPENSES", "label_normalized": "Expenses", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Interest expense", "label_normalized": "Interest expense", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": -9800.0, "raw": "-9,800"}, {"normalized": -7500.0, "raw": "-7,500"}]},
            {"label_raw": "Operating costs", "label_normalized": "Operating costs", "row_type": "line_item", "indent_level": 1, "canonical_key": "operating_costs", "values": [{"normalized": -6200.0, "raw": "-6,200"}, {"normalized": -5800.0, "raw": "-5,800"}]},
            {"label_raw": "Impairment charges", "label_normalized": "Impairment charges", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": -1200.0, "raw": "-1,200"}, {"normalized": -950.0, "raw": "-950"}]},
            {"label_raw": "Operating profit", "label_normalized": "Operating profit", "row_type": "subtotal", "indent_level": 0, "canonical_key": "operating_profit", "values": [{"normalized": 4500.0, "raw": "4,500"}, {"normalized": 3850.0, "raw": "3,850"}]},
            {"label_raw": "Tax expense", "label_normalized": "Tax expense", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": -1350.0, "raw": "-1,350"}, {"normalized": -1155.0, "raw": "-1,155"}]},
            {"label_raw": "Net income", "label_normalized": "Net income", "row_type": "total", "indent_level": 0, "canonical_key": "net_income", "values": [{"normalized": 3150.0, "raw": "3,150"}, {"normalized": 2695.0, "raw": "2,695"}]},
        ],
    },
    "cash_flow": {
        "statement_metadata": {
            "statement_title": "Consolidated Cash Flow Statement",
            "statement_title_raw": "Consolidated Cash Flow Statement",
            "currency": "AUD", "currency_symbol": "$", "unit": "millions",
        },
        "columns": [{"label": "Item"}, {"label": "FY2024"}, {"label": "FY2023"}],
        "rows": [
            {"label_raw": "OPERATING ACTIVITIES", "label_normalized": "Operating Activities", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Net income", "label_normalized": "Net income", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 3150.0, "raw": "3,150"}, {"normalized": 2695.0, "raw": "2,695"}]},
            {"label_raw": "Depreciation and amortisation", "label_normalized": "Depreciation and amortisation", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": 850.0, "raw": "850"}, {"normalized": 790.0, "raw": "790"}]},
            {"label_raw": "Net cash from operating activities", "label_normalized": "Net cash from operating activities", "row_type": "subtotal", "indent_level": 0, "values": [{"normalized": 5200.0, "raw": "5,200"}, {"normalized": 4800.0, "raw": "4,800"}]},
            {"label_raw": "INVESTING ACTIVITIES", "label_normalized": "Investing Activities", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Capital expenditure", "label_normalized": "Capital expenditure", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": -920.0, "raw": "-920"}, {"normalized": -780.0, "raw": "-780"}]},
            {"label_raw": "Net cash from investing", "label_normalized": "Net cash from investing", "row_type": "subtotal", "indent_level": 0, "values": [{"normalized": -920.0, "raw": "-920"}, {"normalized": -780.0, "raw": "-780"}]},
            {"label_raw": "FINANCING ACTIVITIES", "label_normalized": "Financing Activities", "row_type": "section_header", "indent_level": 0, "values": []},
            {"label_raw": "Dividends paid", "label_normalized": "Dividends paid", "row_type": "line_item", "indent_level": 1, "values": [{"normalized": -2060.0, "raw": "-2,060"}, {"normalized": -1850.0, "raw": "-1,850"}]},
            {"label_raw": "Net cash from financing", "label_normalized": "Net cash from financing", "row_type": "subtotal", "indent_level": 0, "values": [{"normalized": -3060.0, "raw": "-3,060"}, {"normalized": -2850.0, "raw": "-2,850"}]},
            {"label_raw": "Net increase in cash", "label_normalized": "Net increase in cash", "row_type": "total", "indent_level": 0, "values": [{"normalized": 1220.0, "raw": "1,220"}, {"normalized": 1170.0, "raw": "1,170"}]},
        ],
    },
}

output = os.path.join(os.path.dirname(__file__), "..", "..", "Sample_Financial_Report.xlsx")
build_professional_excel(sample_result, output, title="Sample Bank \u2014 Financial Statement Review")
print(f"Generated: {output}")
print(f"Size: {os.path.getsize(output):,} bytes")
