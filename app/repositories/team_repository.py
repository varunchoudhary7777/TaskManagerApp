from datetime import datetime

from sqlalchemy import select, asc, desc
from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole
from app.db.models.team import Team
from app.db.models.team_member import TeamMember, TeamRole

from app.schemas.team import(
    TeamSortBy,
    SortOrder,
)

def get_team_by_id(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)

def get_team_by_name(db: Session, team_name: str) -> Team | None:
    statement = select(Team).where(Team.name == team_name)
    return db.scalar(statement)

def list_teams(db: Session) -> list[Team]:
    statement=select(Team)
    return list(db.scalars(statement).all())

def update_team(db: Session, team: Team) -> Team:
    db.commit()
    db.refresh(team)
    return team

def delete_team(db: Session, team_id: int) -> None:
    statement=select(Team).where(Team.id == team_id)
    team=db.scalar(statement)
    db.delete(team)
    db.commit()

def create_team(db: Session, team: Team) -> Team:
    db.add(team)
    db.commit()
    db.refresh(team)

    return team

def list_team_for_user(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        created_at: datetime | None,
        search: str | None,
        sort_by: TeamSortBy,
        sort_order: SortOrder,
) -> list[Team]:
    statement = select(Team)

    #Authorization: decide which teams this user is allowed to see.
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        statement = (
            statement
            .join(
                TeamMember,
                Team.id == TeamMember.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.MANAGER,
            )
        )

    elif current_user.role == UserRole.DEVELOPER:
        statement = (
            statement
            .join(
                TeamMember,
                Team.id == TeamMember.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.DEVELOPER,
            )
        )

    #search within team name.
    if search is not None:
        statement = statement.where(
            Team.name.ilike(f"%{search}%")
        )

    #only allow known, safe sort columns.
    sortable_columns = {
        TeamSortBy.CREATED_AT: Team.created_at,
        TeamSortBy.NAME: Team.name,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(asc(sort_column))
    else:
        statement = statement.order_by(desc(sort_column))

    #pagination should happen last.
    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())