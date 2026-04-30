"""
scripts/print_tables.py
-----------------------
Developer utility: print all three financial statements as formatted ASCII
tables to the console, reading from the output/*.json files.

Usage (run from the project root):
    python scripts/print_tables.py

Prerequisites:
    output/balance_sheet.json, output/income_statement.json,
    output/cash_flow.json must exist (produced by main.py or reprocess.py).
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Locate the output directory relative to this script's location.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def print_table(stype: str) -> None:
    """Print one statement as a formatted ASCII table."""
    stmt = json.loads((OUTPUT_DIR / f"{stype}.json").read_text(encoding="utf-8"))
    rows = stmt["rows"]
    cols = stmt["columns"]

    title = stype.upper().replace("_", " ")
    page_range = stmt.get("page_range", {})
    pages = f"pages {page_range.get('start', '?')}-{page_range.get('end', '?')}"
    nrows = len(rows)

    sep = "-" * 120
    print(f"\n{'='*120}")
    print(f"  {title}   |   {pages}   |   {nrows} rows")
    print(f"{'='*120}")

    # Column headers
    col_widths = [22] * len(cols)
    header = f"  {'Label':<68}"
    for i, c in enumerate(cols):
        short_name = c[:col_widths[i]]
        header += f"  {short_name:>{col_widths[i]}}"
    print(header)
    print(sep)

    for row in rows:
        label = row["label"]
        values = row.get("values", [])
        indent = "  " * row.get("indent_level", 0)
        prefix = "  "

        # Format values
        val_strs = []
        for v in values:
            val_strs.append(v if v else "")

        line = f"{prefix}{indent}{label:<{68 - len(indent)}}"
        for i, v in enumerate(val_strs):
            w = col_widths[i] if i < len(col_widths) else 22
            line += f"  {v:>{w}}"
        print(line)
    print(sep)


if __name__ == "__main__":
    for s in ["balance_sheet", "income_statement", "cash_flow"]:
        print_table(s)
