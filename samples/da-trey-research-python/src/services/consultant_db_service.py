from ..model.base_model import Consultant, Location
from .db_service import DbService

TABLE_NAME = "Consultant"


class ConsultantDbService:
    """Database service for Consultant entities."""

    def __init__(self):
        # Consultants are READ ONLY in this demo, so cache them
        self._db_service = DbService(ok_to_cache_locally=True)

    def get_consultant_by_id(self, consultant_id: str) -> Consultant:
        entity = self._db_service.get_entity_by_row_key(TABLE_NAME, consultant_id)
        return self._convert_db_consultant(entity)

    def get_consultants(self) -> list:
        entities = self._db_service.get_entities(TABLE_NAME)
        return [self._convert_db_consultant(e) for e in entities]

    def create_consultant(self, consultant: Consultant) -> None:
        entity = {
            "PartitionKey": TABLE_NAME,
            "RowKey": consultant.id,
            "id": consultant.id,
            "name": consultant.name,
            "email": consultant.email,
            "phone": consultant.phone,
            "consultantPhotoUrl": consultant.consultantPhotoUrl,
            "location": {
                "street": consultant.location.street,
                "city": consultant.location.city,
                "state": consultant.location.state,
                "country": consultant.location.country,
                "postalCode": consultant.location.postalCode,
                "latitude": consultant.location.latitude,
                "longitude": consultant.location.longitude,
            } if consultant.location else {},
            "skills": consultant.skills,
            "certifications": consultant.certifications,
            "roles": consultant.roles,
        }
        self._db_service.create_entity(TABLE_NAME, consultant.id, entity)
        print(f"Added new consultant {consultant.name} ({consultant.id}) to the Consultant table")

    def _convert_db_consultant(self, db_consultant: dict) -> Consultant:
        location_data = db_consultant.get("location", {})
        if isinstance(location_data, dict):
            location = Location(**location_data)
        else:
            location = Location()

        return Consultant(
            id=db_consultant.get("id", ""),
            name=db_consultant.get("name", ""),
            email=db_consultant.get("email", ""),
            phone=db_consultant.get("phone", ""),
            consultantPhotoUrl=db_consultant.get("consultantPhotoUrl", ""),
            location=location,
            skills=db_consultant.get("skills", []),
            certifications=db_consultant.get("certifications", []),
            roles=db_consultant.get("roles", []),
        )


# Singleton instance
consultant_db_service = ConsultantDbService()
