"""
extractor/pipeline.py — Extraction pipeline orchestrator.

Runs 5 stages in sequence:
  1. Analyze (CU Locator + markdown + enrichment)
  2. Select (score-based candidate selection)
  3. Extract (page-constrained table location + HTML parse)
  4. Enrich (translate + verify + clean)
  5. Validate (structural quality gates)

Public API:
  run(pdf_path, options) -> dict   (same shape as old _run_pipeline output)
"""
import logging
from typing import Optional

from .stages.contracts import (
    PipelineOptions,
    PipelineResult,
    QualityStatus,
)

logger = logging.getLogger(__name__)

STATEMENT_TYPES = ["balance_sheet", "income_statement", "cash_flow"]


def run(
    pdf_path: str,
    options: Optional[PipelineOptions] = None,
) -> dict:
    """Run the full extraction pipeline and return the result dict.

    This is the single entry point replacing function_app._run_pipeline().
    The return dict has the same shape as the old output:
      {
        "summary": [...],
        "balance_sheet": { v1.2 schema } | None,
        "income_statement": { v1.2 schema } | None,
        "cash_flow": { v1.2 schema } | None,
        "confidence": { ... },
      }
    """
    from .stages.analyze import run_analyze
    from .stages.select import run_select
    from .stages.extract import run_extract
    from .stages.enrich import run_enrich
    from .stages.validate import run_validate
    from .confidence_scorer import score_statement

    if options is None:
        options = PipelineOptions()

    # -- Stage 1: Analyze --
    logger.info("Pipeline Stage 1/5: Analyze")
    analyze_result = run_analyze(pdf_path, options)

    # -- Stage 2: Select --
    logger.info("Pipeline Stage 2/5: Select")
    select_result = run_select(analyze_result, options.requested_types)

    # Diagnostic: log select results for each statement type
    for stype in STATEMENT_TYPES:
        if stype in select_result.selected:
            c = select_result.selected[stype]
            scores = select_result.scores.get(stype, [])
            best_score = scores[0].score if scores else "?"
            logging.info(
                f"[PIPELINE] Select {stype}: SELECTED title_raw='{c.title_raw}' "
                f"pages={c.page_start}-{c.page_end} score={best_score}"
            )
        else:
            scores = select_result.scores.get(stype, [])
            if scores:
                logging.info(
                    f"[PIPELINE] Select {stype}: REJECTED "
                    f"{len(scores)} candidates, best_score={scores[0].score:.0f}, "
                    f"reason={scores[0].rejection_reason}, "
                    f"title='{scores[0].candidate.title_raw[:60]}'"
                )
            else:
                logging.info(f"[PIPELINE] Select {stype}: NO CANDIDATES from CU Locator")

    # -- Stage 3: Extract --
    logger.info("Pipeline Stage 3/5: Extract")
    extract_result = run_extract(
        select_result,
        analyze_result.markdown,
        analyze_result.page_map,
        analyze_result.pages,
        requested_types=options.requested_types,
    )

    # Diagnostic: log extract results
    for stype in STATEMENT_TYPES:
        if stype in extract_result.statements:
            es = extract_result.statements[stype]
            logging.info(
                f"[PIPELINE] Extract {stype}: OK rows={len(es.rows)} "
                f"pages={es.start_page}-{es.end_page}"
            )
        elif stype in extract_result.failures:
            logging.info(
                f"[PIPELINE] Extract {stype}: FAILED reason={extract_result.failures[stype]}"
            )
        elif stype in select_result.selected:
            logging.info(f"[PIPELINE] Extract {stype}: MISSING (selected but not extracted)")
        else:
            logging.info(f"[PIPELINE] Extract {stype}: SKIPPED (not selected)")

    # -- Stage 4: Enrich --
    logger.info("Pipeline Stage 4/5: Enrich")
    enrich_result = run_enrich(
        extract_result,
        {stype: c for stype, c in select_result.selected.items()},
        analyze_result.enrichment_lookup,
        analyze_result.markdown,
        options.source_file_name,
    )

    # -- Stage 5: Validate --
    logger.info("Pipeline Stage 5/5: Validate")
    validate_result = run_validate(enrich_result)

    # -- Build output dict (backward compatible) --
    output: dict = {"summary": []}

    for stype in STATEMENT_TYPES:
        if stype not in options.requested_types:
            output["summary"].append({
                "statement_type": stype,
                "status": "not_requested",
                "page_range": {"start": None, "end": None},
            })
            output[stype] = None
            continue

        # Check if statement was extracted
        validated = validate_result.statements.get(stype)
        extracted = extract_result.statements.get(stype)

        if validated:
            v12_doc = validated.v12_doc
            output[stype] = v12_doc
            output["summary"].append({
                "statement_type": stype,
                "status": "extracted",
                "page_range": {
                    "start": extracted.start_page if extracted else None,
                    "end": extracted.end_page if extracted else None,
                },
                "row_count": len(v12_doc.get("rows", [])),
                "column_count": len(v12_doc.get("columns", [])),
                "validation_status": v12_doc.get("validation", {}).get("status"),
                "quality_score": validated.quality_score,
                "quality_status": validated.status.value,
            })
            logger.info(
                f"{stype}: {len(v12_doc.get('rows', []))} rows, "
                f"quality={validated.quality_score:.2f} ({validated.status.value})"
            )
        elif stype in extract_result.failures:
            reason = extract_result.failures[stype]
            status = "found_but_not_extracted" if reason == "could_not_locate_in_markdown" else "found_but_empty"
            candidate = select_result.selected.get(stype)
            output["summary"].append({
                "statement_type": stype,
                "status": status,
                "page_range": {
                    "start": candidate.page_start if candidate else None,
                    "end": candidate.page_end if candidate else None,
                },
            })
            output[stype] = None
        else:
            output["summary"].append({
                "statement_type": stype,
                "status": "not_found",
                "page_range": {"start": None, "end": None},
            })
            output[stype] = None

    # -- Confidence scoring (existing module, reused as-is) --
    confidence = {}
    for stype in STATEMENT_TYPES:
        stmt = output.get(stype)
        if stmt and isinstance(stmt, dict) and stmt.get("rows"):
            confidence[stype] = score_statement(stmt, stype)
        else:
            confidence[stype] = {
                "score": 0.0, "level": "low",
                "signals": {}, "flagged_rows": [],
            }
    output["confidence"] = confidence

    return output
