import json
import logging
import os
from pathlib import Path

import azure.functions as func
import jwt
from jwt import PyJWKClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

DATA_FILE = Path(__file__).parent / "src" / "repairsData.json"

# Load repair records
try:
    repair_records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    logging.exception("Failed to load repairs data")
    raise

# Cache the JWKS client for token validation
_jwks_client = None


def _get_jwks_client(tenant_id: str) -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        _jwks_client = PyJWKClient(jwks_uri)
        logging.info("JWKS client created")
    return _jwks_client


@app.route(route="repairs", methods=["GET"])
def repairs(req: func.HttpRequest) -> func.HttpResponse:
    """Handle HTTP request and return repair information with OAuth token validation."""
    logging.info("HTTP trigger function processed a request.")

    # Token validation
    aad_app_client_id = os.environ.get("AAD_APP_CLIENT_ID", "")
    aad_app_tenant_id = os.environ.get("AAD_APP_TENANT_ID", "")
    aad_app_oauth_authority = os.environ.get("AAD_APP_OAUTH_AUTHORITY", "")

    try:
        auth_header = req.headers.get("Authorization", "")
        parts = auth_header.split(None, 1)
        token = parts[1].strip() if len(parts) == 2 and parts[0] == "Bearer" else None

        if not token:
            logging.error("No token found in request")
            return func.HttpResponse(status_code=401)

        jwks_client = _get_jwks_client(aad_app_tenant_id)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=aad_app_client_id,
            issuer=f"{aad_app_oauth_authority}/v2.0",
        )

        # Verify required scope
        scp = decoded.get("scp", "")
        if "repairs_read" not in scp.split(" "):
            logging.error("Token missing required scope 'repairs_read'")
            return func.HttpResponse(status_code=401)

        user_id = decoded.get("oid", "")
        user_name = decoded.get("name", "")
        logging.info(f"Token is valid for user {user_name} ({user_id})")

    except Exception as ex:
        logging.error(f"Token validation failed: {ex}")
        return func.HttpResponse(status_code=401)

    # Get the assignedTo query parameter
    assigned_to = req.params.get("assignedTo")

    results = repair_records

    if assigned_to:
        query = assigned_to.strip().lower()
        results = [
            item for item in repair_records
            if (
                item["assignedTo"].lower() == query
                or item["assignedTo"].lower().split(" ")[0] == query
                or (len(item["assignedTo"].split(" ")) > 1 and item["assignedTo"].lower().split(" ")[1] == query)
            )
        ]

    return func.HttpResponse(
        json.dumps({"results": results}),
        mimetype="application/json",
        status_code=200,
    )