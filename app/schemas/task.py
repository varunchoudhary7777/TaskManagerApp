from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.task import Task, TaskStatus, Priority

from enum import Enum
class TaskSortBy(str, Enum):
    CREATED_AT="created_at"
    UPDATED_AT="updated_at"
    DUE_DATE="due_date"
    PRIORITY="priority"
    STATUS="status"

class SortOrder(str, Enum):
    ASC="asc"
    DESC="desc"

"""go through this"""  ##############
class TaskBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=300)
    due_date: datetime | None = None  ##############

class CreateTaskRequest(TaskBase):
    project_id: int
    assignee_id: int | None = None
    priority: str | None = None

class UpdateTaskRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=300)
    priority: Priority | None = None
    due_date: datetime | None = None

class UpdateStatus(BaseModel):
    task_status: TaskStatus

class AssignTaskRequest(BaseModel):
    assignee_id: int

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    project_id: int
    assignee_id: int | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)