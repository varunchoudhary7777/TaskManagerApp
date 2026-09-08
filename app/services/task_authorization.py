from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.task import Task
from app.db.models.projects import Project
from app.schemas import project

from app.schemas.task import TaskBase, TaskResponse, CreateTaskRequest
from app.schemas.user import UserResponse, UserRole
from app.schemas.project import ChangeProjectStatus, ProjectResponse

from app.repositories import team_member_repository, project_repository


def authorize_task_creation(db: Session, existing_project: Project, current_user: User):
    if current_user.role == UserRole.ADMIN:
        return
    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can create tasks for projects for their teams only!",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not authorized to create tasks for this project!",
        )


def authorize_task_access(
    db: Session,
    task: Task,
    current_user: User,
) -> None:
    # Find the project to which this task belongs.
    existing_project = project_repository.get_by_project_id(
        db=db,
        project_id=task.project_id,
    )

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project for this task was not found.",
        )

    # Admin can access every task.
    if current_user.role == UserRole.ADMIN:
        return

    # Manager can access tasks only in teams they manage.
    if current_user.role == UserRole.MANAGER:
        is_manager_of_team = team_member_repository.is_member_managed(
            db=db,
            team_id=existing_project.team_id,
            user_id=current_user.id,
        )

        if is_manager_of_team:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers can access tasks only in their managed teams.",
        )

    # Developer can access tasks only in teams they belong to.
    if current_user.role == UserRole.DEVELOPER:
        is_team_member = team_member_repository.is_member(
            db=db,
            teamid=existing_project.team_id,
            userid=current_user.id,
        )

        if is_team_member:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this task's team.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to access this task.",
    )