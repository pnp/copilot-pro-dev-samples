from datetime import datetime

from .project_db_service import project_db_service
from .assignment_db_service import assignment_db_service
from .consultant_db_service import consultant_db_service
from .utilities import HttpError

AVAILABLE_HOURS_PER_MONTH = 160


class ConsultantApiService:
    """API-level operations for consultants."""

    async def get_api_consultant_by_id(self, consultant_id: str) -> dict | None:
        consultant = await consultant_db_service.get_consultant_by_id(consultant_id)
        if consultant:
            assignments = await assignment_db_service.get_assignments()
            return await self._get_api_consultant_for_base(consultant, assignments)
        return None

    async def get_api_consultant_by_email(self, email: str) -> dict | None:
        consultants = await consultant_db_service.get_consultants()
        consultant = next((c for c in consultants if c.get("email", "").lower() == email.lower()), None)
        if consultant:
            assignments = await assignment_db_service.get_assignments()
            return await self._get_api_consultant_for_base(consultant, assignments)
        return None

    async def get_api_consultants(
        self,
        consultant_name: str = "",
        project_name: str = "",
        skill: str = "",
        certification: str = "",
        role: str = "",
        hours_available: str = "",
    ) -> list[dict]:
        consultants = await consultant_db_service.get_consultants()
        assignments = await assignment_db_service.get_assignments()

        if consultant_name:
            consultants = [c for c in consultants if consultant_name.lower() in c.get("name", "").lower()]
        if skill:
            consultants = [
                c for c in consultants
                if any(skill.lower() in s.lower() for s in (c.get("skills") or []))
            ]
        if certification:
            consultants = [
                c for c in consultants
                if any(certification.lower() in s.lower() for s in (c.get("certifications") or []))
            ]
        if role:
            consultants = [
                c for c in consultants
                if any(role.lower() in s.lower() for s in (c.get("roles") or []))
            ]

        results = []
        for c in consultants:
            results.append(await self._get_api_consultant_for_base(c, assignments))

        if results and project_name:
            results = [
                c for c in results
                if any(
                    project_name.lower() in (p.get("projectName", "") + p.get("clientName", "")).lower()
                    for p in c.get("projects", [])
                )
            ]

        if results and hours_available:
            try:
                ha = int(hours_available)
                results = [
                    c for c in results
                    if (AVAILABLE_HOURS_PER_MONTH * 2 - c["forecastThisMonth"] - c["forecastNextMonth"]) >= ha
                ]
            except ValueError:
                pass

        return results

    async def create_api_consultant(self, consultant: dict) -> dict | None:
        await consultant_db_service.create_consultant(consultant)
        assignments = await assignment_db_service.get_assignments()
        return await self._get_api_consultant_for_base(consultant, assignments)

    async def _get_api_consultant_for_base(self, consultant: dict, assignments: list[dict]) -> dict:
        result = {
            "id": consultant.get("id", ""),
            "name": consultant.get("name", ""),
            "email": consultant.get("email", ""),
            "phone": consultant.get("phone", ""),
            "consultantPhotoUrl": consultant.get("consultantPhotoUrl", ""),
            "location": consultant.get("location"),
            "skills": consultant.get("skills", []),
            "certifications": consultant.get("certifications", []),
            "roles": consultant.get("roles", []),
            "projects": [],
            "forecastThisMonth": 0,
            "forecastNextMonth": 0,
            "deliveredLastMonth": 0,
            "deliveredThisMonth": 0,
        }

        consultant_assignments = [a for a in assignments if a.get("consultantId") == consultant.get("id")]

        for assignment in consultant_assignments:
            project = await project_db_service.get_project_by_id(assignment["projectId"])
            forecast_hours = self._find_hours(assignment.get("forecast", []))
            delivered_hours = self._find_hours(assignment.get("delivered", []))

            result["projects"].append({
                "projectName": project.get("name", ""),
                "projectDescription": project.get("description", ""),
                "projectLocation": project.get("location"),
                "mapUrl": project.get("mapUrl", ""),
                "clientName": project.get("clientName", ""),
                "clientContact": project.get("clientContact", ""),
                "clientEmail": project.get("clientEmail", ""),
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

    async def charge_time_to_project(self, project_name: str, consultant_id: str, hours: int) -> dict:
        from .project_api_service import project_api_service

        projects = await project_api_service.get_api_projects(project_name, "")
        if not projects:
            raise HttpError(404, f"Project not found: {project_name}")
        if len(projects) > 1:
            raise HttpError(406, f"Multiple projects found with the name: {project_name}")

        project = projects[0]
        month = datetime.now().month
        year = datetime.now().year
        remaining_forecast = await assignment_db_service.charge_hours_to_project(
            project["id"], consultant_id, month, year, hours
        )

        if remaining_forecast < 0:
            message = (
                f'Charged {hours} hours to {project["clientName"]} on project "{project["name"]}". '
                f"You are {-remaining_forecast} hours over your forecast this month."
            )
        else:
            message = (
                f'Charged {hours} hours to {project["clientName"]} on project "{project["name"]}". '
                f"You have {remaining_forecast} hours remaining this month."
            )

        return {
            "clientName": project["clientName"],
            "projectName": project["name"],
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
consultant_api_service = ConsultantApiService()
