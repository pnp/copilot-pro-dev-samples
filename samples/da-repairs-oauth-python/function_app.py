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


def has_required_scopes(req: func.HttpRequest, required_scopes: str | list[str]) -> bool:
    """Validate that the request has the required OAuth scopes."""
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]

    auth_header = req.headers.get("Authorization")
    if not auth_header:
        return False

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return False

    try:
        decoded_token = jwt.decode(parts[1], options={"verify_signature": False})
        token_scopes = decoded_token.get("scp", "").split(" ")
        return all(scope in token_scopes for scope in required_scopes)
    except Exception:
        return False


@app.route(route="repairs", methods=["GET"])
def repairs(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger function that returns repair information."""
    logging.info("HTTP trigger function processed a request.")

    if not has_required_scopes(req, "repairs_read"):
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
