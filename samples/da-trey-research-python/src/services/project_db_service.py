from ..model.base_model import Project, Location
from .db_service import DbService

TABLE_NAME = "Project"


class ProjectDbService:
    """Database service for Project entities."""

    def __init__(self):
        # Projects are READ ONLY in this demo, so cache them
        self._db_service = DbService(ok_to_cache_locally=True)

    def get_project_by_id(self, project_id: str) -> Project:
        entity = self._db_service.get_entity_by_row_key(TABLE_NAME, project_id)
        return self._convert_db_project(entity)

    def get_projects(self) -> list:
        entities = self._db_service.get_entities(TABLE_NAME)
        return [self._convert_db_project(e) for e in entities]

    def _convert_db_project(self, db_project: dict) -> Project:
        location_data = db_project.get("location", {})
        if isinstance(location_data, dict):
            location = Location(**location_data)
        else:
            location = Location()

        project = Project(
            id=db_project.get("id", ""),
            name=db_project.get("name", ""),
            description=db_project.get("description", ""),
            clientName=db_project.get("clientName", ""),
            clientContact=db_project.get("clientContact", ""),
            clientEmail=db_project.get("clientEmail", ""),
            location=location,
            mapUrl=self._get_map_url(db_project)
        )
        return project

    def _get_map_url(self, project: dict) -> str:
        client_name = project.get("clientName", "")
        company_name_kebab = client_name.lower().replace(" ", "-")
        return f"https://microsoft.github.io/copilot-camp/demo-assets/images/maps/{company_name_kebab}.jpg"


# Singleton instance
project_db_service = ProjectDbService()
