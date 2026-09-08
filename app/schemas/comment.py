from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.comments import Comment

from enum import Enum
class CommentsSortBy(str, Enum):
    CREATED_AT="created_at"
    UPDATED_AT="updated_at"

class SortOrder(str, Enum):
    ASC="asc"
    DESC="desc"

class CommentCreate(BaseModel):
    content: str
    task_id: int

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    task_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config=ConfigDict(from_attributes=True)