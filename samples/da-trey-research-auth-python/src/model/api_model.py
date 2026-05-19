from dataclasses import dataclass, field
from typing import Optional

from .base_model import Location, Project, Consultant


# GET requests for /projects

@dataclass
class ApiProjectAssignment:
    consultantName: str = ""
    consultantLocation: Optional[Location] = None
    role: str = ""
    forecastThisMonth: int = 0
    forecastNextMonth: int = 0
    deliveredLastMonth: int = 0
    deliveredThisMonth: int = 0


@dataclass
class ApiProject(Project):
    consultants: list[ApiProjectAssignment] = field(default_factory=list)
    forecastThisMonth: int = 0
    forecastNextMonth: int = 0
    deliveredLastMonth: int = 0
    deliveredThisMonth: int = 0


# GET requests for /me and /consultants

@dataclass
class ApiConsultantAssignment:
    projectName: str = ""
    projectDescription: str = ""
    projectLocation: Optional[Location] = None
    clientName: str = ""
    clientContact: str = ""
    clientEmail: str = ""
    role: str = ""
    forecastThisMonth: int = 0
    forecastNextMonth: int = 0
    deliveredLastMonth: int = 0
    deliveredThisMonth: int = 0


@dataclass
class ApiConsultant(Consultant):
    projects: list[ApiConsultantAssignment] = field(default_factory=list)
    forecastThisMonth: int = 0
    forecastNextMonth: int = 0
    deliveredLastMonth: int = 0
    deliveredThisMonth: int = 0


# POST request to /api/me/chargeTime

@dataclass
class ApiChargeTimeRequest:
    projectName: str = ""
    hours: int = 0


@dataclass
class ApiChargeTimeResponse:
    clientName: str = ""
    projectName: str = ""
    remainingForecast: int = 0
    message: str = ""


# POST request to /api/projects/assignConsultant

@dataclass
class ApiAddConsultantToProjectRequest:
    projectName: str = ""
    consultantName: str = ""
    role: str = ""
    hours: int = 0


@dataclass
class ApiAddConsultantToProjectResponse:
    clientName: str = ""
    projectName: str = ""
    consultantName: str = ""
    remainingForecast: int = 0
    message: str = ""


@dataclass
class ErrorResult:
    status: int = 0
    message: str = ""
