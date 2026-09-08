from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.db.models.team_member import TeamRole

from enum import Enum
class TeamSortBy(str, Enum):
    NAME="name"
    CREATED_AT="created_at"

class SortOrder(str, Enum):
    ASC="asc"
    DESC="desc"

class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(
        min_length=3,
        max_length=100,
    )

class TeamUpdate(BaseModel):
    name: str = Field(
        default=None,
        max_length=255,
    )
    description: str = Field(
        default = None,
        max_length=255,
    )


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True,)

    id: int
    name: str
    description: str
    created_at: datetime

class TeamMemberAdd(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.DEVELOPER

class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    team_id: int
    joined_at: datetime