import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from redis.exceptions import RedisError

from app.core.cache import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

#This Lua script runs automatically inside Redis.
#
# 1. Increase the request count.
# 2. If this is the first request, start the expiry timer.
# 3. Return the current request count and seconds remaining.
RATE_LIMIT_LUA_SCRIPT = """
local current_count = redis.call("INCR", KEYS[1])

if current_count == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local seconds_remaining = redis.call("TTL", KEYS[1])

return {current_count, seconds_remaining}
"""

def get_client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host

def rate_limit(
        endpoint_name: str,
        max_requests: int,
        window_seconds: int,
) -> Callable:
    """
    Creates a reusable FastAPI dependency.

    Example:
        Depends(rate_limit("auth_login", 5, 60))
    """

    if max_requests < 1:
        raise ValueError("max_requests must be at least 1.")

    if window_seconds < 1:
        raise ValueError("window_seconds must be at least 1.")

    def dependency(
            request: Request,
            response: Response,
    ) -> None:
        if not settings.rate_limit_enabled:
            return

        client = get_redis_client()

        if client is None:
            if settings.rate_limit_fail_open:
                logger.warning(
                    "Rate limiting skipped because Redis is unavailable."
                )
                return

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service is temporarily unavailable."
            )

        client_ip = get_client_ip(request)

        key = f"rate_limit:{endpoint_name}:ip:{client_ip}"

        try:
            result = client.eval(
                RATE_LIMIT_LUA_SCRIPT,
                1,
                key,
                window_seconds,
            )

            request_count = int(result[0])
            seconds_remaining = max(int(result[1]), 1)

        except RedisError:
            logger.exception(
                "Redis rate-limit operation failed for key=%s",
                key,
            )

            if settings.rate_limit_fail_open:
                return

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service is temporarily unavailable.",
            )
        remaining_requests = max(
            max_requests - request_count,
            0,
        )

        #useful for Swagger/Postman/frontend debugging.
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
        response.headers["X-RateLimit-Reset-After"] = str(seconds_remaining)

        if request_count > max_requests:
            logger.warning(
                "Rate limit exceeded: endpoint=%s ip=%s",
                endpoint_name,
                client_ip,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": seconds_remaining,
                },
                headers={
                    "Retry-After": str(seconds_remaining),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

    return dependency