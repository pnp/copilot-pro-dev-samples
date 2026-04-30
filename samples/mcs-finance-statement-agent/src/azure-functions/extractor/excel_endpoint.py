"""
extractor/excel_endpoint.py
----------------------------
Business logic for the /generate-excel endpoint.

Responsibilities:
  - Load extraction result from blob storage
  - Normalize key conventions (camelCase <-> snake_case)
  - Build professional Excel workbook via excel_formatter
  - Upload Excel to blob storage with SAS download URL
  - Build Adaptive Card with download link

Separated from function_app.py for single-responsibility.

Public API:
    handle_generate_excel(job_id, fx_params) -> (status_code, response_dict)
"""

import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import quote as url_quote

from extractor.job_store import load_job, get_container, STATEMENT_TYPES

logger = logging.getLogger(__name__)


def handle_generate_excel(
    job_id: str,
    fx_target_currency: str | None = None,
    fx_spot_rate: float | None = None,
    fx_avg_rate: float | None = None,
    fx_rate_date: str = "",
) -> tuple[int, dict]:
    """Generate Excel from a completed extraction job.

    Args:
        job_id: The extraction job ID (blob key).
        fx_target_currency: Optional target currency for FX conversion.
        fx_spot_rate: Spot rate for balance sheet items.
        fx_avg_rate: Average rate for IS/CF items.
        fx_rate_date: Date of the FX rates.

    Returns:
        (status_code, response_dict) tuple ready for HTTP response.
    """
    from extractor.excel_formatter import build_professional_excel

    # --- Load job from blob ---
    blob_data = load_job(job_id)
    if not blob_data or blob_data.get("status") != "completed":
        return 404, {"error": f"Job {job_id} not found or not completed"}

    result = blob_data.get("result", {})
    company = result.get("companyName", "Financial_Statements")

    # --- Parse JSON string fields ---
    for key in ["summary", "balanceSheet", "incomeStatement", "cashFlow",
                 "confidence", "balance_sheet", "income_statement", "cash_flow"]:
        val = result.get(key)
        if isinstance(val, str):
            try:
                result[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass

    # --- Normalize camelCase -> snake_case ---
    if "balanceSheet" in result and "balance_sheet" not in result:
        result["balance_sheet"] = result["balanceSheet"]
    if "incomeStatement" in result and "income_statement" not in result:
        result["income_statement"] = result["incomeStatement"]
    if "cashFlow" in result and "cash_flow" not in result:
        result["cash_flow"] = result["cashFlow"]

    title = f"{company} — Financial Statement Extraction"

    # --- Build Excel ---
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    build_professional_excel(
        result, tmp_path, title=title,
        fx_target_currency=fx_target_currency,
        fx_spot_rate=fx_spot_rate,
        fx_avg_rate=fx_avg_rate,
        fx_rate_date=fx_rate_date,
    )

    with open(tmp_path, "rb") as f:
        excel_bytes = f.read()
    os.unlink(tmp_path)

    # --- Sanitize filename (ASCII for Content-Disposition, UTF-8 fallback) ---
    safe_company = re.sub(r'[^\x20-\x7E]', '', company).strip() or "Financial_Statements"
    filename = f"{safe_company.replace(' ', '_')}_Review.xlsx"

    logger.info(f"generate-excel: built workbook ({len(excel_bytes)} bytes)")

    # --- Upload to blob storage ---
    from azure.storage.blob import ContentSettings
    container = get_container()
    blob_name = f"excel/{job_id}/{filename}"
    blob_client = container.get_blob_client(blob_name)

    ascii_disp = f'attachment; filename="{filename}"'
    utf8_filename = url_quote(f"{company.replace(' ', '_')}_Review.xlsx")
    content_disp = f"{ascii_disp}; filename*=UTF-8''{utf8_filename}"

    blob_client.upload_blob(
        excel_bytes,
        overwrite=True,
        content_settings=ContentSettings(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content_disposition=content_disp,
        ),
    )

    # --- Generate SAS download URL (24-hour expiry) ---
    download_url = _generate_sas_url(container, blob_name, blob_client)

    # --- Build Adaptive Card for CPS display ---
    card = _build_excel_card(company, filename, download_url)

    return 200, {
        "fileUrl": download_url,
        "fileName": filename,
        "cardJson": json.dumps(card, ensure_ascii=False),
    }


def _generate_sas_url(container, blob_name: str, blob_client) -> str:
    """Generate a SAS download URL for the uploaded Excel blob.

    Tries connection-string account key first, falls back to
    user delegation key for Managed Identity auth.
    """
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions

    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    start = datetime.now(timezone.utc) - timedelta(minutes=5)

    # Try connection-string account key
    conn_str = os.environ.get("AzureWebJobsStorage", "")
    account_key = None
    for part in conn_str.split(";"):
        if part.startswith("AccountKey="):
            account_key = part[len("AccountKey="):]
            break

    if account_key:
        sas = generate_blob_sas(
            account_name=container.account_name,
            container_name=container.container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
    else:
        # Managed Identity — user delegation key
        from azure.identity import ManagedIdentityCredential
        from azure.storage.blob import BlobServiceClient

        blob_uri = os.environ["AzureWebJobsStorage__blobServiceUri"]
        client_id = os.environ.get("AzureWebJobsStorage__clientId")
        credential = ManagedIdentityCredential(client_id=client_id)
        service = BlobServiceClient(blob_uri, credential=credential)
        udk = service.get_user_delegation_key(start, expiry)
        sas = generate_blob_sas(
            account_name=container.account_name,
            container_name=container.container_name,
            blob_name=blob_name,
            user_delegation_key=udk,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
            start=start,
        )

    return f"{blob_client.url}?{sas}"


def _build_excel_card(company: str, filename: str, download_url: str) -> dict:
    """Build an Adaptive Card with Excel download link for CPS display."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column", "width": "auto",
                        "items": [{"type": "Image", "url": "https://cdn-icons-png.flaticon.com/512/732/732220.png", "size": "Small"}],
                    },
                    {
                        "type": "Column", "width": "stretch",
                        "items": [{"type": "TextBlock", "text": "Excel Report Ready", "weight": "Bolder", "size": "Large", "wrap": True}],
                        "verticalContentAlignment": "Center",
                    },
                ],
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Company", "value": company},
                    {"title": "File", "value": filename},
                ],
            },
            {"type": "TextBlock", "text": "Link expires in 24 hours.", "size": "Small", "isSubtle": True, "wrap": True, "spacing": "Medium"},
        ],
        "actions": [
            {"type": "Action.OpenUrl", "title": "Download Excel", "url": download_url, "style": "positive"},
        ],
    }
