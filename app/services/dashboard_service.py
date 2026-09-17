from datetime import UTC, datetime

from sqlalchemy.orm import Session
from app.db.models.user import User
from app.repositories import dashboard_repository
from app.schemas.dashboard import DashboardSummaryResponse

def get_dashboard_summary(
        db: Session,
        current_user: User,
) -> DashboardSummaryResponse:
    task_summary=dashboard_repository.get_task_summary(
        db=db,
        current_user=current_user,
    )

    active_projects = (
        dashboard_repository.get_active_project_count(
            db=db,
            current_user=current_user,
        )
    )

    return DashboardSummaryResponse(
        scope=current_user.role.value,
        active_projects=active_projects,
        generated_at=datetime.now(UTC),
        **task_summary,
    )