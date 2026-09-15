from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.repositories import notification_repository
from app.schemas.notification import NotificationResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser= Annotated[User, Depends(get_current_user)]

@router.get("/", response_model=list[NotificationResponse])
def list_my_notifications(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        unread_only: bool = Query(default=False)
) -> list[NotificationResponse]:
    notifications = notification_repository.list_notification_for_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
        skip=skip,
        unread_only=unread_only,
    )
    return [NotificationResponse.model_validate(notification)
            for notification in notifications
    ]

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def marky_my_notification_as_read(
        notification_id: int,
        db: DbSession,
        current_user: CurrentUser,
) -> NotificationResponse:
    notification = notification_repository.get_notifications_for_user(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notification =  notification_repository.mark_notification_as_read(
        db=db,
        notification=notification,
    )

    return NotificationResponse.model_validate(notification)