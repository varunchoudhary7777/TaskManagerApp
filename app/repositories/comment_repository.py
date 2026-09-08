from datetime import datetime, timedelta, UTC

from sqlalchemy import select, asc, desc
from sqlalchemy.orm import Session

from app.db.models.comments import Comment
from app.db.models.projects import Project
from app.db.models.task import Task
from app.db.models.team_member import TeamMember, TeamRole
from app.db.models.user import User, UserRole

from app.schemas.comment import(
    CommentsSortBy,
    SortOrder,
)

def create_comment(db: Session, new_comment: Comment) -> Comment:
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    comment=db.get(Comment, comment_id)
    if comment is None:
        return None

    return comment

def get_all_comments_by_task(db: Session, task_id: int) -> list[Comment]:
    statement=select(Comment).where(Comment.task_id == task_id)
    return list(db.scalars(statement).all())

def update_comment(db: Session, updated_comment: Comment) -> Comment:
    db.commit()
    db.refresh(updated_comment)
    return updated_comment

def delete_comment(db: Session, comment_id: int) -> None:
    comment=db.get(Comment, comment_id)
    if comment is None:
        return

    db.delete(comment)
    db.commit()

def get_comment_by_id_and_author(db: Session, comment_id: int, author_id: int) -> Comment | None:
    statement=select(Comment).where(Comment.id == comment_id, Comment.author_id == author_id)
    return db.scalar(statement)

def get_comments_by_author(db: Session, author_id: int) -> list[Comment]:
    statement=select(Comment).where(Comment.author_id == author_id)
    return list(db.scalars(statement).all())

def search_all_comments(db: Session, keyword: str) -> list[Comment]:
    statement=select(Comment).where(Comment.content.ilike(f"%{keyword}%"))
    return list(db.scalars(statement).all())

def search_manager_comments(db: Session, keyword: str, user_id: int) -> list[Comment]:
    statement=(select(Comment)
               .join(Task, Task.id == Comment.task_id)
               .join(Project, Project.id ==Task.project_id)
               .join(TeamMember, TeamMember.team_id==Project.team_id
                ).where(TeamMember.user_id==user_id,
                        TeamMember.role==TeamRole.MANAGER,
                        Comment.content.ilike(f"%{keyword}%")))

    return list(db.scalars(statement).all())

def search_developer_comments(db: Session, keyword: str, user_id: int) -> list[Comment]:
    statement=(select(Comment)
               .join(Task, Task.id == Comment.task_id)
               .join(Project, Project.id ==Task.project_id)
               .join(TeamMember, TeamMember.team_id==Project.team_id
                ).where(TeamMember.user_id==user_id,
                        TeamMember.role==TeamRole.DEVELOPER,
                        Comment.content.ilike(f"%{keyword}%")))

    return list(db.scalars(statement).all())

def lists_comments(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        task_id: int | None,
        search: str | None,
        sort_by: CommentsSortBy,
        sort_order: SortOrder,
) -> list[Comment]:
    statement = (
        select(Comment)
        .join(Task, Task.id == Comment.task_id)
        .join(Project, Project.id == Task.project_id)
    )

    #Authorization: decide which comments this user is allowed to see.
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        statement = (
            statement
            .join(
                TeamMember,
                TeamMember.team_id == Project.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.MANAGER,
            )
        )

    elif current_user.role == UserRole.DEVELOPER:
        statement = (
            statement
            .join(
                TeamMember,
                TeamMember.team_id == Project.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.DEVELOPER,
            )
        )

    else:
        return []

    #filter comments belonging to one task.
    if task_id is not None:
        statement = statement.where(
            Comment.task_id == task_id,
        )

    #search within comment content.
    if search is not None:
        statement = statement.where(
            Comment.content.ilike(f"%{search}%")
        )

    sortable_columns = {
        CommentsSortBy.CREATED_AT: Comment.created_at,
        CommentsSortBy.UPDATED_AT: Comment.updated_at,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(asc(sort_column))
    else:
        statement = statement.order_by(desc(sort_column))

    #pagination should happen last.
    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())