import asyncio
import json
import logging

from redis import asyncio as redis_async
from redis.exceptions import RedisError

from app.core.config import settings
from app.realtime.connection_manager import (
    notification_connection_manager,
)
from app.services.notification_service import (
    NOTIFICATION_CHANNEL,
)

logger = logging.getLogger(__name__)

async def listen_for_notifications() -> None:
    while True:
        redis_client = None
        pubsub = None

        try:
            redis_client = redis_async.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )

            pubsub = redis_client.pusbsub()

            await pubsub.subscribe(NOTIFICATION_CHANNEL)

            logger.info(
                "listening for Redis notifications: channme=%s",
                NOTIFICATION_CHANNEL,
            )

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                payload = json.loads(message["data"])

                await notification_connection_manager.send_to_user(
                    user_id=int(payload["recipient_user_id"]),
                    message=payload,
                )

        except asyncio.CancelledError:
            raise

        except (RedisError, json.JSONDecodeError):
            logger.exception(
                "Notification listener failed; retrying in 5 seconds",
            )
            await asyncio.sleep(5)

        finally:
            if pubsub is not None:
                await pubsub.aclose()

            if redis_client is not None:
                await redis_client.aclose()
