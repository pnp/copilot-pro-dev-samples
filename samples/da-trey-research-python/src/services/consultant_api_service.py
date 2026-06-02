from datetime import datetime

from ..model.base_model import Consultant, HoursEntry
from ..model.api_model import ApiConsultant, ApiConsultantAssignment, ApiChargeTimeResponse
from .project_db_service import project_db_service
from .assignment_db_service import assignment_db_service
from .consultant_db_service import consultant_db_service
from .utilities import HttpError

AVAILABLE_HOURS_PER_MONTH = 160


class ConsultantApiService:
    """API service for consultant operations."""

    def get_api_consultant_by_id(self, consultant_id: str) -> ApiConsultant:
        consultant = consultant_db_service.get_consultant_by_id(consultant_id)
        if consultant:
            assignments = assignment_db_service.get_assignments()
            return self._get_api_consultant_for_base(consultant, assignments)
        return None

    def get_api_consultants(
        self, consultant_name: str, project_name: str, skill: str,
        certification: str, role: str, hours_available: str
    ) -> list:
        consultants = consultant_db_service.get_consultants()
        assignments = assignment_db_service.get_assignments()

        # Filter on base properties
        if consultant_name:
            consultants = [c for c in consultants if consultant_name.lower() in c.name.lower()]
        if skill:
            consultants = [
                c for c in consultants
                if any(skill.lower() in s.lower() for s in c.skills)
            ]
        if certification:
            consultants = [
                c for c in consultants
                if any(certification.lower() in cert.lower() for cert in c.certifications)
            ]
        if role:
            consultants = [
                c for c in consultants
                if any(role.lower() in r.lower() for r in c.roles)
            ]

        # Augment with assignment information
        result = [self._get_api_consultant_for_base(c, assignments) for c in consultants]

        # Filter on project name
        if result and project_name:
            result = [
                c for c in result
                if any(
                    project_name.lower() in (p.projectName.lower() + p.clientName.lower())
                    for p in c.projects
                )
            ]

        # Filter on available hours
        if result and hours_available:
            try:
                min_hours = int(hours_available)
                result = [
                    c for c in result
                    if (AVAILABLE_HOURS_PER_MONTH * 2 - c.forecastThisMonth - c.forecastNextMonth) >= min_hours
                ]
            except ValueError:
                pass

        return result

    def create_api_consultant(self, consultant: Consultant) -> ApiConsultant:
        consultant_db_service.create_consultant(consultant)
        assignments = assignment_db_service.get_assignments()
        return self._get_api_consultant_for_base(consultant, assignments)

    def _get_api_consultant_for_base(self, consultant: Consultant, assignments: list) -> ApiConsultant:
        api_consultant = ApiConsultant(
            id=consultant.id,
            name=consultant.name,
            email=consultant.email,
            phone=consultant.phone,
            consultantPhotoUrl=consultant.consultantPhotoUrl,
            location=consultant.location,
            skills=consultant.skills,
            certifications=consultant.certifications,
            roles=consultant.roles,
            projects=[],
            forecastThisMonth=0,
            forecastNextMonth=0,
            deliveredLastMonth=0,
            deliveredThisMonth=0,
        )

        consultant_assignments = [a for a in assignments if a.consultantId == consultant.id]

        for assignment in consultant_assignments:
            project = project_db_service.get_project_by_id(assignment.projectId)
            forecast_hours = self._find_hours(assignment.forecast)
            delivered_hours = self._find_hours(assignment.delivered)

            api_consultant.projects.append(ApiConsultantAssignment(
                projectName=project.name,
                projectDescription=project.description,
                projectLocation=project.location,
                clientName=project.clientName,
                clientContact=project.clientContact,
                clientEmail=project.clientEmail,
                role=assignment.role,
                forecastThisMonth=forecast_hours["thisMonth"],
                forecastNextMonth=forecast_hours["nextMonth"],
                deliveredLastMonth=delivered_hours["lastMonth"],
                deliveredThisMonth=delivered_hours["thisMonth"],
            ))
            api_consultant.forecastThisMonth += forecast_hours["thisMonth"]
            api_consultant.forecastNextMonth += forecast_hours["nextMonth"]
            api_consultant.deliveredLastMonth += delivered_hours["lastMonth"]
            api_consultant.deliveredThisMonth += delivered_hours["thisMonth"]

        return api_consultant

    def _find_hours(self, hours: list) -> dict:
        """Extract last, this, and next month's hours from an array of HoursEntry dicts."""
        now = datetime.now()
        this_month = now.month  # 1-based
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

    def charge_time_to_project(self, project_name: str, consultant_id: str, hours: float) -> ApiChargeTimeResponse:
        # Import here to avoid circular imports
        from .project_api_service import project_api_service

        projects = project_api_service.get_api_projects(project_name, "")
        if not projects:
            raise HttpError(404, f"Project not found: {project_name}")
        elif len(projects) > 1:
            raise HttpError(406, f"Multiple projects found with the name: {project_name}")

        project = projects[0]
        month = datetime.now().month
        year = datetime.now().year
        remaining_forecast = assignment_db_service.charge_hours_to_project(
            project.id, consultant_id, month, year, hours
        )

        if remaining_forecast < 0:
            message = (
                f'Charged {hours} hours to {project.clientName} on project "{project.name}". '
                f'You are {-remaining_forecast} hours over your forecast this month.'
            )
        else:
            message = (
                f'Charged {hours} hours to {project.clientName} on project "{project.name}". '
                f'You have {remaining_forecast} hours remaining this month.'
            )

        return ApiChargeTimeResponse(
            clientName=project.clientName,
            projectName=project.name,
            remainingForecast=remaining_forecast,
            message=message,
        )


# Singleton instance
consultant_api_service = ConsultantApiService()
