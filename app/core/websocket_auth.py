from typing import Annotated
from fastapi import WebSocket, status, Depends
from jose import JWTError, jwt

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import User
from app.db.session import get_db

async def get_websocket_user(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)]
) -> User | None:
    token = websocket.query_params.get("token")

    if token is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
        )
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("Token has no subject.")

        user_id = int(user_id)

    except (JWTError, ValueError):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
        )
        return None

    user = db.get(User, user_id)

    if user is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
        )
        return None

    return user