"""This code sample provides a starter kit to implement server side logic for your
Declarative Agent API plugin in Python. Refer to
https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python
for complete Azure Functions developer guide.
"""

import json
import logging
import os

import azure.functions as func
import jwt

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Load repair records from JSON file
_repairs_data_path = os.path.join(os.path.dirname(__file__), "repairsData.json")
with open(_repairs_data_path, "r", encoding="utf-8") as f:
    repair_records = json.load(f)

# Entra ID configuration for token validation
_tenant_id = os.environ.get("AAD_APP_TENANT_ID", "")
_client_id = os.environ.get("AAD_APP_CLIENT_ID", "")
_jwks_url = f"https://login.microsoftonline.com/{_tenant_id}/discovery/v2.0/keys"
_issuer = f"https://login.microsoftonline.com/{_tenant_id}/v2.0"
_jwks_client = jwt.PyJWKClient(_jwks_url) if _tenant_id else None


def check_auth(req: func.HttpRequest, required_scopes: str | list[str]) -> int:
    """Validate the request token and scopes.

    Returns 0 if authorized, 401 if the token is missing/invalid, or 403 if
    the token is valid but lacks the required scopes.
    """
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]

    auth_header = req.headers.get("Authorization")
    if not auth_header:
        return 401

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return 401

    if not _jwks_client or not _client_id:
        logging.error("AAD_APP_TENANT_ID or AAD_APP_CLIENT_ID not configured")
        return 401

    try:
        token = parts[1]
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=f"api://{_client_id}",
            issuer=_issuer,
        )
    except Exception:
        logging.exception("Token validation failed")
        return 401

    token_scopes = decoded_token.get("scp", "").split(" ")
    if not all(scope in token_scopes for scope in required_scopes):
        return 403

    return 0


@app.route(route="repairs", methods=["GET"])
def repairs(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger function that returns repair information."""
    logging.info("HTTP trigger function processed a request.")

    auth_status = check_auth(req, "repairs_read")
    if auth_status == 401:
        return func.HttpResponse("Unauthorized", status_code=401)
    if auth_status == 403:
        return func.HttpResponse("Insufficient permissions", status_code=403)

    # Get the assignedTo query parameter
    assigned_to = req.params.get("assignedTo")

    # If no filter provided, return all records
    if not assigned_to:
        return func.HttpResponse(
            json.dumps({"results": repair_records}),
            mimetype="application/json",
            status_code=200,
        )

    # Filter repair records by assignedTo
    query = assigned_to.strip().lower()
    filtered_repairs = [
        item
        for item in repair_records
        if _matches_name(item["assignedTo"].lower(), query)
    ]

    return func.HttpResponse(
        json.dumps({"results": filtered_repairs}),
        mimetype="application/json",
        status_code=200,
    )


def _matches_name(full_name: str, query: str) -> bool:
    """Check if a full name matches the query (full name, first name, or last name)."""
    parts = full_name.split(" ")
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""
    return full_name == query or first_name == query or last_name == query
