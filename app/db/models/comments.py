from datetime import datetime, timedelta, UTC

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Comment(Base):
    __tablename__="comments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=False,
        index=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )