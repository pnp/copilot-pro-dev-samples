from dataclasses import dataclass
from typing import Optional


@dataclass
class Incident:
    number: str
    name: str
    description: str
    clientName: str
    clientContact: str
    clientEmail: str
    location: Optional[dict] = None
    mapUrl: str = ""
