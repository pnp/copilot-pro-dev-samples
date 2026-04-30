"""
extractor/job_store.py
-----------------------
Blob-based job store for extraction results.

Responsibilities:
  - CRUD operations on extraction jobs in Azure Blob Storage
  - Building the response payload from pipeline results
  - Translating non-English company names to English via LLM

The Function App's managed identity (or connection string) is used for
blob access. Jobs are stored as JSON blobs in the 'extraction-jobs' container.

Public API:
    save_job(job_id, data)          — upsert a job blob
    load_job(job_id) -> dict | None — read a job blob
    delete_job(job_id)              — delete a job blob
    get_container()                 — get the blob container client
    build_response_payload(result)  — pipeline result -> API response dict
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Container client (lazy singleton)
# ---------------------------------------------------------------------------

_JOBS_CONTAINER = "extraction-jobs"
_container_client = None


def get_container():
    """Get or create the blob container client for job storage.

    Supports two auth modes:
      - Connection string (regular Consumption plan): AzureWebJobsStorage env var
      - Managed Identity (Flex Consumption plan): AzureWebJobsStorage__blobServiceUri
    """
    global _container_client
    if _container_client is None:
        from azure.storage.blob import BlobServiceClient

        conn_str = os.environ.get("AzureWebJobsStorage")
        if conn_str and conn_str.startswith("Default"):
            service = BlobServiceClient.from_connection_string(conn_str)
        else:
            from azure.identity import ManagedIdentityCredential
            blob_uri = os.environ["AzureWebJobsStorage__blobServiceUri"]
            client_id = os.environ.get("AzureWebJobsStorage__clientId")
            credential = ManagedIdentityCredential(client_id=client_id)
            service = BlobServiceClient(blob_uri, credential=credential)

        _container_client = service.get_container_client(_JOBS_CONTAINER)
        if not _container_client.exists():
            _container_client.create_container()
    return _container_client


# ---------------------------------------------------------------------------
# Job CRUD
# ---------------------------------------------------------------------------

def save_job(job_id: str, data: dict):
    """Save a job result to blob storage (overwrites if exists)."""
    get_container().upload_blob(
        f"{job_id}.json",
        json.dumps(data, ensure_ascii=False),
        overwrite=True,
    )


def load_job(job_id: str) -> dict | None:
    """Load a job result from blob storage. Returns None if not found."""
    try:
        blob = get_container().download_blob(f"{job_id}.json")
        return json.loads(blob.readall())
    except Exception:
        return None


def delete_job(job_id: str):
    """Delete a job blob. Silently ignores if not found."""
    try:
        get_container().delete_blob(f"{job_id}.json")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Company name translation
# ---------------------------------------------------------------------------

def translate_company_name(name: str) -> str:
    """Translate non-ASCII company name to English via GPT-4.1.

    Returns the original name if it's already ASCII or if translation fails.
    """
    if not name or name.isascii():
        return name
    try:
        from extractor.llm_reconciler import _get_client, _DEPLOYMENT
        client = _get_client()
        resp = client.chat.completions.create(
            model=_DEPLOYMENT(),
            messages=[
                {"role": "system", "content": "Translate the company name to English. Return ONLY the English name, nothing else."},
                {"role": "user", "content": name},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        translated = resp.choices[0].message.content.strip().strip('"')
        if translated:
            return translated
    except Exception as e:
        logger.warning(f"Company name translation failed: {e}")
    return name


# ---------------------------------------------------------------------------
# Response payload builder
# ---------------------------------------------------------------------------

# Statement types in canonical order
STATEMENT_TYPES = ["balance_sheet", "income_statement", "cash_flow"]

# Key mapping: snake_case <-> camelCase
SNAKE_TO_CAMEL = {
    "balance_sheet": "balanceSheet",
    "income_statement": "incomeStatement",
    "cash_flow": "cashFlow",
}
CAMEL_TO_SNAKE = {v: k for k, v in SNAKE_TO_CAMEL.items()}


def build_response_payload(result: dict) -> dict:
    """Build the API response payload from a pipeline result dict.

    Extracts company name (translates if non-English), stringifies each
    statement as JSON, and returns a flat dict with camelCase keys.
    """
    company_name = None
    for stype in STATEMENT_TYPES:
        stmt = result.get(stype)
        if stmt and isinstance(stmt, dict):
            company_name = stmt.get("document_metadata", {}).get("company_name")
            if company_name:
                break

    company_name = translate_company_name(company_name or "Unknown_Company")

    return {
        "companyName": company_name,
        "summary": json.dumps(result.get("summary", []), ensure_ascii=False),
        "balanceSheet": json.dumps(result.get("balance_sheet"), ensure_ascii=False),
        "incomeStatement": json.dumps(result.get("income_statement"), ensure_ascii=False),
        "cashFlow": json.dumps(result.get("cash_flow"), ensure_ascii=False),
        "confidence": json.dumps(result.get("confidence", {}), ensure_ascii=False),
    }


def parse_stmt_from_result(result: dict, stype_snake: str):
    """Load a statement dict from a result blob (handles both key conventions).

    The blob stores statements as JSON strings with camelCase keys. This
    function handles both snake_case and camelCase lookups, and parses
    the JSON string if needed.
    """
    camel_key = SNAKE_TO_CAMEL.get(stype_snake, stype_snake)
    stmt_str = result.get(stype_snake) or result.get(camel_key)
    if not stmt_str or stmt_str == "null":
        return None
    return json.loads(stmt_str) if isinstance(stmt_str, str) else stmt_str
