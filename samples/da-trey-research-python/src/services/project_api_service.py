from datetime import datetime

from ..model.base_model import Project
from ..model.api_model import ApiProject, ApiProjectAssignment, ApiAddConsultantToProjectResponse
from .project_db_service import project_db_service
from .assignment_db_service import assignment_db_service
from .consultant_db_service import consultant_db_service
from .utilities import HttpError


class ProjectApiService:
    """API service for project operations."""

    def get_api_project_by_id(self, project_id: str) -> ApiProject:
        project = project_db_service.get_project_by_id(project_id)
        assignments = assignment_db_service.get_assignments()
        return self._get_api_project(project, assignments)

    def get_api_projects(self, project_or_client_name: str, consultant_name: str) -> list:
        projects = project_db_service.get_projects()
        assignments = assignment_db_service.get_assignments()

        # Filter on base properties
        if project_or_client_name:
            projects = [
                p for p in projects
                if project_or_client_name.lower() in p.name.lower()
                or project_or_client_name.lower() in p.clientName.lower()
            ]

        # Remove duplicates
        seen_ids = set()
        unique_projects = []
        for p in projects:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_projects.append(p)
        projects = unique_projects

        # Augment with assignment information
        result = [self._get_api_project(p, assignments) for p in projects]

        # Filter on consultant name
        if result and consultant_name:
            result = [
                p for p in result
                if any(consultant_name.lower() in c.consultantName.lower() for c in p.consultants)
            ]

        return result

    def _get_api_project(self, project: Project, assignments: list) -> ApiProject:
        api_project = ApiProject(
            id=project.id,
            name=project.name,
            description=project.description,
            clientName=project.clientName,
            clientContact=project.clientContact,
            clientEmail=project.clientEmail,
            location=project.location,
            mapUrl=project.mapUrl,
            consultants=[],
            forecastThisMonth=0,
            forecastNextMonth=0,
            deliveredLastMonth=0,
            deliveredThisMonth=0,
        )

        project_assignments = [a for a in assignments if a.projectId == project.id]

        for assignment in project_assignments:
            consultant = consultant_db_service.get_consultant_by_id(assignment.consultantId)
            forecast_hours = self._find_hours(assignment.forecast)
            delivered_hours = self._find_hours(assignment.delivered)

            api_project.consultants.append(ApiProjectAssignment(
                consultantName=consultant.name,
                consultantLocation=consultant.location,
                role=assignment.role,
                forecastThisMonth=forecast_hours["thisMonth"],
                forecastNextMonth=forecast_hours["nextMonth"],
                deliveredLastMonth=delivered_hours["lastMonth"],
                deliveredThisMonth=delivered_hours["thisMonth"],
            ))
            api_project.forecastThisMonth += forecast_hours["thisMonth"]
            api_project.forecastNextMonth += forecast_hours["nextMonth"]
            api_project.deliveredLastMonth += delivered_hours["lastMonth"]
            api_project.deliveredThisMonth += delivered_hours["thisMonth"]

        return api_project

    def _find_hours(self, hours: list) -> dict:
        """Extract last, this, and next month's hours from an array of HoursEntry dicts."""
        now = datetime.now()
        this_month = now.month
        this_year = now.year

        last_month = 12 if this_month == 1 else this_month - 1
        last_year = this_year - 1 if this_month == 1 else this_year

        next_month = 1 if this_month == 12 else this_month + 1
        next_year = this_year + 1 if this_month == 12 else this_year

        last_month_hours = 0.0
        this_month_hours = 0.0
        next_month_hours = 0.0

        if hours:
            for h in hours:
                m = h.get("month", 0) if isinstance(h, dict) else h.month
                y = h.get("year", 0) if isinstance(h, dict) else h.year
                hrs = h.get("hours", 0) if isinstance(h, dict) else h.hours
                if m == last_month and y == last_year:
                    last_month_hours = hrs
                elif m == this_month and y == this_year:
                    this_month_hours = hrs
                elif m == next_month and y == next_year:
                    next_month_hours = hrs

        return {
            "lastMonth": last_month_hours,
            "thisMonth": this_month_hours,
            "nextMonth": next_month_hours,
        }

    def add_consultant_to_project(
        self, project_name: str, consultant_name: str, role: str, hours: float
    ) -> ApiAddConsultantToProjectResponse:
        from .consultant_api_service import consultant_api_service

        projects = self.get_api_projects(project_name, "")
        consultants = consultant_api_service.get_api_consultants(consultant_name, "", "", "", "", "")

        if not projects:
            raise HttpError(404, f"Project not found: {project_name}")
        elif len(projects) > 1:
            raise HttpError(406, f"Multiple projects found with the name: {project_name}")
        elif not consultants:
            raise HttpError(404, f"Consultant not found: {consultant_name}")
        elif len(consultants) > 1:
            raise HttpError(406, f"Multiple consultants found with the name: {consultant_name}")

        project = projects[0]
        consultant = consultants[0]

        remaining_forecast = assignment_db_service.add_consultant_to_project(
            project.id, consultant.id, role, hours
        )
        message = (
            f'Added consultant {consultant.name} to {project.clientName} on project '
            f'"{project.name}" with {remaining_forecast} hours forecast this month.'
        )

        return ApiAddConsultantToProjectResponse(
            clientName=project.clientName,
            projectName=project.name,
            consultantName=consultant.name,
            remainingForecast=remaining_forecast,
            message=message,
        )


# Singleton instance
project_api_service = ProjectApiService()
