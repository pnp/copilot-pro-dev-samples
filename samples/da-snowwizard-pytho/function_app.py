import azure.functions as func
import json
import logging

from services.snow_incidents import IncidentsApiService
from services.snow_profiles import ProfilesApiService

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

incidents_service = IncidentsApiService()
profiles_service = ProfilesApiService()


@app.route(route="incidents/{id?}", methods=["GET", "POST"])
def incidents(req: func.HttpRequest) -> func.HttpResponse:
    """Handle HTTP requests for incidents (list, get by ID, create)."""
    try:
        # Need to implement authentication to get the address from context,
        # for now lets use Fred Luddy as the current user
        email = "fred.luddy@example.com"
        incident_id = req.route_params.get("id")

        if req.method == "GET":
            if incident_id:
                logging.info(f"➡️ GET /api/incidents/{incident_id}")
                result = incidents_service.get_incident(incident_id)
                logging.info(f"   ✅ GET /api/incidents/{incident_id}: {len(result)} incidents returned")
            else:
                logging.info("➡️ GET /api/incidents")
                result = incidents_service.get_incidents()
                logging.info(f"   ✅ GET /api/incidents: {len(result)} incidents returned")

            return func.HttpResponse(
                json.dumps({"results": result}),
                status_code=200,
                mimetype="application/json",
            )

        elif req.method == "POST":
            try:
                body = req.get_json()
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "No body to process this request."}),
                    status_code=400,
                    mimetype="application/json",
                )

            logging.info("➡️ POST /api/incidents")
            result = incidents_service.create_incident(
                email, body.get("short_description", ""), body.get("description", "")
            )
            logging.info(f"   ✅ POST /api/incidents: incident created!")

            return func.HttpResponse(
                json.dumps({"results": result}),
                status_code=200,
                mimetype="application/json",
            )

    except Exception as e:
        logging.error(f"   ❌ /api/incidents: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="me/{command?}", methods=["GET"])
def me(req: func.HttpRequest) -> func.HttpResponse:
    """Handle HTTP requests for the current user's profile."""
    try:
        # Need to implement authentication to get the address from context,
        # for now lets use Fred Luddy as the current user
        email = "fred.luddy@example.com"

        logging.info("➡️ GET /api/me")
        result = profiles_service.get_profile(email)
        logging.info(f"   ✅ GET /api/me: {len(result)} profiles returned")

        return func.HttpResponse(
            json.dumps({"results": result}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"   ❌ GET /api/me: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="profiles/{email?}", methods=["GET"])
def profiles(req: func.HttpRequest) -> func.HttpResponse:
    """Handle HTTP requests for user profiles by email."""
    try:
        email = req.route_params.get("email", "").lower()

        logging.info("➡️ GET /api/profiles")
        result = profiles_service.get_profile(email)
        logging.info(f"   ✅ GET /api/profiles: {len(result)} profiles returned")

        return func.HttpResponse(
            json.dumps({"results": result}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"   ❌ GET /api/profiles: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
