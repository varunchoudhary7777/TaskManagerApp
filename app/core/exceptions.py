import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code = exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "errors": None,
        }
    )

async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(
                str(item)
                for item in error["loc"]
            ),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Request validation failed",
            "status_code": 422,
            "errors": errors,
        }
    )

async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unexpected error: method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "errors": None,
        },
    )