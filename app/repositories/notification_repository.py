from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.notification import (
    Notification,
    NotificationType,
)

def create_notification(
        db: Session,
        user_id: int,
        actor_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        resource_type: str,
        resource_id: int,
        details: dict | None = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        notification_type=notification_type,
        title=title,
        message=message,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification

def list_notification_for_user(
        db: Session,
        user_id: int,
        limit: int,
        skip: int,
        unread_only: bool,
) -> list[Notification]:
    statement = select(Notification).where(
        Notification.user_id == user_id,
    )

    if unread_only:
        statement = statement.where(
            Notification.read_at.is_(None),
        )

    statement = (
        statement
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def get_notifications_for_user(
        db: Session,
        notification_id: int,
        user_id: int,
) -> Notification | None:
    statement = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )

    return db.scalar(statement)

def mark_notification_as_read(
        db: Session,
        notification: Notification,
) -> Notification:
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)

    return notification