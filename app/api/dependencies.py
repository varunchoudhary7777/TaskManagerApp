from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.repositories import team_member_repository
from app.core.config import settings
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.schemas.project import CreateProjectRequest

bearer_scheme=HTTPBearer()


def get_current_user(
        credentials: Annotated[
            HTTPAuthorizationCredentials,
            Depends(bearer_scheme)
        ],
        db: Annotated[Session, Depends(get_db)]
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload=jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_error

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise credentials_error

    user=db.get(User, user_id)

    if user is None:
        raise credentials_error

    return user

def require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only ADMINS can perform this action.")

