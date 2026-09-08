from datetime import datetime

from pydantic import BaseModel, ConfigDict

class TaskAttachmentResponse(BaseModel):
    id: int
    task_id: int
    uploaded_by_id: int | None
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)