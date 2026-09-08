from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

class AuditAction(str, Enum):
    TEAM_CREATED = "team_created"
    TEAM_UPDATED = "team_updated"
    TEAM_DELETED = "team_deleted"

    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    PROJECT_MOVED = "project_moved"
    PROJECT_DELETED = "project_deleted"

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_DELETED = "task_deleted"

    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        SQLAlchemyEnum(AuditAction, native_enum=False,),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )

    # Optional extra information about the event.
    #MySQL stores this as a JSON.
    details: Mapped[dict[str,Any] | None] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_audit_logs_resource_created_at",
            "resource_type",
            "resource_id",
            "created_at",
        ),
    )


