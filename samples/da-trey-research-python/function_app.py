import json
import logging
from dataclasses import asdict

import azure.functions as func

from src.services.consultant_api_service import consultant_api_service
from src.services.project_api_service import project_api_service
from src.services.identity_service import identity_service
from src.services.utilities import HttpError, clean_up_parameter

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _to_dict(obj):
    """Convert dataclass or dict to a JSON-serializable dict."""
    if hasattr(obj, "__dataclass_fields__"):
        d = asdict(obj)
        return d
    elif isinstance(obj, dict):
        return obj
    return obj


# ============================================================
# GET /api/consultants/{id?}
# ============================================================
@app.route(route="consultants/{id:alpha?}", methods=["GET"])
def consultants(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function consultants processed a request.")

    try:
        # Validate request
        identity_service.validate_request(req)

        # Get parameters
        consultant_name = (req.params.get("consultantName") or "").lower()
        project_name = (req.params.get("projectName") or "").lower()
        skill = (req.params.get("skill") or "").lower()
        certification = (req.params.get("certification") or "").lower()
        role = (req.params.get("role") or "").lower()
        hours_available = (req.params.get("hoursAvailable") or "").lower()

        consultant_id = req.route_params.get("id", "").lower()

        if consultant_id:
            logging.info(f"➡️ GET /api/consultants/{consultant_id}: request for consultant {consultant_id}")
            result = consultant_api_service.get_api_consultant_by_id(consultant_id)
            response_data = {"results": [_to_dict(result)]}
            logging.info(f"   ✅ GET /api/consultants/{consultant_id}: 1 consultant returned")
            return func.HttpResponse(
                json.dumps(response_data), mimetype="application/json", status_code=200
            )

        logging.info(
            f"➡️ GET /api/consultants: consultantName={consultant_name}, projectName={project_name}, "
            f"skill={skill}, certification={certification}, role={role}, hoursAvailable={hours_available}"
        )

        # Clean up parameters
        consultant_name = clean_up_parameter("consultantName", consultant_name)
        project_name = clean_up_parameter("projectName", project_name)
        skill = clean_up_parameter("skill", skill)
        certification = clean_up_parameter("certification", certification)
        role = clean_up_parameter("role", role)
        hours_available = clean_up_parameter("hoursAvailable", hours_available)

        result = consultant_api_service.get_api_consultants(
            consultant_name, project_name, skill, certification, role, hours_available
        )
        response_data = {"results": [_to_dict(r) for r in result]}
        logging.info(f"   ✅ GET /api/consultants: {len(result)} consultants returned")
        return func.HttpResponse(
            json.dumps(response_data), mimetype="application/json", status_code=200
        )

    except HttpError as e:
        logging.error(f"   ⛔ Returning error status code {e.status}: {e.message}")
        return func.HttpResponse(
            json.dumps({"results": {"status": e.status, "message": e.message}}),
            mimetype="application/json",
            status_code=e.status,
        )
    except Exception as e:
        logging.error(f"   ⛔ Returning error status code 500: {str(e)}")
        return func.HttpResponse(
            json.dumps({"results": {"status": 500, "message": str(e)}}),
            mimetype="application/json",
            status_code=500,
        )


# ============================================================
# GET /api/me
# ============================================================
@app.route(route="me", methods=["GET"])
def me_get(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function me (GET) processed a request.")

    try:
        current_user = identity_service.validate_request(req)

        logging.info("➡️ GET /api/me request")
        response_data = {"results": [_to_dict(current_user)]}
        logging.info(f"   ✅ GET /me: 1 consultant returned")
        return func.HttpResponse(
            json.dumps(response_data), mimetype="application/json", status_code=200
        )

    except HttpError as e:
        logging.error(f"   ⛔ Returning error status code {e.status}: {e.message}")
        return func.HttpResponse(
            json.dumps({"results": {"status": e.status, "message": e.message}}),
            mimetype="application/json",
            status_code=e.status,
        )
    except Exception as e:
        logging.error(f"   ⛔ Returning error status code 500: {str(e)}")
        return func.HttpResponse(
            json.dumps({"results": {"status": 500, "message": str(e)}}),
            mimetype="application/json",
            status_code=500,
        )


# ============================================================
# POST /api/me/chargeTime
# ============================================================
@app.route(route="me/chargeTime", methods=["POST"])
def me_charge_time(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function me/chargeTime processed a request.")

    try:
        current_user = identity_service.validate_request(req)

        try:
            body = req.get_json()
        except ValueError:
            raise HttpError(400, "No body to process this request.")

        if not body:
            raise HttpError(400, "Missing request body")

        project_name = clean_up_parameter("projectName", body.get("projectName", ""))
        if not project_name:
            raise HttpError(400, "Missing project name")

        hours = body.get("hours")
        if hours is None:
            raise HttpError(400, "Missing hours")
        if not isinstance(hours, (int, float)) or hours < 0 or hours > 24:
            raise HttpError(400, f"Invalid hours: {hours}")

        logging.info(f"➡️ POST /api/me/chargeTime: project={project_name}, hours={hours}")
        result = consultant_api_service.charge_time_to_project(project_name, current_user.id, hours)

        response_data = {
            "results": {
                "status": 200,
                "clientName": result.clientName,
                "projectName": result.projectName,
                "remainingForecast": result.remainingForecast,
                "message": result.message,
            }
        }
        logging.info(f"   ✅ POST /api/me/chargeTime: {result.message}")
        return func.HttpResponse(
            json.dumps(response_data), mimetype="application/json", status_code=200
        )

    except HttpError as e:
        logging.error(f"   ⛔ Returning error status code {e.status}: {e.message}")
        return func.HttpResponse(
            json.dumps({"results": {"status": e.status, "message": e.message}}),
            mimetype="application/json",
            status_code=e.status,
        )
    except Exception as e:
        logging.error(f"   ⛔ Returning error status code 500: {str(e)}")
        return func.HttpResponse(
            json.dumps({"results": {"status": 500, "message": str(e)}}),
            mimetype="application/json",
            status_code=500,
        )


# ============================================================
# GET /api/projects/{id?}
# ============================================================
@app.route(route="projects/{id:alpha?}", methods=["GET"])
def projects_get(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function projects (GET) processed a request.")

    try:
        user_info = identity_service.validate_request(req)

        project_id = req.route_params.get("id", "").lower()
        project_name = (req.params.get("projectName") or "").lower()
        consultant_name = (req.params.get("consultantName") or "").lower()

        logging.info(
            f"➡️ GET /api/projects: projectName={project_name}, consultantName={consultant_name}, id={project_id}"
        )

        project_name = clean_up_parameter("projectName", project_name)
        consultant_name = clean_up_parameter("consultantName", consultant_name)

        if project_id:
            result = project_api_service.get_api_project_by_id(project_id)
            response_data = {"results": [_to_dict(result)]}
            logging.info("   ✅ GET /api/projects: 1 project returned")
            return func.HttpResponse(
                json.dumps(response_data), mimetype="application/json", status_code=200
            )

        # Use current user if the project name is user_profile
        if "user_profile" in project_name:
            result = project_api_service.get_api_projects("", user_info.name)
            response_data = {"results": [_to_dict(r) for r in result]}
            logging.info(f"   ✅ GET /api/projects for current user: {len(result)} projects returned")
            return func.HttpResponse(
                json.dumps(response_data), mimetype="application/json", status_code=200
            )

        result = project_api_service.get_api_projects(project_name, consultant_name)
        response_data = {"results": [_to_dict(r) for r in result]}
        logging.info(f"   ✅ GET /api/projects: {len(result)} projects returned")
        return func.HttpResponse(
            json.dumps(response_data), mimetype="application/json", status_code=200
        )

    except HttpError as e:
        logging.error(f"   ⛔ Returning error status code {e.status}: {e.message}")
        return func.HttpResponse(
            json.dumps({"results": {"status": e.status, "message": e.message}}),
            mimetype="application/json",
            status_code=e.status,
        )
    except Exception as e:
        logging.error(f"   ⛔ Returning error status code 500: {str(e)}")
        return func.HttpResponse(
            json.dumps({"results": {"status": 500, "message": str(e)}}),
            mimetype="application/json",
            status_code=500,
        )


# ============================================================
# POST /api/projects/assignConsultant
# ============================================================
@app.route(route="projects/assignConsultant", methods=["POST"])
def projects_assign_consultant(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function projects/assignConsultant processed a request.")

    try:
        identity_service.validate_request(req)

        try:
            body = req.get_json()
        except ValueError:
            raise HttpError(400, "No body to process this request.")

        if not body:
            raise HttpError(400, "Missing request body")

        project_name = clean_up_parameter("projectName", body.get("projectName", ""))
        if not project_name:
            raise HttpError(400, "Missing project name")

        consultant_name = clean_up_parameter("consultantName", body.get("consultantName", ""))
        if not consultant_name:
            raise HttpError(400, "Missing consultant name")

        role = clean_up_parameter("Role", body.get("role", ""))
        if not role:
            raise HttpError(400, "Missing role")

        forecast = body.get("forecast", 0)

        logging.info(
            f"➡️ POST /api/projects/assignConsultant: projectName={project_name}, "
            f"consultantName={consultant_name}, role={role}, forecast={forecast}"
        )

        result = project_api_service.add_consultant_to_project(
            project_name, consultant_name, role, forecast
        )

        response_data = {
            "results": {
                "status": 200,
                "clientName": result.clientName,
                "projectName": result.projectName,
                "consultantName": result.consultantName,
                "remainingForecast": result.remainingForecast,
                "message": result.message,
            }
        }
        logging.info(f"   ✅ POST /api/projects/assignConsultant: {result.message}")
        return func.HttpResponse(
            json.dumps(response_data), mimetype="application/json", status_code=200
        )

    except HttpError as e:
        logging.error(f"   ⛔ Returning error status code {e.status}: {e.message}")
        return func.HttpResponse(
            json.dumps({"results": {"status": e.status, "message": e.message}}),
            mimetype="application/json",
            status_code=e.status,
        )
    except Exception as e:
        logging.error(f"   ⛔ Returning error status code 500: {str(e)}")
        return func.HttpResponse(
            json.dumps({"results": {"status": 500, "message": str(e)}}),
            mimetype="application/json",
            status_code=500,
        )
