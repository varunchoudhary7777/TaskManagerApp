from fastapi import FastAPI
from app.api.routers import auth, team, project, task, comment, audit_log, task_attachment

import asyncio
from contextlib import asynccontextmanager

from app.realtime.notification_listner import (
    listen_for_notifications,
)


from app.api.routers import websocket

from app.api.routers import health

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)

from app.core.logging_config import configure_logging

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    notification_listener_task = asyncio.create_task(
        listen_for_notifications(),
    )

    yield

    notification_listener_task.cancel()

    try:
        await notification_listener_task
    except asyncio.CancelledError:
        pass


app=FastAPI(
    title="Task Manager API",
    lifespan=lifespan,
)


app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unexpected_exception_handler,
)


from app.db.session import engine, Base
app.include_router(auth.router)
app.include_router(team.router)
app.include_router(project.router)
app.include_router(task.router)
app.include_router(comment.router)
app.include_router(health.router)
app.include_router(audit_log.router)
app.include_router(task_attachment.router)
app.include_router(websocket.router)
Base.metadata.create_all(bind=engine)

