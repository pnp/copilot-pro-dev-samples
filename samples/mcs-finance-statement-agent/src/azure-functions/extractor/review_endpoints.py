"""
extractor/review_endpoints.py
------------------------------
Business logic for HITL review endpoints:
  - /build-review-card  — generate Adaptive Card JSON for statement review
  - /parse-card-submission — advance session state from card payload
  - /apply-corrections — merge analyst corrections into extraction result

These endpoints implement a session-state-driven review flow where the
backend owns all review logic. The CPS topic just shuttles sessionState
and card JSON back and forth.

Public API:
    handle_build_review_card(job_id, session_state_str) -> (status_code, dict)
    handle_parse_card_submission(session_state_str, payload_raw) -> (status_code, dict)
    handle_apply_corrections(job_id, session_state_str) -> (status_code, dict)
"""

import json
import logging

from extractor.job_store import (
    load_job, delete_job, parse_stmt_from_result,
    STATEMENT_TYPES, SNAKE_TO_CAMEL,
)

logger = logging.getLogger(__name__)

# Unit display names for the navigator card
_UNIT_DISPLAY = {
    "元": "Yuan (ones)", "千元": "Thousands (CNY)", "万元": "Ten-thousands (CNY)",
    "百万元": "Millions (CNY)", "亿元": "Hundred-millions (CNY)",
    "ones": "Ones", "thousands": "Thousands", "millions": "Millions",
    "billions": "Billions",
}


# ---------------------------------------------------------------------------
# /build-review-card
# ---------------------------------------------------------------------------

def handle_build_review_card(
    job_id: str, session_state_str: str
) -> tuple[int, dict]:
    """Generate an Adaptive Card JSON payload for HITL review.

    On first call (empty sessionState): initialises session state from
    confidence data and returns the navigator card with extraction summary.

    On subsequent calls: uses session state to determine which statement
    card to build (paginated review flow).
    """
    from extractor.card_builder import (
        build_navigator_card,
        build_statement_review_card,
        init_session_state,
    )

    job = load_job(job_id)
    if not job or job.get("status") != "completed":
        return 404, {"error": f"Job {job_id} not found"}

    result = job.get("result", {})

    # Parse confidence data
    confidence_str = result.get("confidence") or "{}"
    confidence = json.loads(confidence_str) if isinstance(confidence_str, str) else confidence_str

    # --- First call: return navigator card ---
    if not session_state_str or session_state_str.strip() in ('{}', '"{}"'):
        available = [
            stype for stype in STATEMENT_TYPES
            if parse_stmt_from_result(result, stype) is not None
        ]
        session_state_str = init_session_state(
            confidence, job_id=job_id, available_statements=available,
        )

        # Extract metadata from first available statement
        company_name = result.get("companyName") or result.get("company_name", "Unknown")
        currency = "USD"
        unit = "ones"
        for stype in STATEMENT_TYPES:
            stmt = parse_stmt_from_result(result, stype)
            if stmt and isinstance(stmt, dict):
                meta = stmt.get("statement_metadata", {})
                currency = meta.get("currency", currency)
                raw_unit = meta.get("unit", unit)
                unit = _UNIT_DISPLAY.get(raw_unit, raw_unit)
                break

        summary_str = result.get("summary", "[]")
        summary = json.loads(summary_str) if isinstance(summary_str, str) else summary_str

        card = build_navigator_card(company_name, currency, unit, confidence, summary, job_id=job_id)
        return 200, {
            "cardJson": json.dumps(card, ensure_ascii=False),
            "sessionState": session_state_str,
        }

    # --- Subsequent calls: build statement review card ---
    try:
        state = json.loads(session_state_str)
    except (json.JSONDecodeError, TypeError):
        return 400, {"error": "Malformed sessionState"}

    step = state.get("step", 1)
    statements = state.get("statements", [])
    total_steps = len(statements)

    if step < 1 or step > total_steps:
        return 400, {"error": f"Invalid step {step} for {total_steps} statements"}

    stype = statements[step - 1]
    stmt = parse_stmt_from_result(result, stype)
    if not stmt:
        return 404, {"error": f"Statement {stype} not found in job"}

    confidence_entry = confidence.get(stype, {"score": 0, "level": "low", "flagged_rows": []})
    corrections_for_stmt = state.get("corrections", {}).get(stype, {})

    card = build_statement_review_card(
        statement_type=stype,
        statement_json=stmt,
        confidence_entry=confidence_entry,
        corrections=corrections_for_stmt,
        step_num=step,
        total_steps=total_steps,
        editable=state.get("editable", False),
        edit_all=state.get("editAll", False),
        edit_all_page=state.get("editAllPage", 0),
    )

    return 200, {
        "cardJson": json.dumps(card, ensure_ascii=False),
        "sessionState": session_state_str,
    }


# ---------------------------------------------------------------------------
# /parse-card-submission
# ---------------------------------------------------------------------------

def handle_parse_card_submission(
    session_state_str: str, payload_raw: str | dict
) -> tuple[int, dict]:
    """Parse an Adaptive Card submission and advance the session state machine.

    Resolves the current statement from sessionState, diffs corrections,
    and returns a topic-facing action (continue/done/skip) plus updated state.
    """
    from extractor.card_builder import advance_session_state

    if not session_state_str:
        return 400, {"error": "Missing sessionState"}

    # Parse payload (topic sends as JSON string)
    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = payload_raw
    if not isinstance(payload, dict):
        payload = {}

    logger.info(f"parse-card-submission: sessionState={session_state_str[:200]}, payload={json.dumps(payload)[:200]}")

    # Resolve statement JSON from blob (needed for correction diffing)
    try:
        state = json.loads(session_state_str)
    except (json.JSONDecodeError, TypeError):
        return 400, {"error": "Malformed sessionState"}

    statement_json = None
    if state.get("phase") == "review":
        step = state.get("step", 0)
        statements = state.get("statements", [])
        if 0 < step <= len(statements):
            stype = statements[step - 1]
            job_id = state.get("jobId") or payload.get("jobId")
            if job_id:
                job = load_job(job_id)
                if job and job.get("status") == "completed":
                    statement_json = parse_stmt_from_result(job.get("result", {}), stype)
            if statement_json is None:
                logger.warning(
                    f"parse-card-submission: could not load statement for step={step}"
                )

    topic_action, updated_state = advance_session_state(session_state_str, payload, statement_json)

    return 200, {
        "action": topic_action,
        "sessionState": updated_state,
    }


# ---------------------------------------------------------------------------
# /apply-corrections
# ---------------------------------------------------------------------------

def handle_apply_corrections(
    job_id: str, session_state_str: str
) -> tuple[int, dict]:
    """Apply accumulated analyst corrections to a cached extraction result.

    Corrections are stored in sessionState across all reviewed statements.
    Returns the corrected statement JSONs ready for Excel generation.
    """
    # Parse session state
    try:
        state = json.loads(session_state_str) if session_state_str else {}
    except (json.JSONDecodeError, TypeError):
        return 400, {"error": "Malformed sessionState"}
    corrections = state.get("corrections", {})

    # Load cached result
    job = load_job(job_id)
    if not job or job.get("status") != "completed":
        return 404, {"error": f"Job {job_id} not found or not completed"}

    result = job.get("result", {})

    # Apply corrections per statement
    from extractor.corrections import apply_corrections as _apply
    for stype in STATEMENT_TYPES:
        stmt = parse_stmt_from_result(result, stype)
        stmt_corrections = corrections.get(stype, {})
        if stmt and stmt_corrections:
            stmt = _apply(stmt, stmt_corrections)
        camel_key = SNAKE_TO_CAMEL.get(stype, stype)
        result[camel_key] = json.dumps(stmt, ensure_ascii=False) if stmt else "null"

    # Build final payload
    payload = {
        "status": "corrected",
        "companyName": result.get("companyName") or result.get("company_name", "Unknown_Company"),
        "summary": result.get("summary", "[]"),
        "balanceSheet": result.get("balanceSheet") or result.get("balance_sheet", "null"),
        "incomeStatement": result.get("incomeStatement") or result.get("income_statement", "null"),
        "cashFlow": result.get("cashFlow") or result.get("cash_flow", "null"),
    }

    # Clean up cached job
    delete_job(job_id)

    return 200, payload
