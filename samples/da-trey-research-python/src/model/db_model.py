from dataclasses import dataclass, field
from typing import Optional
from .base_model import Project, Consultant, Assignment


@dataclass
class DbEntity:
    partitionKey: str = ""
    rowKey: str = ""
    etag: str = ""
    timestamp: Optional[str] = None


@dataclass
class DbProject(DbEntity, Project):
    pass


@dataclass
class DbConsultant(DbEntity, Consultant):
    pass


@dataclass
class DbAssignment(DbEntity, Assignment):
    pass
