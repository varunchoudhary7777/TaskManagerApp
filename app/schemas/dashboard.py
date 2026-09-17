from datetime import datetime
from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    scope: str

    active_projects: int
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    unassigned_tasks: int

    generated_at: datetime