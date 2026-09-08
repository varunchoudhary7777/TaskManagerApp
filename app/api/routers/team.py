from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.team_member import TeamMember

from app.db.session import get_db
from app.repositories import team_repository
from app.schemas.auth import TokenResponse, UserLogin
from app.schemas.team import TeamMemberResponse, TeamResponse, TeamCreate, TeamUpdate, TeamMemberAdd
from app.schemas.user import UserRegister, UserResponse
from app.services import auth_service
from app.services import team_service, team_member_service

from app.schemas.team import(
    TeamSortBy,
    SortOrder,
)

router = APIRouter(
    prefix="/teams",
    tags=['Teams-Info']
)

DbSession = Annotated[Session, Depends(get_db)]

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate,db: DbSession, current_user: CurrentUser) -> TeamResponse:
    return team_service.create_team(db, data, current_user)

@router.get("/", response_model = list[TeamResponse], status_code = status.HTTP_200_OK)
def lists_teams(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        created_at: datetime | None = Query(default=None),
        search: str | None = Query(default=None, min_length=1, max_length=100),
        sort_by: TeamSortBy = Query(default=TeamSortBy.CREATED_AT),
        sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> list[TeamResponse]:
    return team_service.lists_teams(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        created_at=created_at,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.get("/{team_id}",response_model=TeamResponse, status_code=status.HTTP_200_OK)
def get_team(db:DbSession, team_id: int, current_user: CurrentUser) -> TeamResponse:
    return team_service.get_team(db, team_id, current_user)

@router.put("/{team_id}", response_model=TeamResponse, status_code=status.HTTP_200_OK)
def update_team(db: DbSession, team_id: int, team: TeamUpdate, current_user: CurrentUser) -> TeamResponse:
    return team_service.update_team(db, team_id, team, current_user)

@router.delete("/{team_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_team(db: DbSession, team_id: int, current_user: CurrentUser) -> None:
    team_service.delete_team(db, team_id, current_user)

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(db: DbSession,  new_member: TeamMemberAdd, team_id: int, current_user: CurrentUser) -> TeamMemberResponse:
    return team_member_service.add_member(db, new_member, team_id, current_user)

@router.get("/{team_id}/members", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
def get_team_members(db: DbSession, team_id: int, current_user: CurrentUser) -> list[UserResponse]:
    return team_member_service.get_team_members(db, team_id, current_user)

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(db: DbSession, team_id: int, user_id: int, current_user: CurrentUser) -> None:
    team_member_service.remove_member(db, user_id, team_id, current_user)

@router.get("/users/{user_id}/teams", response_model=list[TeamResponse], status_code=status.HTTP_200_OK)
def get_user_teams(db: DbSession, user_id: int, current_user: CurrentUser) -> list[TeamResponse]:
    return team_member_service.get_user_teams(db, user_id, current_user)

