"""Debug script: run Xiamen PDF through pipeline stages to find IS detection failure."""
import os, sys, json, logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load env vars from .env file (never hardcode keys)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
os.environ.setdefault("AZURE_CU_ENDPOINT", "https://placeholder.cognitiveservices.azure.com")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

logging.basicConfig(level=logging.INFO, format="%(message)s")

from extractor.stages.contracts import PipelineOptions
from extractor.stages.analyze import run_analyze
from extractor.stages.select import run_select
from extractor.stages.extract import run_extract

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "samples",
                        "Xiamen ITG Group Corp.,Ltd_QR_2025-09-30T00_00_00_Chinese.pdf")

print(f"PDF: {PDF_PATH}")
print(f"Exists: {os.path.exists(PDF_PATH)}")
print()

options = PipelineOptions()

# Stage 1: Analyze
print("=" * 60)
print("STAGE 1: ANALYZE")
print("=" * 60)
analyze_result = run_analyze(PDF_PATH, options)
print(f"Candidates: {len(analyze_result.candidates)}")
for c in analyze_result.candidates:
    print(f"  type={c.statement_type}, title_raw='{c.title_raw.encode('ascii','replace').decode()}', "
          f"title_en='{c.title_english}', pages={c.page_start}-{c.page_end}, "
          f"consolidated={c.is_consolidated}")
print(f"Markdown length: {len(analyze_result.markdown)}")
print()

# Stage 2: Select
print("=" * 60)
print("STAGE 2: SELECT")
print("=" * 60)
select_result = run_select(analyze_result, options.requested_types)
for stype in ["balance_sheet", "income_statement", "cash_flow"]:
    if stype in select_result.selected:
        c = select_result.selected[stype]
        scores = select_result.scores.get(stype, [])
        print(f"  {stype}: SELECTED score={scores[0].score if scores else '?'} "
              f"title='{c.title_raw}' pages={c.page_start}-{c.page_end}")
    else:
        scores = select_result.scores.get(stype, [])
        if scores:
            for sc in scores:
                print(f"  {stype}: REJECTED score={sc.score:.0f} reason={sc.rejection_reason} "
                      f"title='{sc.candidate.title_raw[:60]}'")
        else:
            print(f"  {stype}: NO CANDIDATES")
print()

# Stage 3: Extract
print("=" * 60)
print("STAGE 3: EXTRACT")
print("=" * 60)
extract_result = run_extract(
    select_result, analyze_result.markdown,
    analyze_result.page_map, analyze_result.pages,
    requested_types=options.requested_types,
)
for stype in ["balance_sheet", "income_statement", "cash_flow"]:
    if stype in extract_result.statements:
        es = extract_result.statements[stype]
        print(f"  {stype}: OK rows={len(es.rows)} pages={es.start_page}-{es.end_page}")
    elif stype in extract_result.failures:
        print(f"  {stype}: FAILED reason={extract_result.failures[stype]}")
    else:
        print(f"  {stype}: SKIPPED (not selected)")

# Check for IS heading in markdown
print()
print("=" * 60)
print("MARKDOWN SEARCH FOR IS HEADINGS")
print("=" * 60)
md = analyze_result.markdown
for pattern in ["合并利润表", "利润表", "INCOME STATEMENT", "PROFIT OR LOSS", "STATEMENT OF PROFIT"]:
    idx = md.find(pattern)
    if idx >= 0:
        context = md[max(0, idx-50):idx+100].replace("\n", " ")
        print(f"  FOUND '{pattern}' at offset {idx}: ...{context}...")
    else:
        print(f"  NOT FOUND: '{pattern}'")
