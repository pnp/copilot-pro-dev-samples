"""
extractor/cu_client.py
----------------------
Azure Content Understanding client for custom analyzers.

Adapted from the Azure Samples reference implementation:
  https://github.com/Azure-Samples/azure-ai-content-understanding-python

Supports:
  - Creating/updating custom analyzers (PUT)
  - Submitting documents for analysis (POST binary)
  - Polling for results (GET with retry)
  - Deleting analyzers (DELETE)
  - Listing existing analyzers (GET)

Configuration (via .env):
  AZURE_CU_ENDPOINT  — Base endpoint (without path), e.g.
                        https://azure-content--resource.cognitiveservices.azure.com

Authentication: Managed Identity (DefaultAzureCredential).
  Requires Cognitive Services User role on the resource.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(override=False)

_API_VERSION = "2025-05-01-preview"
_POLL_INTERVAL = 3
_POLL_TIMEOUT = 300  # 5 minutes max


def _get_auth_headers() -> dict:
    """Return auth headers using managed identity (corp policy: no API keys)."""
    from azure.identity import DefaultAzureCredential
    token = DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
    return {"Authorization": f"Bearer {token.token}"}


def _get_base_url() -> str:
    """Return the CU endpoint base URL (no trailing slash)."""
    endpoint = os.environ.get("AZURE_CU_ENDPOINT", "")
    # The old .env has a full analyze URL; extract just the base.
    if "/contentunderstanding/" in endpoint:
        endpoint = endpoint.split("/contentunderstanding/")[0]
    return endpoint.rstrip("/")


def _get_headers(content_type: str = "application/json") -> dict:
    return {**_get_auth_headers(), "Content-Type": content_type}


# ---------------------------------------------------------------------------
# Analyzer management
# ---------------------------------------------------------------------------

def create_analyzer(analyzer_id: str, template: dict) -> dict:
    """
    Create or update a custom analyzer.

    Args:
        analyzer_id: Unique identifier (e.g. "financial-statement-locator")
        template: Analyzer definition JSON (baseAnalyzerId, fieldSchema, etc.)

    Returns the full response dict. Raises on failure.
    """
    url = (
        f"{_get_base_url()}/contentunderstanding/analyzers/{analyzer_id}"
        f"?api-version={_API_VERSION}"
    )
    resp = requests.put(url, headers=_get_headers(), json=template, timeout=60)
    resp.raise_for_status()

    # If 201 Created with operation-location, poll until ready.
    operation_location = resp.headers.get("operation-location")
    if operation_location:
        return _poll(operation_location)

    return resp.json() if resp.text.strip() else {"status": "created"}


def get_analyzer(analyzer_id: str) -> Optional[dict]:
    """Get analyzer details. Returns None if not found."""
    url = (
        f"{_get_base_url()}/contentunderstanding/analyzers/{analyzer_id}"
        f"?api-version={_API_VERSION}"
    )
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def list_analyzers() -> list[dict]:
    """List all analyzers on this resource."""
    url = f"{_get_base_url()}/contentunderstanding/analyzers?api-version={_API_VERSION}"
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json().get("value", [])


def delete_analyzer(analyzer_id: str) -> None:
    """Delete an analyzer."""
    url = (
        f"{_get_base_url()}/contentunderstanding/analyzers/{analyzer_id}"
        f"?api-version={_API_VERSION}"
    )
    resp = requests.delete(url, headers=_get_headers(), timeout=30)
    if resp.status_code != 404:
        resp.raise_for_status()


# ---------------------------------------------------------------------------
# Document analysis
# ---------------------------------------------------------------------------

def analyze_document(
    analyzer_id: str,
    file_path: str,
    page_range: str | None = None,
) -> dict:
    """
    Submit a document for analysis and return the full result.

    Args:
        analyzer_id: The custom analyzer to use.
        file_path: Path to the PDF file.
        page_range: Optional page range filter (e.g. "4-5", "6", "7-9").
                    Uses 1-based page numbers.

    Returns the complete analysis result dict with extracted fields.
    """
    range_param = f"&range={page_range}" if page_range else ""
    url = (
        f"{_get_base_url()}/contentunderstanding/analyzers/{analyzer_id}:analyze"
        f"?api-version={_API_VERSION}{range_param}"
    )

    with open(file_path, "rb") as f:
        data = f.read()

    # Determine content type from extension.
    ext = Path(file_path).suffix.lower()
    content_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
    }
    ct = content_types.get(ext, "application/octet-stream")

    headers = _get_headers(content_type=ct)
    resp = requests.post(url, headers=headers, data=data, timeout=120)
    resp.raise_for_status()

    operation_location = resp.headers.get("operation-location")
    if operation_location:
        return _poll(operation_location)

    return resp.json()


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------

def _poll(operation_location: str) -> dict:
    """Poll an async operation until it completes."""
    headers = _get_auth_headers()
    start = time.time()
    attempt = 0

    while (time.time() - start) < _POLL_TIMEOUT:
        attempt += 1
        resp = requests.get(operation_location, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        status = result.get("status", "unknown").lower()
        print(f"      [{attempt}] status: {status}")

        if status == "succeeded":
            return result
        if status == "failed":
            error = result.get("error", {})
            raise RuntimeError(
                f"Operation failed: {error.get('code')} - {error.get('message')}"
            )

        time.sleep(_POLL_INTERVAL)

    raise TimeoutError(f"Operation did not complete within {_POLL_TIMEOUT}s")
