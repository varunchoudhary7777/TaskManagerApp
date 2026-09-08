from typing import Annotated

from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User

from app.db.session import get_db
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.services import comment_service

from app.schemas.comment import(
    CommentsSortBy,
    SortOrder,
)

router = APIRouter(
    prefix="/comments",
    tags=["Comments"],
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(db: DbSession, data: CommentCreate, current_user: CurrentUser) -> CommentResponse:
    return comment_service.create_comment(db, data, current_user)

@router.put("/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK)
def update_comment(db: DbSession, comment_id: int, data:CommentUpdate, current_user: CurrentUser) -> CommentResponse:
    return comment_service.update_comment(db, comment_id, data, current_user)

@router.get("/task/{task_id}", response_model=list[CommentResponse], status_code=status.HTTP_200_OK)
def get_task_comments(db: DbSession, task_id: int, current_user: CurrentUser) -> list[CommentResponse]:
    return comment_service.get_task_comments(db, task_id, current_user)

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(db:DbSession, comment_id: int, current_user: CurrentUser) -> None:
    comment_service.delete_comment(db, comment_id, current_user)

@router.get("/search", response_model=list[CommentResponse], status_code=status.HTTP_200_OK)
def search_comments(db: DbSession, keyword: str, current_user: CurrentUser) -> list[CommentResponse]:
    return comment_service.search_comments(db, keyword, current_user)

@router.get("/user_comments", response_model=list[CommentResponse], status_code=status.HTTP_200_OK)
def get_user_comments(db: DbSession, current_user: CurrentUser) -> list[CommentResponse]:
    return comment_service.get_user_comments(db, current_user)


@router.get("/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK)
def get_comment(db: DbSession, comment_id: int, current_user: CurrentUser) -> CommentResponse:
    return comment_service.get_comment(db, comment_id, current_user)

@router.get("/comments/", response_model = list[CommentResponse], status_code = status.HTTP_200_OK)
def lists_comments(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        task_id: int | None = Query(default=None),
        search: str | None = Query(default=None, min_length=1, max_length=100),
        sort_by: CommentsSortBy = Query(default=CommentsSortBy.CREATED_AT),
        sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> list[CommentResponse]:
    return comment_service.lists_comments(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        task_id=task_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )