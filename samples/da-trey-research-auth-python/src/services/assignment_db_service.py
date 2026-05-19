from .db_service import DbService
from .utilities import HttpError

TABLE_NAME = "Assignment"


class AssignmentDbService:
    """Database operations for Assignment entities."""

    def __init__(self):
        # Assignments are READ-WRITE so disable local caching
        self._db_service = DbService(ok_to_cache_locally=False)

    async def get_assignments(self) -> list[dict]:
        db_assignments = await self._db_service.get_entities(TABLE_NAME)
        return [self._convert_db_assignment(a) for a in db_assignments]

    async def charge_hours_to_project(
        self, project_id: str, consultant_id: str, month: int, year: int, hours: int
    ) -> int:
        try:
            row_key = f"{project_id},{consultant_id}"
            db_assignment = await self._db_service.get_entity_by_row_key(TABLE_NAME, row_key)
            if not db_assignment:
                raise HttpError(404, "Assignment not found")

            # Add the hours delivered
            delivered = db_assignment.get("delivered") or []
            if not isinstance(delivered, list):
                delivered = []
            existing = next((d for d in delivered if d["month"] == month and d["year"] == year), None)
            if existing:
                existing["hours"] += hours
            else:
                delivered.append({"month": month, "year": year, "hours": hours})
            delivered.sort(key=lambda x: (x["year"], x["month"]))
            db_assignment["delivered"] = delivered

            # Subtract the hours from the forecast
            remaining_forecast = -hours
            forecast = db_assignment.get("forecast") or []
            if not isinstance(forecast, list):
                forecast = []
            existing_f = next((f for f in forecast if f["month"] == month and f["year"] == year), None)
            if existing_f:
                existing_f["hours"] -= hours
                remaining_forecast = existing_f["hours"]
            else:
                forecast.append({"month": month, "year": year, "hours": -hours})
            forecast.sort(key=lambda x: (x["year"], x["month"]))
            db_assignment["forecast"] = forecast

            await self._db_service.update_entity(TABLE_NAME, db_assignment)
            return remaining_forecast
        except HttpError:
            raise
        except Exception:
            raise HttpError(404, "Assignment not found")

    async def add_consultant_to_project(
        self, project_id: str, consultant_id: str, role: str, hours: int
    ) -> int:
        from datetime import datetime

        month = datetime.now().month
        year = datetime.now().year
        row_key = f"{project_id},{consultant_id}"

        # Check if assignment already exists
        db_assignment = None
        try:
            db_assignment = await self._db_service.get_entity_by_row_key(TABLE_NAME, row_key)
        except Exception:
            pass  # Expected — assignment doesn't exist yet

        if db_assignment:
            raise HttpError(403, "Assignment already exists")

        try:
            new_assignment = {
                "PartitionKey": TABLE_NAME,
                "RowKey": row_key,
                "id": row_key,
                "projectId": project_id,
                "consultantId": consultant_id,
                "role": role,
                "billable": True,
                "rate": 100,
                "forecast": [{"month": month, "year": year, "hours": hours}],
                "delivered": [],
            }
            await self._db_service.create_entity(TABLE_NAME, row_key, new_assignment)
            return hours
        except Exception:
            raise HttpError(500, "Unable to add assignment")

    @staticmethod
    def _convert_db_assignment(db_assignment: dict) -> dict:
        return {
            "id": db_assignment.get("id", ""),
            "projectId": db_assignment.get("projectId", ""),
            "consultantId": db_assignment.get("consultantId", ""),
            "role": db_assignment.get("role", ""),
            "billable": db_assignment.get("billable", False),
            "rate": db_assignment.get("rate", 0),
            "forecast": db_assignment.get("forecast", []),
            "delivered": db_assignment.get("delivered", []),
        }


# Singleton
assignment_db_service = AssignmentDbService()
