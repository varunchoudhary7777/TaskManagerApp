from typing import Annotated

from fastapi import APIRouter, WebSocket, status, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.websocket_auth import get_websocket_user
from app.db.session import get_db
from app.realtime.connection_manager import (
    notification_connection_manager
)

router = APIRouter(
    tags = ["WebSocket Notifications"],
)

DbSession = Annotated[Session, Depends(get_db)]

@router.websocket("/ws/notifications")
async def notification_websocket(
        websocket: WebSocket,
        db: DbSession,
) -> None:
    current_user = await get_websocket_user(websocket, db)

    if current_user is None:
        return

    await notification_connection_manager.connect(
        user_id=current_user.id,
        websocket=websocket,
    )

    try:
        while True:
            # Keeps the connection alive and detects disconnects.
            message = await websocket.receive_text()

            # Optional application-level ping from frontend.
            if message == "ping":
                await websocket.send_json(
                    {"type": "pong"}
                )

    except WebSocketDisconnect:
        notification_connection_manager.disconnect(
            user_id=current_user.id,
            websocket=websocket,
        )

    except Exception:
        notification_connection_manager.disconnect(
            user_id=current_user.id,
            websocket=websocket,
        )
