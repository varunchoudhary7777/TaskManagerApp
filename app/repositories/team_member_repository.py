from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.team_member import TeamMember, TeamRole


def add_member(db: Session, team_member: TeamMember) -> TeamMember:
    db.add(team_member)
    db.commit()
    db.refresh(team_member)
    return team_member

def remove_member(db: Session, team_id: int, user_id: int) -> None:
    request= select(TeamMember).where(TeamMember.team_id == team_id).where(TeamMember.user_id == user_id)
    statement=db.scalar(request)
    db.delete(statement)
    db.commit()

def is_member(db: Session, teamid: int, userid: int) -> bool:
    statement = select(TeamMember).where(TeamMember.team_id == teamid).where(TeamMember.user_id == userid)
    return db.scalar(statement) is not None

def get_team_members(db: Session, team_id: int) -> list[User]:
    statement = (
        select(User)
            .join(TeamMember, User.id == TeamMember.user_id)
            .where(TeamMember.team_id == team_id)
    )

    return db.scalars(statement).all()

def get_user_teams(db: Session, user_id: int) -> list[Team]:
    statement = (
        select(Team)
        .join(TeamMember, Team.id == TeamMember.team_id)
        .where(TeamMember.user_id == user_id)
    )
    return db.scalars(statement).all()

def get_managed_teams(db: Session, user_id: int) -> list[Team]:
    statement=(
        select(Team)
        .join(TeamMember, Team.id==TeamMember.team_id)
        .where(
            TeamMember.user_id==user_id,
            TeamMember.role==TeamRole.MANAGER,
        )
    )
    return db.scalars(statement).all()

def is_member_managed(db: Session, team_id: int, user_id: int) -> bool:
    statement = select(TeamMember).where(TeamMember.team_id == team_id).where(TeamMember.user_id == user_id).where(TeamMember.role==TeamRole.MANAGER)
    return db.scalar(statement) is not None

def get_by_user_id_manager(db: Session, user_id: int, team_id: int):
    statement=select(TeamMember).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id,TeamMember.role == TeamRole.MANAGER)
    return db.scalar(statement)

