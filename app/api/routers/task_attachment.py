from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.task_attachment import TaskAttachmentResponse
from app.services import task_attachment_service

router = APIRouter(
    prefix="/attachments",
    tags=["Task Attachments"],
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post(
    "/task/{task_id}",
    response_model=TaskAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_task_attachment(
        task_id: int,
        file: Annotated[UploadFile, File(...)],
        db: DbSession,
        current_user: CurrentUser,
):
    return await task_attachment_service.upload_attachment(
        db=db,
        task_id=task_id,
        current_user=current_user,
        upload_file=file,
    )


@router.get(
    "/task/{task_id}",
    response_model=list[TaskAttachmentResponse],
)
def get_task_attachments(
        task_id: int,
        db: DbSession,
        current_user: CurrentUser,
) -> list[TaskAttachmentResponse]:
    return task_attachment_service.list_task_attachments(
        db=db,
        task_id=task_id,
        current_user=current_user,
    )
@router.get(
    "/{attachment_id}/download"
)
def download_attachment(
        db: DbSession,
        current_user: CurrentUser,
        attachment_id: int,
):
    attachment, file_path = (
        task_attachment_service.get_attachment_for_download(
            db=db,
            attachment_id=attachment_id,
            current_user=current_user,
        )
    )

    return FileResponse(
        path=file_path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )

@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment(
        db: DbSession,
        current_user: CurrentUser,
        attachment_id: int,
):
    task_attachment_service.delete_task_attachment(
        db=db,
        attachment_id=attachment_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)