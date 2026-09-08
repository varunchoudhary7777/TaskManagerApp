from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.projects import Project, Status

from enum import Enum

class ProjectSortBy(str, Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3,max_length=250)
    team_id: int = Field(gt=0)
    status: Status = Status.ACTIVE

class UpdateProjectRequest(BaseModel):
    name: str|None = Field(default=None, min_length=3, max_length=100)
    description: str|None = Field(default=None, min_length=3, max_length=250)
    status: Status|None = None
    team_id: int = Field(gt=0)

class ProjectResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    status: Status
    team_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

class ProjectSummary(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id: int
    name: str
    status: Status

class UserSummary(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id: int
    username: str

class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class ProjectDetailedResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    status: Status

    team: TeamSummary
    created_by: UserSummary

class MoveProject(BaseModel):
    team_id: int = Field(gt=0)

class ChangeProjectStatus(BaseModel):
    status: Status

class MoveProjectRequest(BaseModel):
    new_team_id: int

