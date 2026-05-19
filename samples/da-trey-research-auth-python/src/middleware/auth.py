import logging
from typing import Callable, Any

import azure.functions as func
import jwt
from jwt import PyJWKClient

from ..config import config
from ..services.consultant_api_service import consultant_api_service


class UserInfo:
    def __init__(self, name: str = "", email: str = "", user_id: str = ""):
        self.id = user_id
        self.name = name
        self.email = email


# Cache the JWKS client
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_uri = f"https://login.microsoftonline.com/{config.entra_app_tenant_id}/discovery/v2.0/keys"
        _jwks_client = PyJWKClient(jwks_uri)
        logging.info("JWKS client created")
    return _jwks_client


def _get_token(req: func.HttpRequest) -> str | None:
    auth_header = req.headers.get("authorization", "")
    parts = auth_header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _validate_token(token: str) -> dict | None:
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        issuer = f"https://login.microsoftonline.com/{config.entra_app_tenant_id}/v2.0"
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.entra_app_client_id,
            issuer=issuer,
        )

        # Verify required scope
        scp = decoded.get("scp", "")
        if "access_as_user" not in scp.split(" "):
            logging.error("Token missing required scope 'access_as_user'")
            return None

        return decoded
    except Exception as ex:
        logging.error(f"Token validation failed: {ex}")
        return None


def _extract_user_info(token_payload: dict) -> UserInfo:
    return UserInfo(
        name=token_payload.get("name", ""),
        email=token_payload.get("preferred_username", ""),
    )


async def _ensure_consultant(user_info: UserInfo) -> dict | None:
    consultant = await consultant_api_service.get_api_consultant_by_email(user_info.email)
    if not consultant:
        consultant = await consultant_api_service.create_api_consultant({
            "name": user_info.name,
            "email": user_info.email,
            "phone": "1-555-456-7890",
            "consultantPhotoUrl": "https://bobgerman.github.io/fictitiousAiGenerated/Unknown.jpg",
            "location": {
                "street": "5 Wayside Rd.",
                "city": "Burlington",
                "state": "MA",
                "country": "USA",
                "postalCode": "01803",
                "latitude": 42.5048,
                "longitude": -71.1956,
            },
            "skills": ["C#", "JavaScript", "TypeScript", "React", "Node.js"],
            "certifications": ["MCSADA", "Azure Developer Associate", "MCAAF", "Azure AI Fundamentals"],
            "roles": ["Project lead", "Developer", "Architect", "DevOps"],
        })
    return consultant


def _error_response(status: int, error: str, message: str) -> func.HttpResponse:
    import json
    return func.HttpResponse(
        json.dumps({"error": error, "message": message}),
        status_code=status,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


def _success_response(body: str, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body,
        status_code=status,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


def with_auth(handler: Callable) -> Callable:
    """Decorator that validates the OAuth token and passes UserInfo to the handler."""

    async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        token = _get_token(req)
        if not token:
            logging.info("No token provided in request headers")
            return _error_response(401, "Unauthorized", "Authentication token is required")

        valid_token = _validate_token(token)
        if not valid_token:
            logging.info("Invalid or expired token")
            return _error_response(401, "Unauthorized", "Invalid or expired authentication token")

        user_info = _extract_user_info(valid_token)
        consultant = await _ensure_consultant(user_info)

        # Update userInfo with consultant ID for more efficient lookups
        if consultant:
            user_info.id = consultant.get("id", user_info.id)

        try:
            response = await handler(req, user_info)
            # Wrap response with CORS headers if it doesn't already have them
            if isinstance(response, func.HttpResponse):
                return _success_response(response.get_body().decode("utf-8"), response.status_code)
            return response
        except Exception as error:
            logging.error(f"Handler execution error: {error}")
            return _error_response(500, "Internal Server Error", "An error occurred while processing the request")

    return wrapper
