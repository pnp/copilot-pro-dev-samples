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
    hours: int = 0


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
    id: Optional[str] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    consultantPhotoUrl: str = ""
    location: Optional[Location] = None
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)


@dataclass
class Assignment:
    id: str = ""  # The assignment ID is "projectid,consultantid"
    projectId: str = ""
    consultantId: str = ""
    role: str = ""
    billable: bool = False
    rate: int = 0
    forecast: list[HoursEntry] = field(default_factory=list)
    delivered: list[HoursEntry] = field(default_factory=list)
