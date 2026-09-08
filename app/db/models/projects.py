from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.team import Team
    from app.db.models.task import Task

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class Status(str,Enum):
    PLANNING="planning"
    ACTIVE="active"
    COMPLETED="completed"
    ARCHIVED="archived"


class Project(Base):
    __tablename__ = "projects"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "name",
            name="uq_team_project_name"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[Status] = mapped_column(
        SQLAlchemyEnum(Status, native_enum=False, length=20),
        default=Status.ACTIVE,
        server_default=Status.ACTIVE.value,
        nullable=False,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    team: Mapped["Team"] = relationship("Team", back_populates="projects")
    created_by: Mapped["User"] = relationship("User",back_populates="projects_created")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tasks: Mapped["Task"] = relationship("Task", back_populates="project")