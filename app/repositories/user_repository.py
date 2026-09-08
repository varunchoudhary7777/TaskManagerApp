from datetime import datetime

from sqlalchemy import select, asc, desc
from sqlalchemy.orm import Session

from app.db.models.user import User, UserRole

from app.schemas.user import (
    UserSortBy,
    SortOrder, UserResponse,
)

def get_by_email(db:Session,email: str) -> User|None:
    statement=select(User).where(User.email==email)
    return db.scalar(statement)


def get_by_id(db: Session,user_id: int) -> User|None:
    return db.get(User, user_id)

def create(db:Session, user:User,) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def change_user_role(db: Session, user:User, new_role: UserRole) -> User:
    user.role=new_role
    db.commit()
    db.refresh(user)
    return user

def list_users(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        role: UserRole | None,
        search_name: str | None,
        search_email: str | None,
        created_at: datetime | None,
        sort_by: UserSortBy,
        sort_order: SortOrder,
) -> list[UserResponse]:
    statement = select(User)

    #filter exact role.
    if role is not None:
        statement = statement.where(
            User.role == role
        )

    #search within username.
    if search_name is not None:
        statement = statement.where(
            User.full_name.ilike(f"%{search_name}%")
        )

    #search within user email.
    if search_email is not None:
        statement = statement.where(
            User.email.ilike(f"%{search_email}%")
        )

    #only allow known, safe sort columns.
    sortable_columns = {
        UserSortBy.CREATED_AT: User.created_at,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(asc(sort_column))
    else:
        statement = statement.order_by(desc(sort_column))

    #pagination should happen last.
    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())