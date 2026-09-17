from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import dashboard_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard and Reporting"],
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    db: DbSession,
    current_user: CurrentUser,
) -> DashboardSummaryResponse:
    return dashboard_service.get_dashboard_summary(
        db=db,
        current_user=current_user,
    )