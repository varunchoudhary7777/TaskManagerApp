from typing import Any

from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    errors: list[dict[str, Any]] | None = None