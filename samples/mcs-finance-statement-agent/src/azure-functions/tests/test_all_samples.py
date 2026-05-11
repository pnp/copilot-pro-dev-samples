"""Run extraction pipeline on all sample PDFs and report results."""
import os, sys, logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load env vars from .env file (never hardcode keys)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
os.environ.setdefault("AZURE_CU_ENDPOINT", "https://placeholder.cognitiveservices.azure.com")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

logging.basicConfig(level=logging.WARNING, format="%(message)s")

from extractor.stages.contracts import PipelineOptions
from extractor.pipeline import run as run_pipeline

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "samples")

pdfs = [f for f in os.listdir(SAMPLES_DIR) if f.endswith(".pdf")]

print(f"Testing {len(pdfs)} sample PDFs\n")
print(f"{'PDF':<55} {'BS':>5} {'IS':>5} {'CF':>5} {'Status'}")
print("-" * 85)

for pdf in sorted(pdfs):
    pdf_path = os.path.join(SAMPLES_DIR, pdf)
    short_name = pdf[:52] + "..." if len(pdf) > 55 else pdf

    try:
        result = run_pipeline(pdf_path, PipelineOptions())
        bs = result.get("balance_sheet")
        is_ = result.get("income_statement")
        cf = result.get("cash_flow")

        bs_rows = len(bs.get("rows", [])) if bs else 0
        is_rows = len(is_.get("rows", [])) if is_ else 0
        cf_rows = len(cf.get("rows", [])) if cf else 0

        missing = []
        if bs_rows == 0: missing.append("BS")
        if is_rows == 0: missing.append("IS")
        if cf_rows == 0: missing.append("CF")

        status = "OK" if not missing else f"MISSING: {','.join(missing)}"
        print(f"{short_name:<55} {bs_rows:>5} {is_rows:>5} {cf_rows:>5} {status}")

    except Exception as e:
        print(f"{short_name:<55} {'ERR':>5} {'ERR':>5} {'ERR':>5} {str(e)[:30]}")
