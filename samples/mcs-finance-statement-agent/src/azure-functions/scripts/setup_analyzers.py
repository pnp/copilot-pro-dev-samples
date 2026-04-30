"""
scripts/setup_analyzers.py
--------------------------
Creates (or updates) the custom Content Understanding analyzers on your
Azure resource.  Run this once before using the new pipeline.

Usage:
    python scripts/setup_analyzers.py           # create both analyzers
    python scripts/setup_analyzers.py --list    # list existing analyzers
    python scripts/setup_analyzers.py --delete  # delete both analyzers

Prerequisites:
    AZURE_CU_ENDPOINT must be set in .env (auth via managed identity)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from extractor.cu_client import (
    create_analyzer,
    get_analyzer,
    list_analyzers,
    delete_analyzer,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "analyzer_templates"

ANALYZERS = {
    "financial-statement-locator": TEMPLATE_DIR / "financial_statement_locator.json",
    "financial-statement-extractor": TEMPLATE_DIR / "financial_statement_extractor.json",
}


def cmd_create():
    """Create or update both analyzers."""
    for analyzer_id, template_path in ANALYZERS.items():
        print(f"\n{'='*60}")
        print(f"Creating analyzer: {analyzer_id}")
        print(f"Template: {template_path.name}")
        print(f"{'='*60}")

        template = json.loads(template_path.read_text(encoding="utf-8"))

        # Check if it already exists.
        existing = get_analyzer(analyzer_id)
        if existing:
            print(f"  Analyzer already exists. Updating...")
        else:
            print(f"  Creating new analyzer...")

        try:
            result = create_analyzer(analyzer_id, template)
            status = result.get("status", "unknown")
            print(f"  Result: {status}")
            if status == "succeeded":
                print(f"  Analyzer '{analyzer_id}' is ready.")
            elif status == "created":
                print(f"  Analyzer '{analyzer_id}' created (may need a moment to become active).")
            else:
                print(f"  Full response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print(f"\nDone. Both analyzers should now be available on your Azure resource.")


def cmd_list():
    """List all analyzers on the resource."""
    analyzers = list_analyzers()
    if not analyzers:
        print("No analyzers found.")
        return
    print(f"\n{len(analyzers)} analyzer(s) found:\n")
    for a in analyzers:
        aid = a.get("analyzerId", "?")
        desc = a.get("description", "")[:60]
        status = a.get("status", "?")
        print(f"  {aid:<40} status={status:<12} {desc}")


def cmd_delete():
    """Delete both financial statement analyzers."""
    for analyzer_id in ANALYZERS:
        print(f"Deleting: {analyzer_id}...")
        try:
            delete_analyzer(analyzer_id)
            print(f"  Deleted.")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage CU custom analyzers")
    parser.add_argument("--list", action="store_true", help="List existing analyzers")
    parser.add_argument("--delete", action="store_true", help="Delete both analyzers")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.delete:
        cmd_delete()
    else:
        cmd_create()
