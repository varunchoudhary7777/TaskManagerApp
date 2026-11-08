from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.models.user import User, UserRole
from app.repositories import dashboard_repository
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse

CurrentUser = Annotated[User, Depends(get_current_user)]


def _get_scope_copy(current_user: User) -> tuple[str, str]:
    """Return UI-safe text explaining the data boundary for each role."""
    if current_user.role == UserRole.ADMIN:
        return (
            "Workspace overview",
            "These insights include every team and project in the workspace.",
        )

    if current_user.role == UserRole.MANAGER:
        return (
            "Managed teams overview",
            "These insights include only the teams and projects you manage.",
        )

    return (
        "My team projects overview",
        "These insights include only projects and tasks in your teams.",
    )


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

    scope_label, scope_description = _get_scope_copy(current_user)
    recent_projects = dashboard_repository.get_recent_projects(
        db=db,
        current_user=current_user,
    )
    upcoming_tasks = dashboard_repository.get_upcoming_tasks(
        db=db,
        current_user=current_user,
    )

    return DashboardSummaryResponse(
        scope=current_user.role.value,
        scope_label=scope_label,
        scope_description=scope_description,
        visible_team_count=dashboard_repository.get_visible_team_count(
            db=db,
            current_user=current_user,
        ),
        active_projects=active_projects,
        generated_at=datetime.now(UTC),
        recent_projects=[
            ProjectResponse.model_validate(project)
            for project in recent_projects
        ],
        upcoming_tasks=[
            TaskResponse.model_validate(task)
            for task in upcoming_tasks
        ],
        **task_summary,
    )
