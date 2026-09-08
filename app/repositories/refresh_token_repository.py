from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.refresh_token import RefreshToken

def create(
        db: Session,
        refresh_token: RefreshToken,
) -> RefreshToken:
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token

def get_by_token_hash(
        db: Session,
        token_hash: str,
) -> RefreshToken | None:
    statement = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
    )

    return db.scalar(statement)

def revoke(
        db: Session,
        refresh_token: RefreshToken,
        revoked_at: datetime,
) -> None:
    refresh_token.revoked_at = revoked_at
    db.commit()