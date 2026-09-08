from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.task_attachment import TaskAttachment

def create_attachment(
        db: Session,
        task_id: int,
        uploaded_by_id: int,
        original_filename: str,
        storage_key: str,
        content_type: str,
        size_bytes: int,
) -> TaskAttachment:
    attachment = TaskAttachment(
        task_id=task_id,
        uploaded_by_id=uploaded_by_id,
        original_filename=original_filename,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=size_bytes,
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment

def get_attachment_by_id(
        db: Session,
        attachment_id: int,
) -> TaskAttachment | None:
    statement = select(TaskAttachment).where(TaskAttachment.id == attachment_id)
    return db.scalar(statement)


def list_attachments_for_task(
        db: Session,
        task_id: int,
) -> list[TaskAttachment]:
    statement = (
        select(TaskAttachment)
        .where(TaskAttachment.task_id == task_id)
        .order_by(TaskAttachment.created_at.desc())
    )

    return list(db.scalars(statement).all())

def delete_attachment(
        db: Session,
        attachment: TaskAttachment,
) -> None:
    db.delete(attachment)
    db.commit()