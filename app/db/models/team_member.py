from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

class TeamRole(str, Enum):
    MANAGER="manager"
    DEVELOPER="developer"
class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        primary_key = True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key = True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    role: Mapped[TeamRole] = mapped_column(
        SQLAlchemyEnum(TeamRole, native_enum=False, length=20),
        nullable=False,
        default=TeamRole.DEVELOPER,
    )
