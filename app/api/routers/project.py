from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.projects import Project, Status
from app.db.models.user import User

from app.db.session import get_db
from app.schemas.project import CreateProjectRequest, ProjectResponse, UpdateProjectRequest, ChangeProjectStatus, \
    MoveProjectRequest, ProjectSortBy
from app.services import project_service

from app.schemas.project import (
        ProjectSortBy,
        SortOrder,
)



router = APIRouter(
    prefix="/projects",
    tags=['Projects'],
)

DbSession = Annotated[Session, Depends(get_db)]

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(db: DbSession, data: CreateProjectRequest, current_user: CurrentUser) -> ProjectResponse:
    return project_service.create_project(db, data, current_user)



@router.get("/search/{keyword}", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
def search_projects(db: DbSession, keyword: str, current_user: CurrentUser) -> list[ProjectResponse]:
    return project_service.search_projects(db, keyword, current_user)

@router.get("/active_projects", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
def list_active_projects(db: DbSession, current_user: CurrentUser) -> list[ProjectResponse]:
    return project_service.list_project_by_status(db, Status.ACTIVE, current_user)

@router.get("/archived_projects", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
def list_archived_projects(db: DbSession, current_user: CurrentUser) -> list[ProjectResponse]:
    return project_service.list_project_by_status(db, Status.ARCHIVED, current_user)

@router.get("/completed_projects", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
def list_completed_projects(db: DbSession, current_user: CurrentUser) -> list[ProjectResponse]:
    return project_service.list_project_by_status(db, Status.COMPLETED, current_user)

@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(db: DbSession, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.get_project_by_id(db, project_id, current_user)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(db: DbSession, project_id: int , current_user: CurrentUser) -> None:
    project_service.delete_project(db, project_id, current_user)

@router.put("/status/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def change_status(db: DbSession, new_status: ChangeProjectStatus, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.change_project_status(db, new_status.status, project_id, current_user)

@router.put("/archive/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def archive_project(db: DbSession, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.archive_project(db, project_id, current_user)

@router.put("/restore/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def restore_project(db: DbSession, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.restore_project(db, project_id, current_user)

@router.put("/move/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def move_project(db: DbSession, new_team: MoveProjectRequest, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.move_project_to_another_team(db, new_team.new_team_id, project_id, current_user)

@router.put("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK )
def update_project(db:DbSession, data: UpdateProjectRequest, project_id: int, current_user: CurrentUser) -> ProjectResponse:
    return project_service.update_project(db, data, project_id, current_user)


@router.get("/", response_model = list[ProjectResponse], status_code = status.HTTP_200_OK)
def list_projects(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        status_filter: Status | None = Query(default=None, alias = "status"),
        team_id : int | None = Query(default=None, gt=0),
        search: str | None = Query(default=None, min_length=1, max_length=100),
        sort_by: ProjectSortBy = Query(default=ProjectSortBy.CREATED_AT),
        sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> list[ProjectResponse]:
    return project_service.lists_projects(
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