from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models.user import UserRole

from enum import Enum
class UserSortBy(str, Enum):
    CREATED_AT = "created_at"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class UserRegister(BaseModel):
    email: EmailStr
    full_name:str = Field(min_length=2, max_length=100)
    password:str = Field(min_length=8, max_length=72)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime

class UserChangeRole(BaseModel):
    new_role: UserRole