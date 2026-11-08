from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse

class DashboardSummaryResponse(BaseModel):
    scope: str
    scope_label: str
    scope_description: str
    visible_team_count: int

    active_projects: int
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    unassigned_tasks: int

    generated_at: datetime

    # These previews are deliberately returned from the dashboard endpoint
    # instead of making the UI call an admin-only global task endpoint.
    recent_projects: list[ProjectResponse] = Field(default_factory=list)
    upcoming_tasks: list[TaskResponse] = Field(default_factory=list)
