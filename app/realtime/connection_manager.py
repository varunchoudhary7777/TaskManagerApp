import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self) -> None:
        # One user can have multiple browser tabs/devices.
        self.active_connections: dict[int, set[WebSocket]] =(
            defaultdict(set)
        )

    async def connect(
        self,
            user_id: int,
            websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        self.active_connections[user_id].add(websocket)

        logger.info(
            "WebSocket connected: user_id=%s",
            user_id,
        )

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket,
    ) -> None:
        connections = self.active_connections.get(user_id)

        if connections is None:
            return

        connections.discard(websocket)

        if not connections:
            self.active_connections.pop(user_id, None)

        logger.info(
            "WebSocket disconnected: user_id=%s",
            user_id,
        )

    async def send_to_user(
        self,
        user_id: int,
        message: dict,
    ) -> None:
        connections = list(
            self.active_connections.get(user_id, set())
        )

        for websocket in connections:
            try:
                await websocket.send_json(message)

            except Exception:
                # The browser may have closed without a clean disconnect.
                self.disconnect(user_id, websocket)

notification_connection_manager = ConnectionManager()
