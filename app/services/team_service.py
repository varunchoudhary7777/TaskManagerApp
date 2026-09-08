from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.audit_logs import AuditAction
from app.db.models.user import User, UserRole
from app.db.models.team import Team
from app.api.dependencies import require_admin
from app.repositories import team_repository
from app.repositories import team_member_repository
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate

from app.core.cache import (
    delete_cache,
    get_cache_json,
    set_cache_json,
    get_cache_version,
    increment_cache_version,
)

from app.schemas.team import(
    TeamSortBy,
    SortOrder,
)
from app.services import audit_log_service

TEAM_CACHE_KEY = "team:{team_id}:v1"
TEAMS_LIST_CACHE_PREFIX = "teams:list"
TEAMS_LIST_CACHE_VERSION = "teams:list:version"

def get_team_cache_key(team_id: int) -> str:
    return TEAM_CACHE_KEY.format(team_id=team_id)

def create_team(db: Session, data: TeamCreate, current_user: User) -> TeamResponse:
    require_admin(current_user)
    existing_team=team_repository.get_team_by_name(db, data.name)

    if existing_team is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A team with this name already exists.")

    team = Team(
        name=data.name,
        description=data.description,
    )

    created_team=team_repository.create_team(db, team)

    audit_log_service.record_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.TEAM_CREATED,
        resource_type="team",
        resource_id=created_team.id,
        details={
            "team_name": created_team.name,
        }
    )

    increment_cache_version(TEAMS_LIST_CACHE_VERSION)

    return TeamResponse.model_validate(created_team)

def get_team(db: Session, team_id: int, current_user: User) -> TeamResponse:
    require_admin(current_user)
    team=team_repository.get_team_by_id(db, team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="team with the given id doesn't exists."
        )

    #Redis.
    cache_key = get_team_cache_key(team_id)
    cached_team = get_cache_json(cache_key)

    if cached_team is not None:
        return TeamResponse.model_validate(cached_team)

    response = TeamResponse.model_validate(team)

    # model="json" converts datetime/Enum values into JSON-safe values.
    set_cache_json(
        key=cache_key,
        value=response.model_dump(mode="json")
    )

    return response


def update_team(db: Session, team_id: int,team: TeamUpdate, current_user: User) -> TeamResponse:
    require_admin(current_user)
    team_required = team_repository.get_team_by_id(db, team_id)
    if team_required is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )

    team_required.name=team.name
    team_required.description=team.description
    updated_team=team_repository.update_team(db, team_required)

    increment_cache_version(TEAMS_LIST_CACHE_VERSION)

    return TeamResponse.model_validate(updated_team)

def delete_team(db: Session, team_id: int, current_user: User) -> None:
    require_admin(current_user)
    existing_team=team_repository.get_team_by_id(db, team_id)
    if existing_team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team doesn't exist!"
        )

    team_repository.delete_team(db, team_id)

    increment_cache_version(TEAMS_LIST_CACHE_VERSION)

def get_admin_team_list_cache_key(
        user_id: int,
        version: int,
        search: str | None,
        skip: int,
        limit: int,
        created_at: datetime | None,
        sort_by: TeamSortBy,
        sort_order: SortOrder,
) -> str:
    normalized_search = (search or "all").strip().lower()
    normalized_created_at = (
        created_at.isoformat()
        if created_at is not None
        else "all"
    )
    return (
        f"{TEAMS_LIST_CACHE_PREFIX}:"
        f"user:{user_id}:"
        f"v:{version}:"
        f"search:{normalized_search}:"
        f"created_at:{normalized_created_at}:"
        f"skip:{skip}:"
        f"limit:{limit}:"
        f"sort:{sort_by.value}:{sort_order.value}"
    )

def lists_teams(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        created_at: datetime | None,
        search: str | None,
        sort_by: TeamSortBy,
        sort_order: SortOrder,
) -> list[TeamResponse]:

    # Authorization
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to list all teams."
        )

    # Read the current_cahe_version.
    version = get_cache_version(TEAMS_LIST_CACHE_VERSION)

    #Redis.
    cache_key = get_admin_team_list_cache_key(
        user_id=current_user.id,
        version=version,
        search=search,
        skip=skip,
        limit=limit,
        created_at=created_at,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    cached_teams = get_cache_json(cache_key)

    if cached_teams is not None:
        return [
            TeamResponse.model_validate(team)
            for team in cached_teams
        ]

    teams = team_repository.list_team_for_user(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        created_at=created_at,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    teams_response = [
        TeamResponse.model_validate(team)
        for team in teams
    ]

    # mode="json" converts datetime/Enum values into JSON-safe values.
    set_cache_json(
        key = cache_key,
        value = [
            team.model_dump(mode="json")
            for team in teams_response
        ]
    )

    return teams_response