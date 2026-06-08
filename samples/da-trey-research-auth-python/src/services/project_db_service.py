from .db_service import DbService

TABLE_NAME = "Project"


class ProjectDbService:
    """Database operations for Project entities."""

    def __init__(self):
        # Projects are READ ONLY in this demo app, so we cache locally
        self._db_service = DbService(ok_to_cache_locally=True)

    async def get_project_by_id(self, project_id: str) -> dict:
        db_project = await self._db_service.get_entity_by_row_key(TABLE_NAME, project_id)
        return self._convert_db_project(db_project)

    async def get_projects(self) -> list[dict]:
        db_projects = await self._db_service.get_entities(TABLE_NAME)
        return [self._convert_db_project(p) for p in db_projects]

    @staticmethod
    def _convert_db_project(db_project: dict) -> dict:
        client_name = db_project.get("clientName", "")
        company_name_kabob = client_name.lower().replace(" ", "-")
        map_url = f"https://microsoft.github.io/copilot-camp/demo-assets/images/maps/{company_name_kabob}.jpg"
        return {
            "id": db_project.get("id", ""),
            "name": db_project.get("name", ""),
            "description": db_project.get("description", ""),
            "clientName": client_name,
            "clientContact": db_project.get("clientContact", ""),
            "clientEmail": db_project.get("clientEmail", ""),
            "location": db_project.get("location"),
            "mapUrl": map_url,
        }


# Singleton
project_db_service = ProjectDbService()
