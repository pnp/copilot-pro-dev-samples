"""
extractor/pdfplumber_client.py
------------------------------
Local PDF extraction using pdfplumber. No cloud service needed.

Returns structured data: pages with tables and text lines.
"""
import logging
import pdfplumber

logger = logging.getLogger(__name__)


def extract_document(file_path: str) -> dict:
    """Extract tables and text from a PDF using pdfplumber.

    Returns:
        {
            "pages": [
                {
                    "page_number": 1,  # 1-based
                    "text": "full page text...",
                    "tables": [
                        [["header1", "header2"], ["row1col1", "row1col2"], ...]
                    ]
                },
                ...
            ]
        }
    """
    pdf = pdfplumber.open(file_path)
    pages = []

    for i, page in enumerate(pdf.pages):
        page_text = page.extract_text() or ""
        page_tables = page.extract_tables() or []

        pages.append({
            "page_number": i + 1,
            "text": page_text,
            "tables": page_tables,
        })

    pdf.close()

    logger.info(f"pdfplumber: {len(pages)} pages, {sum(len(p['tables']) for p in pages)} tables")
    return {"pages": pages}
