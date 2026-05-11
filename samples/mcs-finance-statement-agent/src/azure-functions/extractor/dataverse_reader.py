"""
Dataverse Web API reader. Fetches approved extraction data for Excel generation.
Reuses MSAL auth from dataverse_client.
"""
import logging
import os

import httpx

from extractor.dataverse_client import _get_token, _headers

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return os.environ["DATAVERSE_URL"].rstrip("/")


def read_job(job_id: str) -> dict | None:
    """Fetch ExtractionJob by cree1_jobid (the extraction UUID, not the Dataverse record ID)."""
    token = _get_token()
    url = f"{_base_url()}/api/data/v9.2/cree1_extractionjobs?$filter=cree1_jobid eq '{job_id}'"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers(token))
        resp.raise_for_status()
        rows = resp.json().get("value", [])
        return rows[0] if rows else None


def read_statements(job_id: str) -> list[dict]:
    """Fetch ExtractedStatement rows for a job, ordered by statement type."""
    token = _get_token()
    url = (
        f"{_base_url()}/api/data/v9.2/cree1_extractedstatement1s"
        f"?$filter=cree1_jobid eq '{job_id}'"
        f"&$orderby=cree1_statementtype asc"
    )
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers(token))
        resp.raise_for_status()
        return resp.json().get("value", [])


def read_line_items(job_id: str) -> list[dict]:
    """Fetch all ExtractedLineItem rows for a job, ordered by row then column.

    Handles OData pagination (5000 row limit per page).
    """
    token = _get_token()
    hdrs = _headers(token)
    hdrs["Prefer"] = "odata.maxpagesize=5000"
    url = (
        f"{_base_url()}/api/data/v9.2/cree1_extractedlineitems"
        f"?$filter=cree1_jobid eq '{job_id}'"
        f"&$orderby=cree1_rowindex asc,cree1_columnindex asc"
    )
    all_items = []
    with httpx.Client(timeout=60.0) as client:
        while url:
            resp = client.get(url, headers=hdrs)
            resp.raise_for_status()
            data = resp.json()
            all_items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")

    logger.info("Read %d line items for job %s", len(all_items), job_id)
    return all_items
