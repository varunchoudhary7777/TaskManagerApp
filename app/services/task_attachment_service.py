from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.task_attachment import TaskAttachment
from app.repositories import task_attachment_repository, task_repository
from app.schemas.task_attachment import TaskAttachmentResponse
from app.services import file_storage_service
from app.services.task_authorization import authorize_task_creation, authorize_task_access


async def upload_attachment(
        db: Session,
        task_id: int,
        current_user: User,
        upload_file: UploadFile
) -> TaskAttachment:
    task = task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    authorize_task_access(
        db=db,
        task=task,
        current_user=current_user
    )

    saved_file = await file_storage_service.save_uploaded_file(
        upload_file,
    )

    try:
        attachment = task_attachment_repository.create_attachment(
            db=db,
            task_id=task_id,
            uploaded_by_id=current_user.id,
            original_filename=saved_file.original_filename,
            storage_key=saved_file.storage_key,
            content_type=saved_file.content_type,
            size_bytes=saved_file.size_bytes,
        )

    except Exception:
        file_storage_service.delete_uploaded_file(saved_file.storage_key)
        raise

    return attachment

def list_task_attachments(
        db: Session,
        task_id: int,
        current_user: User,
) -> list[TaskAttachmentResponse]:
    task = task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    authorize_task_access(
        db=db,
        task=task,
        current_user=current_user
    )

    attachments = task_attachment_repository.list_attachments_for_task(
        db=db,
        task_id=task_id,
    )
    return [
        TaskAttachmentResponse.model_validate(att)
        for att in attachments
    ]

def get_attachment_for_download(
        db: Session,
        attachment_id: int,
        current_user: User,
) -> tuple[TaskAttachment, Path]:
    attachment = task_attachment_repository.get_attachment_by_id(
        db=db,
        attachment_id=attachment_id,
    )

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found.",
        )

    task = task_repository.get_task_by_id(
        db=db,
        task_id=attachment.task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    authorize_task_access(
        db=db,
        task=task,
        current_user=current_user,
    )

    file_path = file_storage_service.get_file_path(
        attachment.storage_key,
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file no longer exists."
        )

    return attachment, file_path

def delete_task_attachment(
        db: Session,
        attachment_id: int,
        current_user: User,
) -> None:
    attachment = task_attachment_repository.get_attachment_by_id(
        db=db,
        attachment_id=attachment_id,
    )

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found."
        )

    task = task_repository.get_task_by_id(
        db=db,
        task_id=attachment_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found.",
        )

    authorize_task_access(
        db=db,
        task=task,
        current_user=current_user,
    )

    storage_key = attachment.storage_key

    task_attachment_repository.delete_attachment(
        db=db,
        attachment=attachment,
    )


    file_storage_service.delete_uploaded_file(storage_key)
