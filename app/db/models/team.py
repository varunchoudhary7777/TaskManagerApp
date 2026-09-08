from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.models.projects import Project
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(
        primary_key = True,
        autoincrement = True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique = True,
        index = True,
        nullable = False,
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="team")

    description: Mapped[str] = mapped_column(
        String(400)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default = func.now(),
        nullable = False,
    )