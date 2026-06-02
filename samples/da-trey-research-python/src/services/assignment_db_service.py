from datetime import datetime

from ..model.base_model import Assignment
from .db_service import DbService
from .utilities import HttpError

TABLE_NAME = "Assignment"


class AssignmentDbService:
    """Database service for Assignment entities."""

    def __init__(self):
        # Assignments are READ-WRITE so disable local caching
        self._db_service = DbService(ok_to_cache_locally=False)

    def get_assignments(self) -> list:
        entities = self._db_service.get_entities(TABLE_NAME)
        return [self._convert_db_assignment(e) for e in entities]

    def charge_hours_to_project(self, project_id: str, consultant_id: str, month: int, year: int, hours: float) -> float:
        try:
            row_key = f"{project_id},{consultant_id}"
            db_assignment = self._db_service.get_entity_by_row_key(TABLE_NAME, row_key)
            if not db_assignment:
                raise HttpError(404, "Assignment not found")

            # Add the hours delivered
            delivered = db_assignment.get("delivered", [])
            if not delivered:
                delivered = [{"month": month, "year": year, "hours": hours}]
            else:
                found = False
                for entry in delivered:
                    if entry["month"] == month and entry["year"] == year:
                        entry["hours"] += hours
                        found = True
                        break
                if not found:
                    delivered.append({"month": month, "year": year, "hours": hours})
            delivered.sort(key=lambda x: (x["year"], x["month"]))
            db_assignment["delivered"] = delivered

            # Subtract the hours from the forecast
            remaining_forecast = -hours
            forecast = db_assignment.get("forecast", [])
            if not forecast:
                forecast = [{"month": month, "year": year, "hours": -hours}]
            else:
                found = False
                for entry in forecast:
                    if entry["month"] == month and entry["year"] == year:
                        entry["hours"] -= hours
                        remaining_forecast = entry["hours"]
                        found = True
                        break
                if not found:
                    forecast.append({"month": month, "year": year, "hours": -hours})
            forecast.sort(key=lambda x: (x["year"], x["month"]))
            db_assignment["forecast"] = forecast

            self._db_service.update_entity(TABLE_NAME, db_assignment)
            return remaining_forecast
        except HttpError:
            raise
        except Exception:
            raise HttpError(404, "Assignment not found")

    def add_consultant_to_project(self, project_id: str, consultant_id: str, role: str, hours: float) -> float:
        now = datetime.now()
        month = now.month
        year = now.year

        row_key = f"{project_id},{consultant_id}"
        db_assignment = None
        try:
            db_assignment = self._db_service.get_entity_by_row_key(TABLE_NAME, row_key)
        except Exception:
            pass

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
                "delivered": []
            }
            self._db_service.create_entity(TABLE_NAME, row_key, new_assignment)
            return hours
        except HttpError:
            raise
        except Exception:
            raise HttpError(500, "Unable to add assignment")

    def _convert_db_assignment(self, db_assignment: dict) -> Assignment:
        return Assignment(
            id=db_assignment.get("id", ""),
            projectId=db_assignment.get("projectId", ""),
            consultantId=db_assignment.get("consultantId", ""),
            role=db_assignment.get("role", ""),
            billable=db_assignment.get("billable", True),
            rate=db_assignment.get("rate", 100),
            forecast=db_assignment.get("forecast", []),
            delivered=db_assignment.get("delivered", []),
        )


# Singleton instance
assignment_db_service = AssignmentDbService()
