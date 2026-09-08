from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (create_access_token,
                               hash_password,
                               verify_password)

from app.db.models.user import User, UserRole
from app.db.models.team import Team
from app.db.models.projects import Project
from app.schemas.project import CreateProjectRequest, ProjectResponse, UpdateProjectRequest
from app.repositories import team_member_repository
def authorize_project_creation(db: Session, data: CreateProjectRequest, current_user: User):
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member(db, data.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can create projects for their own team!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create projects!"
        )

def authorize_project_update(db: Session, data: UpdateProjectRequest, current_user: User):
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member(db, data.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can create projects for their own team!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create projects!"
        )

def authorize_project_by_id(db: Session, team_id: int, current_user: User):
    if current_user.role == UserRole.ADMIN:
        return

    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can create projects for their own team!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create projects!"
        )