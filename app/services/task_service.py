from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user import User, UserRole
from app.db.models.task import Task, TaskStatus, Priority
from app.db.models.projects import Project, Status

from app.schemas.task import TaskBase, TaskResponse, CreateTaskRequest, UpdateTaskRequest, UpdateStatus

from app.repositories import task_repository, project_repository, user_repository, team_member_repository
from app.services import task_authorization

from app.services import notification_service

from app.schemas.task import(
    TaskSortBy,
    SortOrder,
)

from app.core.cache import (
    delete_cache,
    get_cache_json,
    set_cache_json,
)

import json

from app.db.models.audit_logs import AuditAction
from app.services import audit_log_service


ADMIN_TASK_LIST_CACHE_KEY = "tasks:admin:list:v1"

def create_task(db: Session, data: CreateTaskRequest, current_user: User) -> TaskResponse:
    existing_project=project_repository.get_by_project_id(db, data.project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!",
        )
    task_authorization.authorize_task_creation(db, existing_project, current_user)

    duplicate=task_repository.get_task_by_title(db, data.project_id, data.title)
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="task already exists!",
        )


    if data.assignee_id is not None:
        existing_assignee = team_member_repository.is_member(db, existing_project.team_id, data.assignee_id)

        if not existing_assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assignee is not part of the team!",
            )

    task = Task(
        title=data.title,
        description=data.description,
        project_id=data.project_id,
        assignee_id=data.assignee_id,
        created_by_id=current_user.id,
    )
    task=task_repository.create_task(db, task)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.TASK_CREATED,
        resource_type="task",
        resource_id=task.id,
        details={
            "task_name": task.title,
            "project_id": task.project_id,
        },
    )

    delete_cache(ADMIN_TASK_LIST_CACHE_KEY)
    return TaskResponse.model_validate(task)

def update_task(db: Session, data: UpdateTaskRequest, project_id: int, task_id: int, current_user: User) -> TaskResponse:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!",
        )

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived projects can't be edited!",
        )

    task_authorization.authorize_task_creation(db, existing_project, current_user)

    task=task_repository.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found!",
        )

    if task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task doesn't belong to the project!"
        )

    duplicate=task_repository.get_task_by_title(db, project_id, data.title)
    if duplicate is not None and duplicate.id != task_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task with this title already exists in the project!",
        )

    if data.title is not None:
        task.title = data.title

    if data.description is not None:
        task.description = data.description

    if data.priority is not None:
        task.priority = data.priority

    if data.due_date is not None:
        task.due_date = data.due_date

    task=task_repository.update_task(db, task)
    delete_cache(ADMIN_TASK_LIST_CACHE_KEY)
    return TaskResponse.model_validate(task)


def delete_task(db: Session, task_id: int, project_id: int, current_user: User) -> None:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!",
        )

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ARCHIVED projects cannot be modified!"
        )

    task_authorization.authorize_task_creation(db, existing_project, current_user)

    task=task_repository.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found!",
        )

    if task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task doesn't belong to the project!"
        )

    task_repository.delete_task(db, task_id)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.TASK_DELETED,
        resource_type="task",
        resource_id=task.id,
        details={
            "task_name": task.title,
            "project_id": task.project_id,
        }
    )

    delete_cache(ADMIN_TASK_LIST_CACHE_KEY)

def get_task_by_id(db: Session, task_id: int, current_user: User) -> TaskResponse:
    existing_task=task_repository.get_task_by_id(db, task_id)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found!",
        )

    existing_project=project_repository.get_by_project_id(db, existing_task.project_id)

    if current_user.role == UserRole.ADMIN:
        pass

    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager can access task of a project of their managed team only!"
            )

    elif current_user.role == UserRole.DEVELOPER and team_member_repository.is_member(db, existing_project.team_id, current_user.id):
        pass

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access tasks of other teams!"
        )

    return TaskResponse.model_validate(existing_task)

def list_tasks(
        db: Session,
        current_user: User,
) -> list[TaskResponse]:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view all tasks."
        )

    cached_tasks = get_cache_json(
        ADMIN_TASK_LIST_CACHE_KEY
    )

    if cached_tasks is not None:
        return [
            TaskResponse.model_validate(task)
            for task in cached_tasks
        ]

    tasks = task_repository.get_all_tasks(db)

    response_tasks = [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

    serializable_tasks = [
        task.model_dump(mode="json")
        for task in response_tasks
    ]

    set_cache_json(
        key=ADMIN_TASK_LIST_CACHE_KEY,
        value=serializable_tasks,
    )
    return response_tasks

def search_all_tasks(db: Session, keyword: str, current_user: User) -> list[TaskResponse]:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrator can see all the tasks in search!"
        )

    tasks=task_repository.search_all_tasks(db, keyword)
    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]


def search_tasks(db: Session, keyword: str, project_id: int, current_user: User) -> list[TaskResponse]:
    existing_project=project_repository.get_by_project_id(db, project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!"
        )

    if current_user.role == UserRole.ADMIN:
        pass

    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can access tasks of team managed by them only!",
            )

    elif current_user.role == UserRole.DEVELOPER:
        if not team_member_repository.is_member(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="not allowed to see other teams tasks!"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view the tasks!"
        )

    tasks=task_repository.search_tasks(db, keyword, project_id)
    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def change_task_status(db: Session, new_status: UpdateStatus, task_id: int, current_user: User) -> TaskResponse:
    existing_task=task_repository.get_task_by_id(db, task_id)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found!"
        )

    existing_project=project_repository.get_by_project_id(db, existing_task.project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!"
        )

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update an ARCHIVED project!"
        )

    if current_user.role == UserRole.ADMIN:
        pass

    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update team as a manager!"
            )

    elif current_user.role == UserRole.DEVELOPER:
        if existing_task.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="you can only update tasks assigned to you!",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update the task status!"
        )

    existing_task.status=new_status.task_status
    task=task_repository.update_task(db, existing_task)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.TASK_STATUS_CHANGED,
        resource_type="task",
        resource_id=task.id,
        details={
            "new_status": task.status,
        }
    )

    delete_cache(ADMIN_TASK_LIST_CACHE_KEY)
    return TaskResponse.model_validate(task)


def assign_task(db: Session, task_id: int, assignee_id: int, current_user: User) -> TaskResponse:
    existing_task=task_repository.get_task_by_id(db, task_id)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found!",
        )

    if existing_task.assignee_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already assigned!",
        )

    existing_project=project_repository.get_by_project_id(db, existing_task.project_id)

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!",
        )

    if existing_project.status == Status.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ARCHIVED projects can't be updated!",
        )

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, existing_project.team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a manager for the respective project!",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to assign task!",
        )

    if not team_member_repository.is_member(db, existing_project.team_id, assignee_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignee is not part of the team!",
        )

    existing_task.assignee_id=assignee_id
    task=task_repository.update_task(db, existing_task)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.TASK_ASSIGNED,
        resource_type="task",
        resource_id=task.id,
        details={
            "assigned_to_user_id": assignee_id,
        }
    )

    if assignee_id != current_user.id:
        notification_service.create_task_assignment_notification(
            db=db,
            recipient_user_id=assignee_id,
            actor=current_user,
            task=task,
        )

    delete_cache(ADMIN_TASK_LIST_CACHE_KEY)
    return TaskResponse.model_validate(task)

def tasks_due_today(db: Session, current_user: User) -> list[TaskResponse]:
    if current_user.role == UserRole.ADMIN:
        tasks=task_repository.all_tasks_due_today(db)

    elif current_user.role == UserRole.MANAGER:
        tasks=task_repository.managed_tasks_due_today(db, current_user)

    elif current_user.role == UserRole.DEVELOPER:
        tasks=task_repository.tasks_due_today(db, current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access tasks!"
        )

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def tasks_due_this_week(db: Session, current_user: User) -> list[TaskResponse]:
    if current_user.role == UserRole.ADMIN:
        tasks=task_repository.all_tasks_due_this_week(db)

    elif current_user.role == UserRole.MANAGER:
        tasks=task_repository.managed_tasks_due_this_week(db, current_user.id)

    elif current_user.role == UserRole.DEVELOPER:
        tasks=task_repository.tasks_due_this_week(db, current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access tasks!"
        )

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def over_due_tasks(db: Session, current_user: User) -> list[TaskResponse]:
    if current_user.role == UserRole.ADMIN:
        tasks=task_repository.all_over_due_tasks(db)

    elif current_user.role == UserRole.MANAGER:
        tasks=task_repository.managed_overdue_tasks(db, current_user.id)

    elif current_user.role == UserRole.DEVELOPER:
        tasks=task_repository.overdue_tasks(db, current_user.id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to see tasks!",
        )

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def list_tasks_by_status(db: Session, task_status: TaskStatus ,current_user: User) -> list[TaskResponse]:
    if current_user.role == UserRole.ADMIN:
        tasks=task_repository.get_all_tasks_by_status(db, task_status)

    elif current_user.role == UserRole.MANAGER:
        tasks=task_repository.get_managed_task_by_status(db, task_status, current_user.id)

    elif current_user.role == UserRole.DEVELOPER:
        tasks=task_repository.get_tasks_by_status(db, task_status, current_user.id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view tasks!",
        )

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def get_tasks_by_priority(db: Session, task_priority: Priority, current_user: User) -> list[TaskResponse]:
    if current_user.role == UserRole.ADMIN:
        tasks=task_repository.get_all_tasks_by_priority(db, task_priority)

    elif current_user.role == UserRole.MANAGER:
        tasks=task_repository.get_managed_tasks_by_priority(db, task_priority, current_user.id)

    elif current_user.role == UserRole.DEVELOPER:
        tasks=task_repository.get_tasks_by_priority(db, task_priority, current_user.id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view the tasks!",
        )

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

def lists_tasks(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        status_filter: TaskStatus | None,
        assignee_id: int | None,
        search: str | None,
        sort_by: TaskSortBy,
        sort_order: SortOrder,
) -> list[TaskResponse]:
    tasks = task_repository.list_tasks_for_user(
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

    return [
        TaskResponse.model_validate(task)
        for task in tasks
    ]

