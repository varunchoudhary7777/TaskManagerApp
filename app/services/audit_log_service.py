from sqlalchemy.orm import Session

from app.db.models.audit_logs import AuditAction, AuditLog
from app.repositories import audit_log_repository
from app.schemas.audit_log import AuditLogResponse


def record_audit_log(
        db: Session,
        actor_id: int | None,
        action: AuditAction,
        resource_type: str,
        resource_id: int,
        details: dict | None = None,
) -> AuditLogResponse:
    audit_log = audit_log_repository.create_audit_log(
        db=db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )

    return AuditLogResponse.model_validate(audit_log)