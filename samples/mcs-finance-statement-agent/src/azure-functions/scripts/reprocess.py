"""
scripts/reprocess.py
--------------------
Developer utility: re-run statement detection and parsing against a cached
raw_result.json without hitting the Azure Content Understanding API again.

Useful for iterating on statement_detector.py changes without incurring API
costs or waiting for the analysis to complete.

Usage (run from the project root):
    python scripts/reprocess.py
    python scripts/reprocess.py --llm          # with LLM reconciliation

Prerequisites:
    output/raw_result.json must exist (produced by a previous main.py run).
"""

import argparse
import json
import sys
from pathlib import Path

# Allow importing the extractor package from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from extractor import locate_statements, build_statement_json, build_summary

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
STATEMENT_TYPES = ["balance_sheet", "cash_flow", "income_statement"]


def main(use_llm: bool = False) -> None:
    raw_path = OUTPUT_DIR / "raw_result.json"
    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found. Run main.py first to generate it.")
        sys.exit(1)

    raw_result = json.loads(raw_path.read_text(encoding="utf-8"))

    # Re-run location detection and parsing
    locations = locate_statements(raw_result, use_llm=use_llm)
    for stype in STATEMENT_TYPES:
        stmt = build_statement_json(stype, raw_result, locations.get(stype), use_llm=use_llm)
        (OUTPUT_DIR / f"{stype}.json").write_text(
            json.dumps(stmt, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(build_summary(locations), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Print a quick summary
    for stype in STATEMENT_TYPES:
        stmt = json.loads((OUTPUT_DIR / f"{stype}.json").read_text(encoding="utf-8"))
        pr = stmt.get("page_range", {})
        print(f"{stype}: {len(stmt['rows'])} rows, pages {pr.get('start')}-{pr.get('end')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reprocess cached Azure CU output")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM reconciliation pass (requires Azure OpenAI credentials in .env)",
    )
    args = parser.parse_args()
    main(use_llm=args.llm)
