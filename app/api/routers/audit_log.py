from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.api.dependencies import get_current_user, require_admin
from app.db.models.audit_logs import AuditAction, AuditLog
from app.db.models.user import User
from app.db.session import get_db
from app.repositories import audit_log_repository
from app.schemas.audit_log import AuditLogResponse

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/", response_model=list[AuditLogResponse], status_code=status.HTTP_200_OK)
def get_audit_logs(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        action: AuditAction | None = None,
        resource_type: str | None = None,
        actor_id: int | None = None,
) -> list[AuditLog]:
    require_admin(current_user)

    return audit_log_repository.list_audit_logs(
        db=db,
        limit=limit,
        skip=skip,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
    )