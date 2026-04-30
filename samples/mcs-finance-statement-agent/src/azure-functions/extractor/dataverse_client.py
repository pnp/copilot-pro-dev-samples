"""
Dataverse Web API client. MSAL service principal auth + single row + batch writes.
"""
import json
import logging
import os
import uuid

import httpx
import msal

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def _get_token() -> str:
    authority = f"https://login.microsoftonline.com/{os.environ['DATAVERSE_TENANT_ID']}"
    app = msal.ConfidentialClientApplication(
        client_id=os.environ["DATAVERSE_CLIENT_ID"],
        client_credential=os.environ["DATAVERSE_CLIENT_SECRET"],
        authority=authority,
    )
    result = app.acquire_token_for_client(scopes=[f"{os.environ['DATAVERSE_URL']}/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"MSAL token error: {result.get('error_description', result)}")
    return result["access_token"]


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }


def build_create_request(table: str, data: dict, content_id: str, lookups: dict | None = None) -> dict:
    body = {**data}
    if lookups:
        body.update(lookups)
    return {"method": "POST", "url": table, "body": body, "content_id": content_id}


def build_batch_payload(requests: list[dict]) -> tuple[str, str]:
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    changeset_id = f"changeset_{uuid.uuid4().hex[:12]}"
    parts = [f"--{batch_id}", f"Content-Type: multipart/mixed; boundary={changeset_id}", ""]
    for req in requests:
        parts.extend([
            f"--{changeset_id}",
            "Content-Type: application/http",
            "Content-Transfer-Encoding: binary",
            f"Content-ID: {req['content_id']}",
            "",
            f"{req['method']} {req['url']} HTTP/1.1",
            "Content-Type: application/json",
            "",
            json.dumps(req["body"]),
        ])
    parts.append(f"--{changeset_id}--")
    parts.append(f"--{batch_id}--")
    return batch_id, "\r\n".join(parts)


def write_to_dataverse(job_id: str, job_row: dict, statement_rows: list[tuple[str, dict]], line_items: list[tuple[str, dict]]):
    """
    Write extraction results to Dataverse. Synchronous (called from background thread).

    Args:
        job_id: extraction job ID
        job_row: ExtractionJob dict
        statement_rows: list of (statement_type, row_dict) tuples
        line_items: list of (statement_type, row_dict) tuples
    """
    base_url = os.environ["DATAVERSE_URL"].rstrip("/")
    token = _get_token()
    hdrs = _headers(token)

    with httpx.Client(timeout=60.0) as client:
        # 1. Create ExtractionJob (need ID back)
        resp = client.post(f"{base_url}/api/data/v9.2/cree1_extractionjobs", json=job_row, headers=hdrs)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"ExtractionJob create failed: {resp.status_code} {resp.text[:1000]}")
        job_record_id = resp.json().get("cree1_extractionjobid", "")
        logger.info("Created ExtractionJob %s -> %s", job_id, job_record_id)

        # 2. Create ExtractedStatement rows (need IDs for line item lookups)
        stmt_ids = {}
        for stmt_type, stmt_data in statement_rows:
            stmt_data["cree1_ExtractionJobID@odata.bind"] = f"/cree1_extractionjobs({job_record_id})"
            resp = client.post(f"{base_url}/api/data/v9.2/cree1_extractedstatement1s", json=stmt_data, headers=hdrs)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"ExtractedStatement ({stmt_type}) create failed: {resp.status_code} {resp.text[:1000]}")
            stmt_ids[stmt_type] = resp.json().get("cree1_extractedstatement1id", "")
            logger.info("Created ExtractedStatement %s -> %s", stmt_type, stmt_ids[stmt_type])

        # 3. Batch-write ExtractedLineItems
        batch_hdrs = {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
        }
        content_id = 1
        batch_reqs = []
        total_written = 0

        for stmt_type, item_data in line_items:
            lookups = {"cree1_ExtractionJob@odata.bind": f"/cree1_extractionjobs({job_record_id})"}
            if stmt_type in stmt_ids:
                lookups["cree1_ExtractedStatement@odata.bind"] = f"/cree1_extractedstatement1s({stmt_ids[stmt_type]})"
            batch_reqs.append(build_create_request("cree1_extractedlineitems", item_data, str(content_id), lookups))
            content_id += 1

            if len(batch_reqs) >= BATCH_SIZE:
                boundary, body = build_batch_payload(batch_reqs)
                batch_hdrs["Content-Type"] = f"multipart/mixed; boundary={boundary}"
                resp = client.post(f"{base_url}/api/data/v9.2/$batch", content=body, headers=batch_hdrs)
                if resp.status_code not in (200, 204):
                    raise RuntimeError(f"Batch write failed: {resp.status_code} {resp.text[:1000]}")
                total_written += len(batch_reqs)
                logger.info("Written %d/%d line items", total_written, len(line_items))
                batch_reqs = []

        if batch_reqs:
            boundary, body = build_batch_payload(batch_reqs)
            batch_hdrs["Content-Type"] = f"multipart/mixed; boundary={boundary}"
            resp = client.post(f"{base_url}/api/data/v9.2/$batch", content=body, headers=batch_hdrs)
            if resp.status_code not in (200, 204):
                raise RuntimeError(f"Batch write failed: {resp.status_code} {resp.text[:1000]}")
            total_written += len(batch_reqs)

        logger.info("Dataverse write complete: %d statements, %d line items", len(statement_rows), total_written)
