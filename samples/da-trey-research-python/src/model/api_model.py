from dataclasses import dataclass, field
from typing import Optional

from .base_model import Location, Project, Consultant


@dataclass
class ApiProjectAssignment:
    consultantName: str = ""
    consultantLocation: Optional[Location] = None
    role: str = ""
    forecastThisMonth: float = 0.0
    forecastNextMonth: float = 0.0
    deliveredLastMonth: float = 0.0
    deliveredThisMonth: float = 0.0


@dataclass
class ApiProject(Project):
    consultants: list = field(default_factory=list)  # list of ApiProjectAssignment
    forecastThisMonth: float = 0.0
    forecastNextMonth: float = 0.0
    deliveredLastMonth: float = 0.0
    deliveredThisMonth: float = 0.0


@dataclass
class ApiConsultantAssignment:
    projectName: str = ""
    projectDescription: str = ""
    projectLocation: Optional[Location] = None
    clientName: str = ""
    clientContact: str = ""
    clientEmail: str = ""
    role: str = ""
    forecastThisMonth: float = 0.0
    forecastNextMonth: float = 0.0
    deliveredLastMonth: float = 0.0
    deliveredThisMonth: float = 0.0


@dataclass
class ApiConsultant(Consultant):
    projects: list = field(default_factory=list)  # list of ApiConsultantAssignment
    forecastThisMonth: float = 0.0
    forecastNextMonth: float = 0.0
    deliveredLastMonth: float = 0.0
    deliveredThisMonth: float = 0.0


@dataclass
class ApiChargeTimeResponse:
    clientName: str = ""
    projectName: str = ""
    remainingForecast: float = 0.0
    message: str = ""


@dataclass
class ApiAddConsultantToProjectResponse:
    clientName: str = ""
    projectName: str = ""
    consultantName: str = ""
    remainingForecast: float = 0.0
    message: str = ""
