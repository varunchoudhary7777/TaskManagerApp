from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    actor_id: int | None
    notification_type: NotificationType
    title: str
    message: str
    resource_id: int
    details: dict[str, Any] | None
    read_at: datetime | None
    created_at: datetime

    model_Config = ConfigDict(from_attributes=True)

