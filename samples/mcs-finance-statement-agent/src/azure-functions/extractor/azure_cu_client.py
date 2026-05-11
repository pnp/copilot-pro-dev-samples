"""
extractor/azure_cu_client.py
----------------------------
Thin wrapper around the Azure Content Understanding (prebuilt-read) REST API.

Responsibilities:
  - POST a PDF file to the Azure CU endpoint
  - Handle both async (202 + Operation-Location) and sync (200 + body) modes
  - Poll the operation URL until analysis status is 'succeeded'

Configuration (via .env):
  AZURE_CU_ENDPOINT  — Full analyze URL including api-version query param

Authentication: Managed Identity (DefaultAzureCredential).
  Requires Cognitive Services User role on the resource.
"""

import os
import time

import requests
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(override=False)

ENDPOINT: str = os.environ["AZURE_CU_ENDPOINT"]

# Always use managed identity — no API keys
_credential = DefaultAzureCredential()


def _get_auth_headers() -> dict:
    """Return auth headers using managed identity token."""
    token = _credential.get_token("https://cognitiveservices.azure.com/.default")
    return {"Authorization": f"Bearer {token.token}"}

_POLL_INTERVAL_SECONDS = 3
_MAX_POLL_ATTEMPTS = 60


def submit_document(file_path: str) -> tuple[str | None, dict | None]:
    """
    POST the PDF to Azure Content Understanding.

    Returns a (operation_location, result) tuple:
      - Async mode:  (url_string, None) — caller must poll the URL.
      - Sync mode:   (None, result_dict) — result is already available.
    """
    with open(file_path, "rb") as f:
        data = f.read()

    headers = {**_get_auth_headers(), "Content-Type": "application/pdf"}

    response = requests.post(ENDPOINT, headers=headers, data=data, timeout=60)

    response.raise_for_status()

    operation_location = response.headers.get("operation-location")
    if operation_location:
        # Async mode — caller must poll
        return operation_location, None

    if not response.text.strip():
        raise ValueError(
            f"Azure returned HTTP {response.status_code} with an empty body "
            "and no operation-location header. Check your AZURE_CU_ENDPOINT "
            "and that the managed identity has Cognitive Services User role."
        )

    # Synchronous mode — result is in the response body directly
    return None, response.json()


def poll_result(operation_location: str) -> dict:
    """
    Poll the operation URL until status is 'succeeded'.
    Returns the full result dict.
    Raises RuntimeError on failure, TimeoutError if max attempts exceeded.
    """
    headers = _get_auth_headers()

    for attempt in range(1, _MAX_POLL_ATTEMPTS + 1):
        response = requests.get(operation_location, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        status = result.get("status", "unknown")
        print(f"      [{attempt}/{_MAX_POLL_ATTEMPTS}] status: {status}")

        if status.lower() == "succeeded":
            return result

        if status.lower() == "failed":
            error = result.get("error", {})
            raise RuntimeError(
                f"Azure Content Understanding analysis failed. "
                f"Code: {error.get('code')} | Message: {error.get('message')}"
            )

        time.sleep(_POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"Analysis did not complete after {_MAX_POLL_ATTEMPTS} polling attempts "
        f"({_MAX_POLL_ATTEMPTS * _POLL_INTERVAL_SECONDS}s)."
    )
