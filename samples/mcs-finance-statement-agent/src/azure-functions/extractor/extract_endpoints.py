"""
extractor/extract_endpoints.py
-------------------------------
Business logic for extraction endpoints:
  - /extract         — accept PDF upload, start async extraction job
  - /extract-by-url  — accept PDF URL, download and start extraction
  - /extract/status  — poll for job results
  - /fx-rate         — fetch FX conversion rates

The extraction runs in a background thread. Results are stored in blob
storage via job_store. The CPS agent polls /extract/status until complete.

Public API:
    handle_extract(body, files, params, headers) -> (status_code, dict, headers)
    handle_extract_by_url(body, params) -> (status_code, dict, headers)
    handle_extract_status(job_id) -> (status_code, dict)
    handle_fx_rate(params) -> (status_code, dict)
    run_job(job_id, tmp_path, ...) — background thread target
"""

import base64
import json
import logging
import os
import tempfile
import threading
import uuid

from extractor.job_store import save_job, load_job, delete_job, build_response_payload, STATEMENT_TYPES
from extractor.pipeline import run as run_pipeline
from extractor.stages.contracts import PipelineOptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------

def run_job(
    job_id: str,
    tmp_path: str,
    use_enrichment: bool,
    requested_types: list[str],
    file_name: str,
):
    """Run the 5-stage extraction pipeline in a background thread.

    Saves the completed result (or failure) to blob storage. Cleans up
    the temp PDF file when done.
    """
    try:
        backend = os.environ.get("EXTRACTION_BACKEND", "cu")
        options = PipelineOptions(
            use_enrichment=use_enrichment,
            requested_types=requested_types,
            source_file_name=file_name,
            backend=backend,
        )
        result = run_pipeline(tmp_path, options)
        payload = build_response_payload(result)

        save_job(job_id, {"status": "completed", "result": payload})
        logger.info(f"Job {job_id} extraction completed, result saved to blob storage")

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        save_job(job_id, {"status": "failed", "error": str(e)})
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# /extract — PDF upload (multipart, JSON base64, or raw bytes)
# ---------------------------------------------------------------------------

def handle_extract(
    body: bytes,
    files: dict,
    form: dict,
    params: dict,
    headers: dict,
) -> tuple[int, dict, dict]:
    """Handle PDF extraction request. Supports multipart, JSON, or raw bytes.

    Returns (status_code, response_body, response_headers).
    """
    # Parse query params
    use_enrichment = params.get("enrichment", "true").lower() != "false"
    requested_types = params.get("statements", "")
    if requested_types:
        requested_types = [s.strip() for s in requested_types.split(",")]
    else:
        requested_types = list(STATEMENT_TYPES)

    content_type = headers.get("content-type", "").lower()

    # --- Get PDF bytes from request ---
    if "multipart/form-data" in content_type:
        uploaded_file = files.get("file")
        if not uploaded_file:
            return 400, {"error": "Missing 'file' in multipart form data"}, {}
        pdf_bytes = uploaded_file.read()
        file_name = form.get("fileName", uploaded_file.filename or "document.pdf")
        logger.info(f"Received multipart file: {file_name} ({len(pdf_bytes)} bytes)")

    elif "application/json" in content_type or body[:1] == b"{":
        payload = json.loads(body)
        file_url = payload.get("fileUrl") or payload.get("contentUrl")
        file_content = payload.get("fileContent")
        file_name = payload.get("fileName", "document.pdf")

        if file_content:
            if "," in file_content and file_content.index(",") < 100:
                file_content = file_content.split(",", 1)[1]
            pdf_bytes = base64.b64decode(file_content)
        elif file_url:
            import requests as http_requests
            download_resp = http_requests.get(file_url, timeout=120)
            download_resp.raise_for_status()
            pdf_bytes = download_resp.content
        else:
            return 400, {"error": "Missing fileUrl or fileContent"}, {}

    elif body and len(body) > 100:
        pdf_bytes = body
        file_name = "uploaded.pdf"

    else:
        return 400, {"error": "Send multipart file, JSON, or raw PDF bytes"}, {}

    # --- Start background job ---
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    save_job(job_id, {"status": "processing"})

    thread = threading.Thread(
        target=run_job,
        args=(job_id, tmp_path, use_enrichment, requested_types, file_name),
        daemon=True,
    )
    thread.start()
    logger.info(f"Job {job_id} started for {file_name}")

    return 202, {"jobId": job_id, "status": "processing"}, {
        "Location": f"/api/extract/status/{job_id}",
        "Retry-After": "5",
    }


# ---------------------------------------------------------------------------
# /extract-by-url — URL-based extraction
# ---------------------------------------------------------------------------

def handle_extract_by_url(body: dict, params: dict) -> tuple[int, dict, dict]:
    """Handle URL-based extraction. Downloads the PDF then starts async job.

    Returns (status_code, response_body, response_headers).
    """
    file_url = body.get("fileUrl") or body.get("contentUrl")
    file_name = body.get("fileName", "document.pdf")
    auth_token = body.get("authToken", "")

    if not file_url:
        return 400, {"error": "Missing fileUrl"}, {}

    use_enrichment = params.get("enrichment", "true").lower() != "false"
    requested_types = params.get("statements", "")
    if requested_types:
        requested_types = [s.strip() for s in requested_types.split(",")]
    else:
        requested_types = list(STATEMENT_TYPES)

    # Download PDF
    import requests as http_requests
    req_headers = {}
    if auth_token:
        req_headers["Authorization"] = f"Bearer {auth_token}"
    download_resp = http_requests.get(file_url, headers=req_headers, timeout=120)
    download_resp.raise_for_status()
    pdf_bytes = download_resp.content
    logger.info(f"Downloaded {file_name} from URL ({len(pdf_bytes)} bytes)")

    # Start background job
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    save_job(job_id, {"status": "processing"})

    thread = threading.Thread(
        target=run_job,
        args=(job_id, tmp_path, use_enrichment, requested_types, file_name),
        daemon=True,
    )
    thread.start()
    logger.info(f"Job {job_id} started for {file_name} (via URL)")

    return 202, {"jobId": job_id, "status": "processing"}, {
        "Location": f"/api/extract/status/{job_id}",
        "Retry-After": "5",
    }


# ---------------------------------------------------------------------------
# /extract/status/{jobId} — poll for results
# ---------------------------------------------------------------------------

def handle_extract_status(job_id: str) -> tuple[int, dict]:
    """Poll for extraction job status. Returns result when complete.

    The status endpoint uses anonymous auth — the job ID itself acts as
    the access token (unguessable UUID).
    """
    job = load_job(job_id)

    if not job:
        return 404, {"error": f"Job {job_id} not found"}

    if job["status"] == "processing":
        # Return empty fields so the connector schema stays consistent
        return 200, {
            "status": "processing",
            "companyName": "", "summary": "",
            "balanceSheet": "", "incomeStatement": "",
            "cashFlow": "", "confidence": "",
        }

    if job["status"] == "completed":
        result = job["result"]
        result["status"] = "completed"
        result["jobId"] = job_id
        return 200, result

    # Failed
    error = job.get("error", "Unknown error")
    delete_job(job_id)
    return 200, {"status": "failed", "error": error}


# ---------------------------------------------------------------------------
# /fx-rate — FX conversion rate lookup
# ---------------------------------------------------------------------------

# In-memory cache: "CNY-AUD-2025-09-30" -> rate dict
_fx_rate_cache: dict[str, dict] = {}


def handle_fx_rate(params: dict) -> tuple[int, dict]:
    """Fetch FX rates for currency conversion.

    Tries exchangerate.host first, falls back to open.er-api.com.
    Caches results in memory for the function app lifetime.
    """
    from_currency = params.get("from", "").upper()
    to_currency = params.get("to", "").upper()
    rate_date = params.get("date", "")
    period_start = params.get("period_start", "")

    if not from_currency or not to_currency:
        return 400, {"error": "Missing 'from' and 'to' query parameters"}

    if from_currency == to_currency:
        return 200, {
            "from": from_currency, "to": to_currency,
            "spot_rate": 1.0, "average_rate": 1.0,
            "date": rate_date, "source": "identity",
        }

    # Check cache
    cache_key = f"{from_currency}-{to_currency}-{rate_date}"
    if cache_key in _fx_rate_cache:
        logger.info(f"FX rate cache hit: {cache_key}")
        return 200, _fx_rate_cache[cache_key]

    import httpx

    # Fetch spot rate
    spot_url = (
        f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}&date={rate_date}"
        if rate_date else
        f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}"
    )
    logger.info(f"Fetching FX spot rate: {spot_url}")

    with httpx.Client(timeout=10) as client:
        spot_resp = client.get(spot_url)
        spot_data = spot_resp.json()

    spot_rate = spot_data.get("result") or spot_data.get("info", {}).get("rate")

    if spot_rate is None:
        # Fallback: exchangerate-api.com (free tier)
        fallback_url = f"https://open.er-api.com/v6/latest/{from_currency}"
        with httpx.Client(timeout=10) as client:
            fb_resp = client.get(fallback_url)
            fb_data = fb_resp.json()
        spot_rate = fb_data.get("rates", {}).get(to_currency)

    if spot_rate is None:
        return 502, {"error": f"Could not fetch rate for {from_currency}/{to_currency}"}

    # Average rate: compute from timeseries if period_start provided
    average_rate = spot_rate
    if period_start and rate_date:
        try:
            ts_url = f"https://api.exchangerate.host/timeseries?start_date={period_start}&end_date={rate_date}&source={from_currency}&currencies={to_currency}"
            with httpx.Client(timeout=15) as client:
                ts_resp = client.get(ts_url)
                ts_data = ts_resp.json()

            ts_rates = ts_data.get("quotes", {}) or ts_data.get("rates", {})
            if ts_rates:
                values = []
                for day_data in ts_rates.values():
                    if isinstance(day_data, dict):
                        val = day_data.get(f"{from_currency}{to_currency}") or day_data.get(to_currency)
                        if val:
                            values.append(float(val))
                    elif isinstance(day_data, (int, float)):
                        values.append(float(day_data))
                if values:
                    average_rate = round(sum(values) / len(values), 6)
                    logger.info(f"FX average rate computed from {len(values)} daily rates")
        except Exception as e:
            logger.warning(f"Could not compute average rate, using spot: {e}")

    result = {
        "from": from_currency, "to": to_currency,
        "spot_rate": round(float(spot_rate), 6),
        "average_rate": round(float(average_rate), 6),
        "date": rate_date, "source": "exchangerate.host",
    }

    _fx_rate_cache[cache_key] = result
    return 200, result
