"""
function_app.py
---------------
Azure Function HTTP router for the Financial Statement Extraction Pipeline.

This file is a thin routing layer only — all business logic lives in the
extractor/ modules:

  extractor/extract_endpoints.py  — PDF extraction (upload, URL, polling)
  extractor/excel_endpoint.py     — Excel generation and download
  extractor/review_endpoints.py   — HITL review (Adaptive Cards, corrections)
  extractor/job_store.py          — Blob storage CRUD for job results

API Endpoints:
  POST /api/extract              — Submit PDF for extraction (async, returns jobId)
  POST /api/extract-by-url       — Submit PDF URL for extraction
  GET  /api/extract/status/{id}  — Poll extraction status and results
  POST /api/generate-excel       — Generate Excel workbook from results
  POST /api/build-review-card    — Build Adaptive Card for HITL review
  POST /api/parse-card-submission — Parse Adaptive Card submit payload
  POST /api/apply-corrections    — Apply analyst corrections
  GET  /api/fx-rate              — Fetch FX conversion rates
  GET  /api/health               — Health check
"""

import json
import logging
import time
import traceback
from datetime import datetime

import azure.functions as func

# ---------------------------------------------------------------------------
# Azure Function App instance
# ---------------------------------------------------------------------------

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ---------------------------------------------------------------------------
# POST /extract — submit PDF for async extraction
# ---------------------------------------------------------------------------

@app.route(route="extract", methods=["POST"])
def extract(req: func.HttpRequest) -> func.HttpResponse:
    """Accept a PDF upload and start async extraction. Returns 202 + jobId."""
    logging.info("Extract request received")
    try:
        status, body, headers = _import_extract().handle_extract(
            body=req.get_body(),
            files=req.files,
            form=req.form,
            params=dict(req.params),
            headers=dict(req.headers),
        )
        return func.HttpResponse(
            json.dumps(body, ensure_ascii=False),
            status_code=status, headers=headers, mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Failed to start extraction job")
        return _error_response(500, f"Failed to start job: {e}")


# ---------------------------------------------------------------------------
# POST /extract-by-url — submit PDF URL for async extraction
# ---------------------------------------------------------------------------

@app.route(route="extract-by-url", methods=["POST"])
def extract_by_url(req: func.HttpRequest) -> func.HttpResponse:
    """Accept a PDF download URL and start async extraction."""
    logging.info("Extract-by-url request received")
    try:
        body = req.get_json()
    except Exception:
        return _error_response(400, "Invalid JSON body")

    try:
        status, resp, headers = _import_extract().handle_extract_by_url(
            body=body, params=dict(req.params),
        )
        return func.HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status_code=status, headers=headers, mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Failed to start extraction job (via URL)")
        return _error_response(500, f"Failed to start job: {e}")


# ---------------------------------------------------------------------------
# GET /extract/status/{jobId} — poll for results
# ---------------------------------------------------------------------------

@app.route(route="extract/status/{jobId}", methods=["GET"],
           auth_level=func.AuthLevel.ANONYMOUS)
def extract_status(req: func.HttpRequest) -> func.HttpResponse:
    """Poll for extraction job status. Anonymous auth — jobId is the token."""
    job_id = req.route_params.get("jobId")
    status, body = _import_extract().handle_extract_status(job_id)
    return func.HttpResponse(
        json.dumps(body, ensure_ascii=False, indent=2),
        status_code=status, mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# POST /generate-excel — build Excel from extraction results
# ---------------------------------------------------------------------------

@app.route(route="generate-excel", methods=["POST"])
def generate_excel(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a formatted Excel workbook and return a download URL."""
    job_id = req.params.get("jobId")
    fx_target_currency = None
    fx_spot_rate = None
    fx_avg_rate = None
    fx_rate_date = ""
    try:
        body = req.get_json()
        if not job_id:
            job_id = body.get("jobId")
        fx_target_currency = body.get("fxTargetCurrency") or req.params.get("fxTargetCurrency")
        fx_spot_rate = body.get("fxSpotRate") or req.params.get("fxSpotRate")
        fx_avg_rate = body.get("fxAvgRate") or req.params.get("fxAvgRate")
        fx_rate_date = body.get("fxRateDate") or req.params.get("fxRateDate") or ""
    except Exception:
        pass

    if not job_id:
        return _error_response(400, "jobId is required")

    if fx_spot_rate:
        fx_spot_rate = float(fx_spot_rate)
    if fx_avg_rate:
        fx_avg_rate = float(fx_avg_rate)

    logging.info(f"generate-excel: building Excel for job {job_id}")
    try:
        from extractor.excel_endpoint import handle_generate_excel
        status, body = handle_generate_excel(
            job_id, fx_target_currency, fx_spot_rate, fx_avg_rate, fx_rate_date,
        )
        return func.HttpResponse(
            json.dumps(body, ensure_ascii=False),
            status_code=status, mimetype="application/json",
        )
    except Exception as e:
        logging.exception(f"generate-excel failed for job {job_id}")
        return _error_response(500, str(e))


# ---------------------------------------------------------------------------
# POST /build-review-card — Adaptive Card for HITL review
# ---------------------------------------------------------------------------

@app.route(route="build-review-card", methods=["POST"])
def build_review_card(req: func.HttpRequest) -> func.HttpResponse:
    """Generate an Adaptive Card JSON payload for HITL statement review."""
    try:
        body = req.get_json()
    except Exception:
        return _error_response(400, "Invalid JSON body")

    from extractor.review_endpoints import handle_build_review_card
    status, resp = handle_build_review_card(
        job_id=body.get("jobId"),
        session_state_str=body.get("sessionState", ""),
    )
    return func.HttpResponse(
        json.dumps(resp, ensure_ascii=False),
        status_code=status, mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# POST /parse-card-submission — advance review session state
# ---------------------------------------------------------------------------

@app.route(route="parse-card-submission", methods=["POST"])
def parse_card_submission_route(req: func.HttpRequest) -> func.HttpResponse:
    """Parse an Adaptive Card submission and advance the session state machine."""
    try:
        body = req.get_json()
    except Exception:
        return _error_response(400, "Invalid JSON body")

    try:
        from extractor.review_endpoints import handle_parse_card_submission
        status, resp = handle_parse_card_submission(
            session_state_str=body.get("sessionState", ""),
            payload_raw=body.get("payload", "{}"),
        )
        return func.HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status_code=status, mimetype="application/json",
        )
    except Exception as e:
        logging.exception(f"parse-card-submission error: {e}")
        return _error_response(500, f"Internal error: {e}")


# ---------------------------------------------------------------------------
# POST /apply-corrections — merge analyst corrections
# ---------------------------------------------------------------------------

@app.route(route="apply-corrections", methods=["POST"])
def apply_corrections(req: func.HttpRequest) -> func.HttpResponse:
    """Apply HITL analyst corrections and return corrected statement data."""
    try:
        body = req.get_json()
    except Exception:
        return _error_response(400, "Invalid JSON body")

    job_id = body.get("jobId")
    if not job_id:
        return _error_response(400, "Missing jobId")

    from extractor.review_endpoints import handle_apply_corrections
    status, resp = handle_apply_corrections(
        job_id=job_id,
        session_state_str=body.get("sessionState", "{}"),
    )
    return func.HttpResponse(
        json.dumps(resp, ensure_ascii=False),
        status_code=status, mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# GET /fx-rate — FX conversion rates
# ---------------------------------------------------------------------------

@app.route(route="fx-rate", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def fx_rate(req: func.HttpRequest) -> func.HttpResponse:
    """Fetch FX rates for currency conversion."""
    try:
        status, body = _import_extract().handle_fx_rate(dict(req.params))
        return func.HttpResponse(
            json.dumps(body), status_code=status, mimetype="application/json",
        )
    except Exception as e:
        logging.exception(f"FX rate fetch failed: {e}")
        return _error_response(500, str(e))


# ---------------------------------------------------------------------------
# GET /health — health check
# ---------------------------------------------------------------------------

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "version": "3.0.0",
            "schema_version": "1.2.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "active_jobs": 0,
        }),
        mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# GET /timeout-test — connector timeout diagnostic
# ---------------------------------------------------------------------------

@app.route(route="timeout-test", methods=["GET"])
def timeout_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test endpoint to measure connector timeout limits."""
    sleep_seconds = int(req.params.get("sleep", "10"))
    start = time.time()
    logging.info(f"timeout-test: sleeping for {sleep_seconds}s ...")
    time.sleep(sleep_seconds)
    elapsed = round(time.time() - start, 2)
    return func.HttpResponse(
        json.dumps({
            "status": "ok",
            "requested_sleep": sleep_seconds,
            "actual_elapsed": elapsed,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }),
        mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_response(status_code: int, message: str) -> func.HttpResponse:
    """Build a JSON error response."""
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code, mimetype="application/json",
    )


def _import_extract():
    """Lazy import of extract_endpoints to avoid circular imports."""
    from extractor import extract_endpoints
    return extract_endpoints
