import json
import logging
import os
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

DATA_FILE = Path(__file__).parent / "src" / "repairsData.json"


def _is_api_key_valid(req: func.HttpRequest) -> bool:
    expected_key = os.environ.get("API_KEY", "").strip()
    if not expected_key:
        return False
    api_key = (req.headers.get("X-API-Key") or "").strip()
    return api_key == expected_key


@app.route(route="repairs", methods=["GET"])
def repairs(req: func.HttpRequest) -> func.HttpResponse:
    if not _is_api_key_valid(req):
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        repair_records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("Error reading repairs data")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve repair records"}),
            status_code=500,
            mimetype="application/json",
        )

    assigned_to = req.params.get("assignedTo")
    if assigned_to:
        query = assigned_to.strip().lower()
        repair_records = [
            r for r in repair_records
            if r["assignedTo"].lower() == query
            or query in r["assignedTo"].lower().split()
        ]

    return func.HttpResponse(
        json.dumps({"results": repair_records}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="repairs/{id}", methods=["PATCH"])
def update_repair(req: func.HttpRequest) -> func.HttpResponse:
    if not _is_api_key_valid(req):
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    repair_id = req.route_params.get("id")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json",
        )

    new_title = body.get("title")
    new_assignee = body.get("assignedTo")

    if new_title is not None and (not isinstance(new_title, str) or not new_title.strip()):
        return func.HttpResponse(
            json.dumps({"error": "Title must be a non-empty string"}),
            status_code=400,
            mimetype="application/json",
        )
    if new_assignee is not None and (not isinstance(new_assignee, str) or not new_assignee.strip()):
        return func.HttpResponse(
            json.dumps({"error": "AssignedTo must be a non-empty string"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        repair_records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        idx = next((i for i, r in enumerate(repair_records) if r["id"] == repair_id), -1)
        if idx < 0:
            return func.HttpResponse(
                json.dumps({"error": "Repair not found"}),
                status_code=404,
                mimetype="application/json",
            )

        if new_title is not None:
            repair_records[idx]["title"] = new_title
        if new_assignee is not None:
            repair_records[idx]["assignedTo"] = new_assignee

        DATA_FILE.write_text(json.dumps(repair_records, indent=2), encoding="utf-8")

        return func.HttpResponse(
            json.dumps({"updatedRepair": repair_records[idx]}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Error updating repair record")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update repair record"}),
            status_code=500,
            mimetype="application/json",
        )
