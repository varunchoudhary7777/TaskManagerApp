from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict

from app.db.models.audit_logs import AuditAction

class AuditLogResponse(BaseModel):
    id: int
    actor_id: int | None
    action: AuditAction
    resource_type: str
    resource_id: int
    details: dict[str,Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)