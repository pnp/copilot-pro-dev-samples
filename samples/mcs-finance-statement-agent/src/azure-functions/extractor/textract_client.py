"""
extractor/textract_client.py
----------------------------
AWS Textract client for document analysis.

Handles: S3 upload -> StartDocumentAnalysis -> poll -> return blocks -> S3 cleanup.

Configuration (via env vars or ~/.aws/credentials):
  AWS_REGION              -- AWS region (must match S3 bucket and Textract)
  AWS_S3_BUCKET           -- S3 bucket for temporary PDF upload
  AWS_S3_PREFIX           -- S3 key prefix (default: "textract-input")

  Authentication via either:
  - ~/.aws/credentials (local dev -- boto3 reads automatically)
  - AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars (production)
"""

import logging
import os
import time
import uuid

import boto3

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 3
_POLL_TIMEOUT = 300  # 5 minutes


def _get_s3_client():
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", region_name=region)


def _get_textract_client():
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("textract", region_name=region)


def analyze_document(file_path: str) -> dict:
    """
    Submit a PDF for Textract table analysis and return the full result.

    1. Uploads PDF to S3
    2. Starts async document analysis with TABLES feature
    3. Polls until complete
    4. Handles pagination for large documents
    5. Cleans up S3 object
    6. Returns the Textract response with all Blocks

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        Textract response dict containing Blocks array.
    """
    bucket = os.environ["AWS_S3_BUCKET"]
    prefix = os.environ.get("AWS_S3_PREFIX", "textract-input")
    s3_key = f"{prefix}/{uuid.uuid4().hex}.pdf"

    s3 = _get_s3_client()
    textract = _get_textract_client()

    # Step 1: Upload to S3
    logger.info(f"Uploading PDF to s3://{bucket}/{s3_key}")
    s3.upload_file(Filename=file_path, Bucket=bucket, Key=s3_key)

    try:
        # Step 2: Start analysis
        logger.info("Starting Textract document analysis")
        start_resp = textract.start_document_analysis(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": s3_key}},
            FeatureTypes=["TABLES"],
        )
        job_id = start_resp["JobId"]
        logger.info(f"Textract job started: {job_id}")

        # Step 3: Poll until complete
        result = _poll_job(textract, job_id)

        # Step 4: Handle pagination (large documents)
        all_blocks = list(result.get("Blocks", []))
        next_token = result.get("NextToken")
        while next_token:
            page_resp = textract.get_document_analysis(
                JobId=job_id, NextToken=next_token
            )
            all_blocks.extend(page_resp.get("Blocks", []))
            next_token = page_resp.get("NextToken")

        result["Blocks"] = all_blocks
        return result

    finally:
        # Step 5: Always clean up S3
        logger.info(f"Cleaning up s3://{bucket}/{s3_key}")
        try:
            s3.delete_object(Bucket=bucket, Key=s3_key)
        except Exception as e:
            logger.warning(f"S3 cleanup failed (non-fatal): {e}")


def _poll_job(textract, job_id: str) -> dict:
    """Poll Textract job until SUCCEEDED or FAILED."""
    start = time.time()
    attempt = 0

    while (time.time() - start) < _POLL_TIMEOUT:
        attempt += 1
        resp = textract.get_document_analysis(JobId=job_id)
        status = resp["JobStatus"]
        logger.info(f"  [{attempt}] Textract status: {status}")

        if status == "SUCCEEDED":
            return resp
        if status == "FAILED":
            msg = resp.get("StatusMessage", "Unknown error")
            raise RuntimeError(f"Textract job failed: {msg}")

        time.sleep(_POLL_INTERVAL)

    raise TimeoutError(f"Textract job did not complete within {_POLL_TIMEOUT}s")
