from datetime import datetime

from .project_db_service import project_db_service
from .assignment_db_service import assignment_db_service
from .consultant_db_service import consultant_db_service
from .consultant_api_service import consultant_api_service
from .utilities import HttpError


class ProjectApiService:
    """API-level operations for projects."""

    async def get_api_project_by_id(self, project_id: str) -> dict:
        project = await project_db_service.get_project_by_id(project_id)
        assignments = await assignment_db_service.get_assignments()
        return await self._get_api_project(project, assignments)

    async def get_api_projects(self, project_or_client_name: str = "", consultant_name: str = "") -> list[dict]:
        projects = await project_db_service.get_projects()
        assignments = await assignment_db_service.get_assignments()

        if project_or_client_name:
            q = project_or_client_name.lower()
            projects = [
                p for p in projects
                if q in p.get("name", "").lower() or q in p.get("clientName", "").lower()
            ]

        # Remove duplicates
        seen_ids = set()
        unique_projects = []
        for p in projects:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                unique_projects.append(p)
        projects = unique_projects

        results = []
        for p in projects:
            results.append(await self._get_api_project(p, assignments))

        if results and consultant_name:
            q = consultant_name.lower()
            results = [
                p for p in results
                if any(q in c.get("consultantName", "").lower() for c in p.get("consultants", []))
            ]

        return results

    async def _get_api_project(self, project: dict, assignments: list[dict]) -> dict:
        result = {**project}
        project_assignments = [a for a in assignments if a.get("projectId") == project.get("id")]

        result["consultants"] = []
        result["forecastThisMonth"] = 0
        result["forecastNextMonth"] = 0
        result["deliveredLastMonth"] = 0
        result["deliveredThisMonth"] = 0

        for assignment in project_assignments:
            consultant = await consultant_db_service.get_consultant_by_id(assignment["consultantId"])
            forecast_hours = self._find_hours(assignment.get("forecast", []))
            delivered_hours = self._find_hours(assignment.get("delivered", []))

            result["consultants"].append({
                "consultantName": consultant.get("name", ""),
                "consultantLocation": consultant.get("location"),
                "role": assignment.get("role", ""),
                "forecastThisMonth": forecast_hours["thisMonth"],
                "forecastNextMonth": forecast_hours["nextMonth"],
                "deliveredLastMonth": delivered_hours["lastMonth"],
                "deliveredThisMonth": delivered_hours["thisMonth"],
            })

            result["forecastThisMonth"] += forecast_hours["thisMonth"]
            result["forecastNextMonth"] += forecast_hours["nextMonth"]
            result["deliveredLastMonth"] += delivered_hours["lastMonth"]
            result["deliveredThisMonth"] += delivered_hours["thisMonth"]

        return result

    async def add_consultant_to_project(
        self, project_name: str, consultant_name: str, role: str, hours: int
    ) -> dict:
        projects = await self.get_api_projects(project_name, "")
        consultants = await consultant_api_service.get_api_consultants(consultant_name, "", "", "", "", "")

        if not projects:
            raise HttpError(404, f"Project not found: {project_name}")
        if len(projects) > 1:
            raise HttpError(406, f"Multiple projects found with the name: {project_name}")
        if not consultants:
            raise HttpError(404, f"Consultant not found: {consultant_name}")
        if len(consultants) > 1:
            raise HttpError(406, f"Multiple consultants found with the name: {consultant_name}")

        project = projects[0]
        consultant = consultants[0]

        remaining_forecast = await assignment_db_service.add_consultant_to_project(
            project["id"], consultant["id"], role, hours
        )
        message = (
            f'Added consultant {consultant["name"]} to {project["clientName"]} '
            f'on project "{project["name"]}" with {remaining_forecast} hours forecast this month.'
        )

        return {
            "clientName": project["clientName"],
            "projectName": project["name"],
            "consultantName": consultant["name"],
            "remainingForecast": remaining_forecast,
            "message": message,
        }

    @staticmethod
    def _find_hours(hours: list[dict]) -> dict:
        now = datetime.now()
        this_month = now.month
        this_year = now.year

        last_month = 12 if this_month == 1 else this_month - 1
        last_year = this_year - 1 if this_month == 1 else this_year

        next_month = 1 if this_month == 12 else this_month + 1
        next_year = this_year + 1 if this_month == 12 else this_year

        def get_hours(m: int, y: int) -> int:
            entry = next((h for h in hours if h.get("month") == m and h.get("year") == y), None)
            return entry["hours"] if entry else 0

        return {
            "lastMonth": get_hours(last_month, last_year),
            "thisMonth": get_hours(this_month, this_year),
            "nextMonth": get_hours(next_month, next_year),
        }


# Singleton
project_api_service = ProjectApiService()
