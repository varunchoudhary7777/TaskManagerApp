from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

UPLOAD_ROOT = Path(settings.upload_directory)

ALLOWED_EXTENSIONS = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpg"},
    ".jpeg": {"image/jpeg"},
    ".txt": {"text/plain"},
    ".docx": {"application/vnd.openxmlformats-offiedocument.wordprocessingml.document"},
}

CHUNK_SIZE = 1024 * 1024

@dataclass
class SavedFile:
    original_filename: str
    storage_key: str
    content_type: str
    size_bytes: int

async def save_uploaded_file(upload_file: UploadFile) -> SavedFile:
    original_filename = Path(upload_file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    suffix = Path(original_filename).suffix.lower()
    allowed_content_types = ALLOWED_EXTENSIONS.get(suffix)

    if allowed_content_types is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Allowed: PDF, PNG, JPG, TXT, DOCX.",
        )

    content_type = upload_file.content_type or "aplication/octet-stream"

    if content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File extension and content type do not match.",
        )

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_ROOT / storage_key
    total_size = 0

    try:
        with destination.open("wb") as output_file:
            while chunk := await upload_file.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="File is larger than the 10MB limit.",
                    )

                output_file.write(chunk)


    except Exception:
        destination.unlink(missing_ok=True)
        raise

    finally:
        await upload_file.close()

    return SavedFile(
        original_filename=original_filename,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=total_size
    )

def get_file_path(storage_key: str) -> Path:
    return UPLOAD_ROOT / Path(storage_key).name

def delete_uploaded_file(storage_key: str) -> None:
    get_file_path(storage_key).unlink(missing_ok=True)