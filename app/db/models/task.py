from datetime import datetime, timedelta, UTC
from enum import Enum


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.projects import Project

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class TaskStatus(str, Enum):
    TODO="TODO"
    IN_PROGRESS="IN_PROGRESS"
    COMPLETED="COMPLETED"

class Priority(str, Enum):
    LOW="LOW"
    MEDIUM="MEDIUM"
    HIGH="HIGH"
    URGENT="URGENT"

class Task(Base):
    __tablename__="tasks"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "title",
            name="uq_project_task_title",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[TaskStatus] = mapped_column(
        SQLAlchemyEnum(TaskStatus, native_enum=False, length=20),
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
        nullable=False,
        index=True,
    )

    priority: Mapped[Priority] = mapped_column(
        SQLAlchemyEnum(Priority, native_enum=False, length=20),
        default=Priority.LOW,
        server_default=Priority.LOW.value,
        nullable=False,
        index=True,
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=4),
        nullable=False,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    assignee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    assignee: Mapped["User"] = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    creator: Mapped["User"] =relationship("User", foreign_keys=[created_by_id], back_populates="tasks_created")

