"""
Stage 1: Analyze — CU Locator + markdown + page map.
                    OR
                    Document Intelligence + markdown + LLM classification.
                    OR
                    Textract + adapter + LLM classification.
                    OR
                    pdfplumber (local) + adapter + LLM classification.

Backend is selected by PipelineOptions.backend:
    "cu", "document_intelligence", "textract", or "pdfplumber".

Wraps existing cu_client.analyze_document() calls and parses the
CU Locator response into typed CandidateStatement objects.
"""
import logging
from typing import Optional

from .contracts import AnalyzeResult, CandidateStatement, PipelineOptions

logger = logging.getLogger(__name__)


def parse_locator_statements(locator_result: dict) -> list[CandidateStatement]:
    """Extract CandidateStatement objects from the CU locator response.

    This is a typed version of the old _parse_locator_statements() in function_app.py.
    """
    contents = locator_result.get("result", {}).get("contents", [])
    if not contents:
        return []

    fields = contents[0].get("fields", {})
    stmts = fields.get("statements", {}).get("valueArray", [])

    results = []
    for s in stmts:
        props = s.get("valueObject", {})

        def _str(key):
            return props.get(key, {}).get("valueString")

        def _int(key):
            return props.get(key, {}).get("valueInteger")

        def _bool(key):
            return props.get(key, {}).get("valueBoolean")

        results.append(CandidateStatement(
            statement_type=_str("statement_type") or "",
            title_raw=_str("title_raw"),
            title_english=_str("title_english"),
            page_start=_int("page_start"),
            page_end=_int("page_end"),
            company_name=_str("company_name"),
            company_name_raw=_str("company_name_raw"),
            report_language=_str("report_language"),
            currency=_str("currency"),
            unit=_str("unit"),
            is_consolidated=_bool("is_consolidated"),
            accounting_standard=_str("accounting_standard"),
        ))

    return results


def _run_analyze_cu(
    pdf_path: str,
    options: PipelineOptions,
) -> AnalyzeResult:
    """Original CU backend — unchanged.

    Args:
        pdf_path: Path to the PDF file on disk.
        options: Pipeline options (enrichment flag, etc.).

    Returns:
        AnalyzeResult with candidates, markdown, pages, page_map, enrichment_lookup.
    """
    from extractor.cu_client import analyze_document
    from extractor.statement_detector import _build_page_map
    from extractor.enrichment import build_enrichment_lookup

    # Step 1: CU Locator
    logger.info("Stage 1 (Analyze): Running CU Locator")
    locator_result = analyze_document("financial-statement-locator", pdf_path)

    candidates = parse_locator_statements(locator_result)

    # Step 2: Extract markdown and pages
    contents = locator_result.get("result", {}).get("contents", [])
    markdown = contents[0].get("markdown", "") if contents else ""
    pages = contents[0].get("pages", []) if contents else []
    page_map = _build_page_map(pages)

    # Step 3: CU Extractor for enrichment (optional)
    enrichment_lookup = {}
    if options.use_enrichment:
        logger.info("Stage 1 (Analyze): Running CU Extractor for enrichment")
        try:
            extractor_result = analyze_document(
                "financial-statement-extractor", pdf_path
            )
            enrichment_lookup = build_enrichment_lookup(extractor_result)
        except Exception as e:
            logger.warning(f"Enrichment failed, continuing without: {e}")

    logger.info(
        f"Stage 1 (Analyze): {len(candidates)} candidates, "
        f"{len(markdown)} chars markdown, {len(pages)} pages"
    )

    return AnalyzeResult(
        candidates=candidates,
        markdown=markdown,
        pages=pages,
        page_map=page_map,
        enrichment_lookup=enrichment_lookup,
    )


def _run_analyze_textract(
    pdf_path: str,
    options: PipelineOptions,
) -> AnalyzeResult:
    """Textract backend — adapter converts blocks to AnalyzeResult."""
    from extractor.textract_client import analyze_document
    from extractor.textract_adapter import (
        reconstruct_markdown,
        build_page_map,
        classify_statements_with_llm,
    )

    logger.info("Stage 1 (Analyze): Running AWS Textract")
    textract_result = analyze_document(pdf_path)
    blocks = textract_result.get("Blocks", [])

    # Reconstruct markdown with embedded HTML tables
    markdown = reconstruct_markdown(blocks)
    page_map = build_page_map(blocks, markdown)

    # Classify statements via LLM
    logger.info("Stage 1 (Analyze): Classifying statements via LLM")
    stmt_classifications = classify_statements_with_llm(markdown)

    candidates = []
    for s in stmt_classifications:
        candidates.append(CandidateStatement(
            statement_type=s.get("statement_type", ""),
            title_raw=s.get("title_raw"),
            title_english=s.get("title_raw"),  # LLM already returns English
            page_start=s.get("page_start"),
            page_end=s.get("page_end"),
            company_name=s.get("company_name"),
            company_name_raw=s.get("company_name"),
            report_language=s.get("report_language"),
            currency=s.get("currency"),
            unit=s.get("unit"),
            is_consolidated=s.get("is_consolidated"),
            accounting_standard=s.get("accounting_standard"),
        ))

    logger.info(
        f"Stage 1 (Analyze): {len(candidates)} candidates, "
        f"{len(markdown)} chars markdown, page_map entries: {len(page_map)}"
    )

    return AnalyzeResult(
        candidates=candidates,
        markdown=markdown,
        pages=[],  # Textract doesn't use CU's page span format
        page_map=page_map,
        enrichment_lookup={},  # LLM fallback handles enrichment in Stage 4
    )


def _run_analyze_pdfplumber(
    pdf_path: str,
    options: PipelineOptions,
) -> AnalyzeResult:
    """pdfplumber backend — local extraction, no cloud service."""
    from extractor.pdfplumber_client import extract_document
    from extractor.pdfplumber_adapter import (
        reconstruct_markdown,
        build_page_map,
        classify_statements_with_llm,
    )

    logger.info("Stage 1 (Analyze): Running pdfplumber (local)")
    pdfplumber_result = extract_document(pdf_path)

    markdown = reconstruct_markdown(pdfplumber_result)
    page_map = build_page_map(pdfplumber_result, markdown)

    logger.info("Stage 1 (Analyze): Classifying statements via LLM")
    stmt_classifications = classify_statements_with_llm(markdown)

    candidates = []
    for s in stmt_classifications:
        candidates.append(CandidateStatement(
            statement_type=s.get("statement_type", ""),
            title_raw=s.get("title_raw"),
            title_english=s.get("title_raw"),
            page_start=s.get("page_start"),
            page_end=s.get("page_end"),
            company_name=s.get("company_name"),
            company_name_raw=s.get("company_name"),
            report_language=s.get("report_language"),
            currency=s.get("currency"),
            unit=s.get("unit"),
            is_consolidated=s.get("is_consolidated"),
            accounting_standard=s.get("accounting_standard"),
        ))

    logger.info(
        f"Stage 1 (Analyze): {len(candidates)} candidates, "
        f"{len(markdown)} chars markdown, page_map entries: {len(page_map)}"
    )

    return AnalyzeResult(
        candidates=candidates,
        markdown=markdown,
        pages=[],
        page_map=page_map,
        enrichment_lookup={},
    )


def _run_analyze_document_intelligence(
    pdf_path: str,
    options: PipelineOptions,
) -> AnalyzeResult:
    """Azure Document Intelligence backend — prebuilt-layout with markdown output.

    DI returns markdown with embedded HTML tables natively, so no complex
    adapter is needed.  Auth is via Managed Identity (DefaultAzureCredential).
    """
    from extractor.di_client import analyze_document
    from extractor.di_adapter import build_page_map, classify_statements_with_llm

    logger.info("Stage 1 (Analyze): Running Azure Document Intelligence")
    di_result = analyze_document(pdf_path)

    # DI markdown output already contains HTML tables
    markdown = di_result.get("content", "")
    page_map = build_page_map(di_result, markdown)

    # Classify statements via LLM (same approach as Textract/pdfplumber)
    logger.info("Stage 1 (Analyze): Classifying statements via LLM")
    stmt_classifications = classify_statements_with_llm(markdown)

    candidates = []
    for s in stmt_classifications:
        candidates.append(CandidateStatement(
            statement_type=s.get("statement_type", ""),
            title_raw=s.get("title_raw"),
            title_english=s.get("title_raw"),
            page_start=s.get("page_start"),
            page_end=s.get("page_end"),
            company_name=s.get("company_name"),
            company_name_raw=s.get("company_name"),
            report_language=s.get("report_language"),
            currency=s.get("currency"),
            unit=s.get("unit"),
            is_consolidated=s.get("is_consolidated"),
            accounting_standard=s.get("accounting_standard"),
        ))

    logger.info(
        f"Stage 1 (Analyze): {len(candidates)} candidates, "
        f"{len(markdown)} chars markdown, page_map entries: {len(page_map)}"
    )

    return AnalyzeResult(
        candidates=candidates,
        markdown=markdown,
        pages=[],  # DI doesn't use CU's page span format
        page_map=page_map,
        enrichment_lookup={},  # LLM fallback handles enrichment in Stage 4
    )


def run_analyze(
    pdf_path: str,
    options: PipelineOptions,
) -> AnalyzeResult:
    """Run Stage 1 — delegates to backend based on options.backend."""
    if options.backend == "document_intelligence":
        return _run_analyze_document_intelligence(pdf_path, options)
    elif options.backend == "textract":
        return _run_analyze_textract(pdf_path, options)
    elif options.backend == "pdfplumber":
        return _run_analyze_pdfplumber(pdf_path, options)
    return _run_analyze_cu(pdf_path, options)
