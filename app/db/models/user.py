from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.models.projects import Project
    from app.db.models.task import Task
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class UserRole(str,Enum):
    ADMIN="admin"
    MANAGER="manager"
    DEVELOPER="developer"

class User(Base):
    __tablename__="users"

    id:Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email:Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    password_hash:Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    projects_created: Mapped[list["Project"]] = relationship("Project",back_populates="created_by")
    assigned_tasks: Mapped[list["Task"]] = relationship("Task",foreign_keys="Task.assignee_id", back_populates="assignee")
    tasks_created: Mapped[list["Task"]] = relationship("Task", foreign_keys="Task.created_by_id", back_populates="creator")


    role:Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, native_enum=False, length=20),
        default=UserRole.DEVELOPER,
        nullable=False,
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )