import json
import logging

from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.db.models.notification import NotificationType, Notification
from app.db.models.task import Task
from app.db.models.user import User
from app.repositories import notification_repository

logger = logging.getLogger(__name__)

NOTIFICATION_CHANNEL = "notifications:events:v1"

def publish_notification_event(notification: Notification) -> None:
    client = get_redis_client()

    if client is None:
        logger.warning(
            "Notification was saved but Redis is unavailable."
        )
        return

    payload = {
        "type": "notification",
        "notifications_id": notification.id,
        "recipient_user_id": notification.user_id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "resource_type": notification.resource_type,
        "resource_id": notification.resource_id,
        "details": notification.details,
        "created_id": notification.created_at,
    }

    try:
        client.publish(
            NOTIFICATION_CHANNEL,
            json.dumps(payload),
        )

    except RedisError:
        # The notification remains saved in MySQL.
        logger.exception(
            "Could not publish live notification: id=%s",
            notification.id,
        )

def create_task_assignment_notification(
        db: Session,
        recipient_user_id: int,
        actor: User,
        task: Task,
) -> None:
    notification = notification_repository.create_notification(
        db=db,
        user_id=recipient_user_id,
        actor_id=actor.id,
        notification_type=NotificationType.TASK_ASSIGNED,
        title="New Task Assigned",
        message=(
            f"{actor.full_name} assigned you the task."
            f"'{task.title}'"
        ),
        resource_type="task",
        resource_id=task.id,
        details={
            "project_id": task.project_id,
        },
    )

    publish_notification_event(notification)