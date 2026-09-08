from fastapi import FastAPI
from app.api.routers import auth, team, project, task, comment, audit_log, task_attachment

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

app=FastAPI(title="Task Manager API")


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
Base.metadata.create_all(bind=engine)

