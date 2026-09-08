from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_logs import AuditAction, AuditLog

def create_audit_log(
        db: Session,
        actor_id: int | None,
        action: AuditAction,
        resource_type: str,
        resource_id: int,
        details: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log

def list_audit_logs(
        db: Session,
        limit: int,
        skip: int,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        actor_id: int | None = None,
) -> list[AuditLog]:
    statement = select(AuditLog)

    if action is not None:
        statement = statement.where(AuditLog.action == action)

    if resource_type is not None:
        statement = statement.where(AuditLog.resource_type == resource_type)

    if actor_id is not None:
        statement = statement.where(AuditLog.actor_id == actor_id)

    statement = (
        statement
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())