from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Location:
    street: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postalCode: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class HoursEntry:
    month: int = 0
    year: int = 0
    hours: float = 0.0


@dataclass
class Project:
    id: str = ""
    name: str = ""
    description: str = ""
    clientName: str = ""
    clientContact: str = ""
    clientEmail: str = ""
    location: Optional[Location] = None
    mapUrl: str = ""


@dataclass
class Consultant:
    id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    consultantPhotoUrl: str = ""
    location: Optional[Location] = None
    skills: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    roles: list = field(default_factory=list)


@dataclass
class Assignment:
    id: str = ""  # The assignment ID is "projectid,consultantid"
    projectId: str = ""
    consultantId: str = ""
    role: str = ""
    billable: bool = True
    rate: float = 100.0
    forecast: list = field(default_factory=list)  # list of HoursEntry
    delivered: list = field(default_factory=list)  # list of HoursEntry
