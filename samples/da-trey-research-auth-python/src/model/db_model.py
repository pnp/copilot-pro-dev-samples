from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base_model import Project, Consultant, Assignment


@dataclass
class DbEntity:
    etag: str = ""
    PartitionKey: str = ""
    RowKey: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class DbProject(DbEntity, Project):
    pass


@dataclass
class DbConsultant(DbEntity, Consultant):
    pass


@dataclass
class DbAssignment(DbEntity, Assignment):
    pass
