from ..model.base_model import Consultant
from .db_service import DbService

TABLE_NAME = "Consultant"


class ConsultantDbService:
    """Database operations for Consultant entities."""

    def __init__(self):
        # Consultants are READ ONLY in this demo app, so we cache locally
        self._db_service = DbService(ok_to_cache_locally=True)

    async def get_consultant_by_id(self, consultant_id: str) -> dict:
        return await self._db_service.get_entity_by_row_key(TABLE_NAME, consultant_id)

    async def get_consultants(self) -> list[dict]:
        return await self._db_service.get_entities(TABLE_NAME)

    async def create_consultant(self, consultant: dict) -> None:
        if not consultant.get("id"):
            consultants = await self.get_consultants()
            max_id = max((int(c.get("id", 0)) for c in consultants), default=0)
            consultant["id"] = str(max_id + 1)

        db_consultant = {
            **consultant,
            "etag": "",
            "PartitionKey": TABLE_NAME,
            "RowKey": consultant["id"],
        }
        await self._db_service.create_entity(TABLE_NAME, consultant["id"], db_consultant)
        print(f"Added new consultant {consultant.get('name')} ({consultant['id']}) to the Consultant table")


# Singleton
consultant_db_service = ConsultantDbService()
