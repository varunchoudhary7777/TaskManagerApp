from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from app.db.models.team_member import TeamMember
from app.db.models.team import Team
from app.db.models.user import User
from app.api.dependencies import require_admin

from app.repositories import team_repository, user_repository
from app.repositories import team_member_repository
from app.db.models.user import UserRole
from app.schemas.team import TeamMemberAdd, TeamMemberResponse, TeamResponse
from app.schemas.user import UserResponse

def add_member(db: Session, member: TeamMemberAdd, team_id: int, current_user: User) -> TeamMemberResponse:
    require_admin(current_user)

    team_required = team_repository.get_team_by_id(db, team_id)
    if team_required is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found!"
        )

    existing_user=user_repository.get_by_id(db, member.user_id)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found!"
        )

    team_member=team_member_repository.is_member(db, team_id, member.user_id)

    if team_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="team member is already in team."
        )

    team_member=TeamMember(
            team_id=team_id,
            user_id=member.user_id,
            role=member.role,
        )

    new_member=team_member_repository.add_member(db,team_member)
    return TeamMemberResponse.model_validate(new_member)

def remove_member(db: Session, member_id: int, team_id: int, current_user: User) -> None:
    require_admin(current_user)

    existing_team=team_repository.get_team_by_id(db, team_id)
    if existing_team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="team doesn't exist!"
        )

    existing_member=team_member_repository.is_member(db,team_id, member_id)
    if not existing_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user isn't a part of the team!"
        )

    team_member_repository.remove_member(db, team_id, member_id)

def get_team_members(db: Session, team_id:int, current_user: User) -> list[UserResponse]:
    require_admin(current_user)
    existing_team=team_repository.get_team_by_id(db, team_id)
    if existing_team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team doesn't exist!"
        )

    members: list[User]=team_member_repository.get_team_members(db, team_id)
    return [
        UserResponse.model_validate(member)
        for member in members
    ]

def get_user_teams(db: Session, user_id: int, current_user: User) -> list[TeamResponse]:

    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="only the admin or the respective user is allowed (Not Authorized)!"
        )


    existing_user=user_repository.get_by_id(db, user_id)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User doesn't exist!"
        )

    teams: list[Team]=team_member_repository.get_user_teams(db, user_id)
    return [
        TeamResponse.model_validate(team)
        for team in teams
    ]
