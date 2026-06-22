from ..model.base_model import Consultant, Location
from ..model.api_model import ApiConsultant
from .consultant_api_service import consultant_api_service
from .utilities import HttpError


class IdentityService:
    """Demo-only identity service for validating requests."""

    def validate_request(self, req) -> ApiConsultant:
        """Validate the request and return the current user's consultant profile."""
        # Default user used for unauthenticated testing
        user_id = "1"
        user_name = "Avery Howard"
        user_email = "avery@treyresearch.com"

        # Get the consultant record for this user; create one if necessary
        consultant = None
        try:
            consultant = consultant_api_service.get_api_consultant_by_id(user_id)
        except Exception as ex:
            if hasattr(ex, "status") and ex.status != 404:
                raise
            consultant = None

        if not consultant:
            consultant = self._create_consultant_for_user(user_id, user_name, user_email)

        return consultant

    def _create_consultant_for_user(self, user_id: str, user_name: str, user_email: str) -> ApiConsultant:
        """Create a new consultant record for this user with default values."""
        consultant = Consultant(
            id=user_id,
            name=user_name,
            email=user_email,
            phone="1-555-123-4567",
            consultantPhotoUrl="https://microsoft.github.io/copilot-camp/demo-assets/images/consultants/Unknown.jpg",
            location=Location(
                street="One Memorial Drive",
                city="Cambridge",
                state="MA",
                country="USA",
                postalCode="02142",
                latitude=42.361366,
                longitude=-71.081257,
            ),
            skills=["Python", "JavaScript"],
            certifications=["Azure Development"],
            roles=["Architect", "Project Lead"],
        )
        return consultant_api_service.create_api_consultant(consultant)


# Singleton instance
identity_service = IdentityService()
