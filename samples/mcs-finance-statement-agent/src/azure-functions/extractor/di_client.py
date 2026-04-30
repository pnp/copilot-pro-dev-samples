"""
extractor/di_client.py
-----------------------
Azure Document Intelligence client using the prebuilt-layout model.

Returns markdown with embedded HTML tables — the same format that
Content Understanding produces — so all downstream pipeline stages
(locator, transformer, validator, enricher) work unchanged.

Configuration (via .env):
  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT — Resource endpoint, e.g.
      https://your-docai-resource.cognitiveservices.azure.com/

Authentication: Managed Identity (DefaultAzureCredential).
  Requires Cognitive Services User role on the resource.
  API keys are disabled on this subscription.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger(__name__)


def _get_client():
    """Create a DocumentIntelligenceClient with Managed Identity auth."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"].rstrip("/")
    credential = DefaultAzureCredential()
    return DocumentIntelligenceClient(endpoint=endpoint, credential=credential)


def analyze_document(file_path: str) -> dict:
    """
    Submit a PDF to Document Intelligence prebuilt-layout and return the result.

    Uses output_content_format="markdown" so the response includes markdown
    text with embedded HTML <table> blocks — matching the CU output format.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The AnalyzeResult as a dict with keys:
            - content: str (markdown with HTML tables)
            - pages: list[dict] (page metadata)
            - tables: list[dict] (structured table data, for reference)
    """
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    client = _get_client()

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    logger.info(
        "DI: Submitting %d bytes to prebuilt-layout (markdown mode)", len(pdf_bytes)
    )

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
        output_content_format="markdown",
    )

    result = poller.result()

    # Convert SDK object to dict for consistent handling
    result_dict = {
        "content": result.content,  # Markdown with HTML tables
        "pages": [],
        "tables": [],
    }

    if result.pages:
        for page in result.pages:
            result_dict["pages"].append({
                "pageNumber": page.page_number,
                "spans": [
                    {"offset": s.offset, "length": s.length}
                    for s in (page.spans or [])
                ],
            })

    if result.tables:
        for table in result.tables:
            result_dict["tables"].append({
                "rowCount": table.row_count,
                "columnCount": table.column_count,
                "cells": [
                    {
                        "rowIndex": c.row_index,
                        "columnIndex": c.column_index,
                        "content": c.content,
                        "kind": c.kind or "content",
                        "columnSpan": c.column_span or 1,
                        "rowSpan": c.row_span or 1,
                    }
                    for c in (table.cells or [])
                ],
                "boundingRegions": [
                    {"pageNumber": r.page_number}
                    for r in (table.bounding_regions or [])
                ],
            })

    page_count = len(result_dict["pages"])
    table_count = len(result_dict["tables"])
    content_len = len(result_dict["content"])
    logger.info(
        "DI: Got %d pages, %d tables, %d chars markdown",
        page_count, table_count, content_len,
    )

    return result_dict
