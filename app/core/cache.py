import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Redis | None = None

def get_redis_client() -> Redis | None:
    global redis_client

    if not settings.cache_enabled:
        return None

    if redis_client is None:
        try:
            redis_client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        except RedisError:
            logger.exception("Could not create Redis client.")
            return None

    return redis_client

def get_cache_json(key: str) -> Any | None:
    client = get_redis_client()

    if client is None:
        return None

    try:
        cached_value = client.get(key)

        if cached_value is None:
            logger.info("Redis cache miss: key=%s", key)
            return None

        logger.info("Redis cache hit: key=%s", key)

        return json.loads(cached_value)

    except (RedisError, json.JSONDecodeError):
        logger.exception(
            "Redis cache read failed: key=%s",
            key,
        )
        return None

def set_cache_json(
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
) -> None:
    client = get_redis_client()

    if client is None:
        return

    try:
        client.set(
            key,
            json.dumps(value),
            ex=ttl_seconds or settings.cache_ttl_seconds,
        )

        logger.info("Redis cache set: key=%s", key)

    except RedisError:
        logger.exception(
            "Redis cache write failed: key=%s",
            key,
        )

def delete_cache(key: str) -> None:
    client = get_redis_client()

    if client is None:
        return

    try:
        client.delete(key)

        logger.info("Redis cache deleted: key=%s", key)

    except RedisError:
        logger.exception(
            "Redis cache delete failed: key=%s",
            key,
        )


def get_cache_version(key: str) -> int:
    client = get_redis_client()

    if client is None:
        return 1

    try:
        value = client.get(key)

        if value is None:
            client.set(key,1)
            return 1

        return int(value)

    except (RedisError, ValueError):
        logger.exception("Could not read cache version: %s", key)
        return 1

def increment_cache_version(key: str) -> None:
    client = get_redis_client()

    if client is None:
        return

    try:
        client.incr(key)
    except RedisError:
        logger.exception("Could not increment cache version: %s", key)