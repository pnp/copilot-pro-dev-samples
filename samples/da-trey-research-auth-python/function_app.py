import json
import logging

import azure.functions as func

from src.services.consultant_api_service import consultant_api_service
from src.services.project_api_service import project_api_service
from src.services.utilities import HttpError, clean_up_parameter
from src.middleware.auth import with_auth, UserInfo

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# /api/consultants and /api/consultants/{id}

async def _consultants_handler(req: func.HttpRequest, user_info: UserInfo) -> func.HttpResponse:
    logging.info("HTTP trigger function consultants processed a request.")

    try:
        # Extract route param — Azure Functions Python v2 uses route_params
        consultant_id = req.route_params.get("id", "")

        if consultant_id:
            consultant_id = consultant_id.lower()
            print(f"➡️ GET /api/consultants/{consultant_id}: request for consultant {consultant_id}")
            result = await consultant_api_service.get_api_consultant_by_id(consultant_id)
            results = [result] if result else []
            print(f"   ✅ GET /api/consultants/{consultant_id}: response status 1 consultant returned")
            return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

        consultant_name = (req.params.get("consultantName") or "").lower()
        project_name = (req.params.get("projectName") or "").lower()
        skill = (req.params.get("skill") or "").lower()
        certification = (req.params.get("certification") or "").lower()
        role = (req.params.get("role") or "").lower()
        hours_available = (req.params.get("hoursAvailable") or "").lower()

        print(f"➡️ GET /api/consultants: request for consultantName={consultant_name}, projectName={project_name}, skill={skill}, certification={certification}, role={role}, hoursAvailable={hours_available}")

        consultant_name = clean_up_parameter("consultantName", consultant_name)
        project_name = clean_up_parameter("projectName", project_name)
        skill = clean_up_parameter("skill", skill)
        certification = clean_up_parameter("certification", certification)
        role = clean_up_parameter("role", role)
        hours_available = clean_up_parameter("hoursAvailable", hours_available)

        results = await consultant_api_service.get_api_consultants(
            consultant_name, project_name, skill, certification, role, hours_available
        )
        print(f"   ✅ GET /api/consultants: response status 200; {len(results)} consultants returned")
        return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

    except Exception as error:
        status = getattr(error, "status", 500)
        print(f"   ⛔ Returning error status code {status}: {error}")
        return func.HttpResponse(
            json.dumps({"results": {"status": status, "message": str(error)}}),
            mimetype="application/json",
            status_code=status,
        )


@app.route(route="consultants/{id:alpha?}", methods=["GET"])
async def consultants(req: func.HttpRequest) -> func.HttpResponse:
    handler = with_auth(_consultants_handler)
    return await handler(req)


# /api/projects and /api/projects/{id}

async def _projects_handler(req: func.HttpRequest, user_info: UserInfo) -> func.HttpResponse:
    logging.info("HTTP trigger function projects processed a request.")

    try:
        route_id = req.route_params.get("id", "")
        if route_id:
            route_id = route_id.lower()

        if req.method == "GET":
            project_name = (req.params.get("projectName") or "").lower()
            consultant_name = (req.params.get("consultantName") or "").lower()

            print(f"➡️ GET /api/projects: request for projectName={project_name}, consultantName={consultant_name}, id={route_id}")

            project_name = clean_up_parameter("projectName", project_name)
            consultant_name = clean_up_parameter("consultantName", consultant_name)

            if route_id and route_id not in ("assignconsultant",):
                result = await project_api_service.get_api_project_by_id(route_id)
                results = [result]
                print(f"   ✅ GET /api/projects: response status 200; 1 projects returned")
                return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

            # Use current user if the project name is user_profile
            if "user_profile" in project_name:
                current_user_name = user_info.name or "Unknown User"
                results = await project_api_service.get_api_projects("", current_user_name)
                print(f"   ✅ GET /api/projects for current user response status 200; {len(results)} projects returned")
                return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

            results = await project_api_service.get_api_projects(project_name, consultant_name)
            print(f"   ✅ GET /api/projects: response status 200; {len(results)} projects returned")
            return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

        elif req.method == "POST":
            if route_id == "assignconsultant":
                try:
                    body = json.loads(req.get_body().decode("utf-8"))
                except Exception:
                    raise HttpError(400, "No body to process this request.")

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

                print(f"➡️ POST /api/projects: assignconsultant request, projectName={project_name}, consultantName={consultant_name}, role={role}, forecast={forecast}")
                result = await project_api_service.add_consultant_to_project(project_name, consultant_name, role, forecast)

                response = {
                    "results": {
                        "status": 200,
                        "clientName": result["clientName"],
                        "projectName": result["projectName"],
                        "consultantName": result["consultantName"],
                        "remainingForecast": result["remainingForecast"],
                        "message": result["message"],
                    }
                }
                print(f"   ✅ POST /api/projects: response status 200 - {result['message']}")
                return func.HttpResponse(json.dumps(response), mimetype="application/json", status_code=200)
            else:
                raise HttpError(400, f"Invalid command: {route_id}")
        else:
            raise HttpError(405, f"Method not allowed: {req.method}")

    except Exception as error:
        status = getattr(error, "status", 500)
        print(f"   ⛔ Returning error status code {status}: {error}")
        return func.HttpResponse(
            json.dumps({"results": {"status": status, "message": str(error)}}),
            mimetype="application/json",
            status_code=status,
        )


@app.route(route="projects/{id?}", methods=["GET", "POST"])
async def projects(req: func.HttpRequest) -> func.HttpResponse:
    handler = with_auth(_projects_handler)
    return await handler(req)


# /api/me and /api/me/{command}

async def _me_handler(req: func.HttpRequest, user_info: UserInfo) -> func.HttpResponse:
    logging.info("HTTP trigger function me processed a request.")

    try:
        me = await consultant_api_service.get_api_consultant_by_email(user_info.email)
        command = (req.route_params.get("command") or "").lower()

        if req.method == "GET":
            if command:
                raise HttpError(400, f"Invalid command: {command}")

            print("➡️ GET /api/me request")
            results = [me] if me else []
            print(f"   ✅ GET /me response status 200; {len(results)} consultants returned")
            return func.HttpResponse(json.dumps({"results": results}), mimetype="application/json", status_code=200)

        elif req.method == "POST":
            if command == "chargetime":
                try:
                    body = json.loads(req.get_body().decode("utf-8"))
                except Exception:
                    raise HttpError(400, "No body to process this request.")

                project_name = clean_up_parameter("projectName", body.get("projectName", ""))
                if not project_name:
                    raise HttpError(400, "Missing project name")

                hours = body.get("hours")
                if hours is None:
                    raise HttpError(400, "Missing hours")
                if not isinstance(hours, (int, float)) or hours < 0 or hours > 24:
                    raise HttpError(400, f"Invalid hours: {hours}")

                print(f"➡️ POST /api/me/chargetime request for project {project_name}, hours {hours}")
                result = await consultant_api_service.charge_time_to_project(project_name, user_info.id, int(hours))

                response = {
                    "results": {
                        "status": 200,
                        "clientName": result["clientName"],
                        "projectName": result["projectName"],
                        "remainingForecast": result["remainingForecast"],
                        "message": result["message"],
                    }
                }
                print(f"   ✅ POST /api/me/chargetime response status 200; {result['message']}")
                return func.HttpResponse(json.dumps(response), mimetype="application/json", status_code=200)
            else:
                raise HttpError(400, f"Invalid command: {command}")
        else:
            raise HttpError(405, f"Method not allowed: {req.method}")

    except Exception as error:
        status = getattr(error, "status", 500)
        print(f"   ⛔ Returning error status code {status}: {error}")
        return func.HttpResponse(
            json.dumps({"results": {"status": status, "message": str(error)}}),
            mimetype="application/json",
            status_code=status,
        )


@app.route(route="me/{command?}", methods=["GET", "POST"])
async def me(req: func.HttpRequest) -> func.HttpResponse:
    handler = with_auth(_me_handler)
    return await handler(req)
