from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.projects import Project
from app.db.models.task import Task, Priority
from app.db.models.user import User
from app.db.models.team_member import TeamMember

from app.db.session import get_db
from app.repositories import task_repository
from app.schemas.task import CreateTaskRequest, TaskResponse, TaskStatus, UpdateTaskRequest, UpdateStatus
from app.schemas.project import CreateProjectRequest, ProjectResponse
from app.services import task_service

from app.schemas.task import(
    TaskSortBy,
    SortOrder,
)

from fastapi import BackgroundTasks

import logging
logger=logging.getLogger(__name__)

from app.repositories import user_repository
from app.services import email_service

from app.workers.email_tasks import (
    send_task_assignment_email_task,
)


router = APIRouter(
    prefix="/tasks",
    tags=['Tasks'],
)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(db: DbSession, data: CreateTaskRequest, current_user: CurrentUser) -> TaskResponse:
    return task_service.create_task(db, data, current_user)

@router.put("/update/{project_id}/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(db: DbSession, project_id: int, task_id: int, data: UpdateTaskRequest, current_user: CurrentUser) -> TaskResponse:
    return task_service.update_task(db, data, project_id, task_id,current_user)

@router.delete("/{project_id}/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(db: DbSession, task_id: int, project_id: int, current_user: CurrentUser) -> None:
    task_service.delete_task(db, task_id, project_id, current_user)

@router.get("/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def list_task(db: DbSession, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.list_tasks(db, current_user)

@router.get("/search/{keyword}", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def search_all_tasks(db: DbSession, keyword: str, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.search_all_tasks(db, keyword, current_user)

@router.get("/search_all/{keyword}/{project_id}", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def search_tasks(db: DbSession, keyword: str, project_id: int, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.search_tasks(db, keyword, project_id, current_user)

@router.put("/task_status/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def change_task_status(db: DbSession, new_status: UpdateStatus, task_id: int, current_user: CurrentUser) -> TaskResponse:
    return task_service.change_task_status(db, new_status, task_id, current_user)

@router.put(
    "/assign/{task_id}/{assignee_id}",
    response_model = TaskResponse,
    status_code = status.HTTP_200_OK,
)
def assign_task(
        background_tasks: BackgroundTasks,
        db: DbSession,
        task_id: int,
        assignee_id: int,
        current_user: CurrentUser,
) -> TaskResponse:
    task = task_service.assign_task(
        db=db,
        task_id=task_id,
        assignee_id=assignee_id,
        current_user=current_user,
    )

    assignee = user_repository.get_by_id(
        db,
        assignee_id,
    )

    # Do not send an unnecessary email when a user assigns a task to themselves.
    if assignee is not None and assignee_id != current_user.id:
        logger.info(
            "Queueing task assignment email: task_id=%s, email=%s",
            task.id,
            assignee.email,
        )

        send_task_assignment_email_task.delay(
            to_email=assignee.email,
            recipient_name=assignee.full_name,
            task_id=task.id,
            task_title=task.title,
        )

    return task

@router.get("/due_today/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def tasks_due(db: DbSession, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.tasks_due_today(db, current_user)

@router.get("/due_this_week/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def tasks_due_this_week(db: DbSession, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.tasks_due_this_week(db, current_user)

@router.get("/over_due/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def overdue_tasks(db: DbSession, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.over_due_tasks(db, current_user)

@router.get("/status/{task_status}", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def list_tasks_by_status(db: DbSession, task_status: TaskStatus, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.list_tasks_by_status(db, task_status, current_user)

@router.get("/priority/{task_priority}", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def list_tasks_by_priority(db: DbSession, task_priority: Priority, current_user: CurrentUser) -> list[TaskResponse]:
    return task_service.get_tasks_by_priority(db, task_priority, current_user)

@router.get("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task(db: DbSession, task_id: int, current_user: CurrentUser) -> TaskResponse:
    return task_service.get_task_by_id(db, task_id, current_user)


@router.get("/tasks/", response_model = list[TaskResponse], status_code = status.HTTP_200_OK)
def lists_tasks(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=1, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        status_filter: TaskStatus | None = Query(default=None, alias="status"),
        assignee_id: int | None = Query(default=None, gt=0),
        search: str | None = Query(defualt=None, min_length=1, max_length=100),
        sort_by: TaskSortBy | None = Query(default=TaskSortBy.CREATED_AT),
        sort_order: SortOrder | None = Query(default=SortOrder.DESC),
) -> list[TaskResponse]:
    return task_repository.lists_tasks(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        status_filter=status_filter,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

