from datetime import datetime
from multiprocessing import context

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.audit_logs import AuditAction
from app.db.models.comments import Comment
from app.db.models.user import User, UserRole
from app.db.models.projects import Project, Status

from app.repositories import comment_repository, task_repository, project_repository, team_member_repository
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse

from app.schemas.comment import(
    CommentsSortBy,
    SortOrder,
)

from app.core.cache import (
    delete_cache,
    get_cache_version,
    increment_cache_version,
    get_cache_json,
    set_cache_json,
)
from app.services import audit_log_service

COMMENTS_TASK_CACHE_KEY = "comments:task:{task_id}:v1"

COMMENTS_LIST_CACHE_KEY_PREFIX = "comments:list"
COMMENTS_LIST_CACHE_KEY_VERSION = "comments:list:version"

def get_comments_task_cache_key(task_id: int) -> str:
    return COMMENTS_TASK_CACHE_KEY.format(task_id=task_id)


def create_comment(db: Session, data: CommentCreate, current_user: User) -> CommentResponse:
    task=task_repository.get_task_by_id(db, data.task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found!",
        )

    project=project_repository.get_by_project_id(db, task.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!",
        )

    assignee_id=task.assignee_id
    team_id=project.team_id

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="this manager is not part of the current team!",
            )
    elif current_user.role == UserRole.DEVELOPER:
        if not team_member_repository.is_member(db, team_id, current_user.id) or assignee_id!=current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="user not the part of the team!",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user not the part of the team!",
        )

    comment = Comment(
        content=data.content,
        task_id=data.task_id,
        author_id=current_user.id,
    )

    comment=comment_repository.create_comment(db, comment)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.COMMENT_CREATED,
        resource_type="comment",
        resource_id=comment.id,
        details={
            "comment_content": comment.content,
            "task_id": comment.task_id,
        }
    )

    delete_cache(get_comments_task_cache_key(comment.task_id))
    increment_cache_version(COMMENTS_LIST_CACHE_KEY_VERSION)

    return CommentResponse.model_validate(comment)


def get_comment(db: Session, comment_id: int, current_user: User) -> CommentResponse:
    comment=comment_repository.get_comment_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="comment not found!",
        )

    task=task_repository.get_task_by_id(db, comment.task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found!",
        )

    project=project_repository.get_by_project_id(db, task.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!",
        )

    team_id=project.team_id
    assignee_id=task.assignee_id

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="manager is not managing this team!",
            )

    elif current_user.role == UserRole.DEVELOPER:
        if not team_member_repository.is_member(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="user is not part of the current team!",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is not part of the current team!",
        )

    return CommentResponse.model_validate(comment)


def get_task_comments(db: Session, task_id: int, current_user: User) -> list[CommentResponse]:
    task=task_repository.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found!",
        )

    project=project_repository.get_by_project_id(db, task.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found!",
        )

    team_id=project.team_id

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        if not team_member_repository.is_member_managed(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="not managed by the current manager!",
            )

    elif current_user.role == UserRole.DEVELOPER:
        if not team_member_repository.is_member(db, team_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="user is not part of the team!",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is not authorized!",
        )

    cache_key = get_comments_task_cache_key(task_id)
    cached_comments = get_cache_json(cache_key)

    if cached_comments is not None:
        return [
            CommentResponse.model_validate(comment)
            for comment in cached_comments
        ]

    comments_response = comment_repository.get_all_comments_by_task(db, task_id)
    set_cache_json(
        key=cache_key,
        value=[
            comment.model_dump(mode="json")
            for comment in comments_response
        ],
    )
    return comments_response

def update_comment(db: Session, comment_id: int, update_data: CommentUpdate, current_user: User) -> CommentResponse:
    comment=comment_repository.get_comment_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="comment not found!",
        )

    creator_id=comment.author_id

    if current_user.role != UserRole.ADMIN and current_user.id != creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to update the comment!",
        )

    comment.content = update_data.content

    comment=comment_repository.update_comment(db, comment)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.COMMENT_UPDATED,
        resource_type="comment",
        resource_id=comment.id,
        details={
            "comment_content": comment.content,
            "task_id": comment.task_id,
        }
    )

    delete_cache(get_comments_task_cache_key(comment.task_id))
    increment_cache_version(COMMENTS_LIST_CACHE_KEY_VERSION)

    return CommentResponse.model_validate(comment)

def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    comment=comment_repository.get_comment_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="comment not found!",
        )

    author_id=comment.author_id

    if current_user.role != UserRole.ADMIN and current_user.id != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to delete the comment!",
        )

    comment_repository.delete_comment(db, comment_id)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.COMMENT_DELETED,
        resource_type="comment",
        resource_id=comment.id,
        details={
            "comment_content": comment.content,
            "task_id": comment.task_id,
        }
    )

    delete_cache(get_comments_task_cache_key(comment.task_id))
    increment_cache_version(COMMENTS_LIST_CACHE_KEY_VERSION)

def get_user_comments(db: Session, current_user: User) -> list[CommentResponse]:
    comments=comment_repository.get_comments_by_author(db, current_user.id)
    return [
        CommentResponse.model_validate(comment)
        for comment in comments
    ]

def search_comments(db: Session, keyword: str, current_user: User) -> list[CommentResponse]:
    if current_user.role == UserRole.ADMIN:
        comments=comment_repository.search_all_comments(db, keyword)

    elif current_user.role == UserRole.MANAGER:
        comments=comment_repository.search_manager_comments(db, keyword,current_user.id)

    elif current_user.role == UserRole.DEVELOPER:
        comments=comment_repository.search_developer_comments(db, keyword, current_user.id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized!"
        )

    return [
        CommentResponse.model_validate(comment)
        for comment in comments
    ]

def get_comments_list_cache_key(
        user_id: int,
        version: int,
        limit: int,
        skip: int,
        search: str | None,
        task_id: int | None,
        sort_by: CommentsSortBy,
        sort_order: SortOrder,
) -> str:
    normalized_search = (search or "all").strip().lower()

    return (
        f"{COMMENTS_LIST_CACHE_KEY_PREFIX}:"
        f"user:{user_id}:"
        f"v:{version}:"
        f"search:{normalized_search}:"
        f"skip:{skip}:"
        f"limit:{limit}:"
        f"task_id:{task_id}:"
        f"sort:{sort_by.value}:{sort_order.value}:"
    )

def lists_comments(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        task_id: int | None,
        search: str | None,
        sort_by: CommentsSortBy,
        sort_order: SortOrder,
) -> list[CommentResponse]:

    # Read the current_cahe_version
    version = get_cache_version(COMMENTS_LIST_CACHE_KEY_VERSION)

    #Redis.
    cache_key = get_comments_list_cache_key(
        user_id=current_user.id,
        version=version,
        search=search,
        skip=skip,
        limit=limit,
        task_id=task_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    cached_comments = get_cache_json(cache_key)

    if cached_comments is not None:
        return [
            CommentResponse.model_validate(comment)
            for comment in cached_comments
        ]

    comments = comment_repository.lists_comments(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        task_id=task_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    comments_response = [
        CommentResponse.model_validate(comment)
        for comment in comments
    ]

    set_cache_json(
        key=cache_key,
        value=[
            comment.model_dump(mode="json")
            for comment in comments_response
        ]
    )

    return comments_response