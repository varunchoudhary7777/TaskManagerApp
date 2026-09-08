from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import (
    delete_cache,
    get_cache_json,
    set_cache_json,
)
from app.db.models.audit_logs import AuditAction
from app.schemas import audit_log

from app.schemas.project import (
    ProjectSortBy,
    SortOrder,
)
from app.services import audit_log_service

PROJECT_CACHE_KEY = "project:{project_id}:v1"

def get_project_cache_key(project_id: int) -> str:
    return PROJECT_CACHE_KEY.format(project_id=project_id)

from app.db.models.user import User, UserRole
from app.db.models.team import Team
from app.db.models.projects import Project, Status
from app.repositories.team_member_repository import get_managed_teams
from app.schemas.project import CreateProjectRequest, ProjectResponse, UpdateProjectRequest

from app.services.authorization import authorize_project_creation, authorize_project_update, authorize_project_by_id
from app.repositories import user_repository, team_repository, project_repository, team_member_repository

def create_project(db: Session, data: CreateProjectRequest, current_user: User) -> ProjectResponse:
    exists_team=team_repository.get_team_by_id(db, data.team_id)
    if exists_team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not Found!",
        )

    authorize_project_creation(db, data, current_user)

    exists_project=project_repository.exists_by_name(db, data.name, data.team_id)
    if exists_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name already exists!"
        )

    project = Project(
        name=data.name,
        description=data.description,
        status=data.status,
        team_id=data.team_id,
        created_by_id=current_user.id,
    )
    project = project_repository.create_project(db, project)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_CREATED,
        resource_type="project",
        resource_id=project.id,
        details={
            "project_name": project.name,
        }
    )

    return ProjectResponse.model_validate(project)

def update_project(db: Session, update_request: UpdateProjectRequest, project_id: int, current_user: User) -> ProjectResponse:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!",
        )
    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived projects cannot be modified."
        )

    authorize_project_update(db, update_request, current_user)

    duplicate=project_repository.exists_by_name(db, update_request.name, update_request.team_id)


    if (duplicate is not None
            and duplicate.id != existing_project.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting name!"
        )


    existing_project.name=update_request.name
    existing_project.description=update_request.description
    if update_request.status is not None:
        existing_project.status = update_request.status

    project=project_repository.update_project(db, existing_project)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_UPDATED,
        resource_type="project",
        resource_id=project.id,
        details={
            "project_name": project.name,
        }
    )

    delete_cache(get_project_cache_key(project_id))

    return ProjectResponse.model_validate(project)

def delete_project(db: Session, project_id: int, current_user: User) -> None:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not Found!"
        )

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete projects.",
        )

    project_repository.delete_project(db, project_id)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_DELETED,
        resource_type="project",
        resource_id=existing_project.id,
        details={
            "project_name": existing_project.name,
        }
    )

    delete_cache(get_project_cache_key(project_id))

def get_project_by_id(db: Session, project_id: int, current_user: User) -> ProjectResponse:
    existing_project=project_repository.get_by_project_id(db, project_id)

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!"
        )

    if current_user.role == UserRole.DEVELOPER:
        is_member = team_member_repository.is_member(
            db,
            existing_project.team_id,
            current_user.id,
        )

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project's team.",
            )
    else:
        authorize_project_by_id(
            db,
            existing_project.team_id,
            current_user,
        )

    #Redis.
    cache_key = get_project_cache_key(project_id)
    cached_project = get_cache_json(cache_key)

    if cached_project is not None:
        return ProjectResponse.model_validate(cached_project)

    #Redis did not contain it: make response from MySQL.
    response = ProjectResponse.model_validate(existing_project)

    #mode="json" converts datetime/Enum values into JSON-safe values.
    set_cache_json(
        key=cache_key,
        value=response.model_dump(mode="json"),
    )

    return response

def list_projects(db: Session, current_user: User) -> list[ProjectResponse]:
    if current_user.role == UserRole.ADMIN:
        projects=project_repository.list_projects(db)

    elif current_user.role == UserRole.MANAGER:
        membership=team_member_repository.get_managed_teams(db, current_user.id)
        if len(membership) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="you are not assigned to any team."
            )
        projects = []
        for team in membership:
            projects.extend(project_repository.get_by_team_id(db, team.id))

    elif current_user.role == UserRole.DEVELOPER:
        projects = project_repository.list_projects_dev(
            db,
            current_user.id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view projects."
        )

    return [
        ProjectResponse.model_validate(project)
        for project in projects
    ]

def search_projects(db: Session, keyword: str, current_user) -> list[ProjectResponse]:
    if current_user.role == UserRole.ADMIN:
        projects=project_repository.search_by_name(db, keyword)
    elif current_user.role == UserRole.MANAGER:
        teams=team_member_repository.get_managed_teams(db, current_user.id)
        if len(teams)==0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="you are not authorized to view projects."
            )
        projects=[]
        for team in teams:
            projects.extend(project_repository.search_by_name_and_team(db, keyword, team.id))

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not authorized to view projects."
        )

    return [
        ProjectResponse.model_validate(project)
        for project in projects
    ]

def change_project_status(db: Session, new_status: Status, project_id: int, current_user: User) -> ProjectResponse:
    existing_project = project_repository.get_by_project_id(db, project_id)

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!",
        )

    authorize_project_by_id(db, existing_project.team_id, current_user)

    if existing_project.status == new_status:
        return ProjectResponse.model_validate(existing_project)

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived projects cannot be modified.",
        )

    existing_project.status=new_status
    project=project_repository.update_project(db, existing_project)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_STATUS_CHANGED,
        resource_type="project",
        resource_id=project.id,
        details={
            "project_name": project.name,
        }
    )

    return ProjectResponse.model_validate(project)


def move_project_to_another_team(db: Session, new_team_id: int, project_id: int, current_user: User) -> ProjectResponse:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!"
        )
    if existing_project.team_id == new_team_id:
        return ProjectResponse.model_validate(existing_project)

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived projects cannot be modified."
        )


    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not allowed to change the project team."
        )

    team=team_repository.get_team_by_id(db, new_team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="team doesn't exist!"
        )

    existing_project.team_id=new_team_id
    project=project_repository.update_project(db, existing_project)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_MOVED,
        resource_type="project",
        resource_id=project.id,
        details={
            "project_name": project.name,
        }
    )

    delete_cache(get_project_cache_key(project_id))

    return ProjectResponse.model_validate(project)

def archive_project(db: Session, project_id: int, current_user: User) -> ProjectResponse:
    return change_project_status(db, Status.ARCHIVED, project_id, current_user)

def restore_project(db: Session, project_id: int, current_user: User) ->ProjectResponse:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!"
        )
    if existing_project.status != Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project is not Archived!"
        )

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not authorized to restore the project."
        )

    existing_project.status=Status.ACTIVE
    project=project_repository.update_project(db, existing_project)
    return ProjectResponse.model_validate(project)

def list_project_by_status(db: Session, required_status: Status, current_user: User) -> list[ProjectResponse]:
    if current_user.role == UserRole.ADMIN:
        projects=project_repository.list_projects_by_status_admin(db, required_status)
    elif current_user.role == UserRole.MANAGER:
        projects=project_repository.list_projects_by_status(db, required_status, current_user.id)
    elif current_user.role == UserRole.DEVELOPER:
        projects=project_repository.list_projects_by_status_dev(db, required_status, current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access the projects!",
        )

    return [
        ProjectResponse.model_validate(project)
        for project in projects
    ]

def lists_projects(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        status_filter: Status | None,
        team_id: int | None,
        search: str | None,
        sort_by: ProjectSortBy,
        sort_order: SortOrder,
) -> list[ProjectResponse]:
    projects = project_repository.list_projects_for_user(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        status_filter=status_filter,
        team_id=team_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return [
        ProjectResponse.model_validate(project)
        for project in projects
    ]



