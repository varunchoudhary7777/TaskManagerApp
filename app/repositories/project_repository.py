from sqlalchemy import select, asc, desc
from sqlalchemy.orm import Session
from app.db.models.projects import Project, Status
from app.db.models.team_member import TeamMember, TeamRole
from app.db.models.user import User, UserRole

from app.schemas.project import ProjectSortBy, SortOrder
def get_by_team_id(db: Session, team_id: int) -> list[Project]:
    statement=select(Project).where(Project.team_id==team_id)
    return db.scalars(statement).all()

def get_by_creator_id(db: Session, created_by_id: int) -> list[Project]:
    statement=select(Project).where(Project.created_by_id==created_by_id)
    return db.scalars(statement).all()

def get_by_project_id(db: Session, project_id: int) -> Project|None:
    return db.get(Project, project_id)

def list_projects(db: Session, limit: int = 20, skip: int = 0) -> list[Project]:
    statement=(select(Project).offset(skip).limit(limit))
    return db.scalars(statement).all()



def create_project(db: Session, new_project: Project) -> Project:
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project

def update_project(db: Session, project: Project) -> Project:
    db.commit()
    db.refresh(project)

    return project

def delete_project(db: Session, project_id: int) -> None:
    project=db.get(Project, project_id)
    if project is None:
        return
    db.delete(project)
    db.commit()

def exists_by_name(db: Session, name: str,team_id: int) -> Project|None:
    statement=select(Project).where(Project.team_id == team_id).where(Project.name==name)
    project=db.scalar(statement)
    return project

def exists_by_id(db: Session, project_id: int) -> bool:
    project=db.get(Project, project_id)
    if project is None:
        return False
    return True


def projects_by_status(db: Session, project_status: Status) -> list[Project]:
    statement=select(Project).where(Project.status==project_status)
    return db.scalars(statement).all()

def active_projects(db: Session) -> list[Project]:
    return projects_by_status(db, Status.ACTIVE)

def search_by_name(db: Session, keyword: str) -> list[Project]:
    statement=select(Project).where(Project.name.ilike(f"%{keyword}%"))
    return db.scalars(statement).all()

def search_by_name_and_team(
    db: Session,
    keyword: str,
    team_id: int,
) -> list[Project]:
    statement = (
        select(Project)
        .where(
            Project.team_id == team_id,
            Project.name.ilike(f"%{keyword}%"),
        )
    )

    return db.scalars(statement).all()

def list_projects_by_status_admin(db: Session, required_status: Status, limit: int = 20, skip: int = 0) -> list[Project]:
    statement=(select(Project).where(Project.status==required_status).order_by(Project.created_at.desc()).offset(skip).limit(limit))
    return db.scalars(statement).all()

def list_projects_by_status(db: Session, required_status: Status, user_id: int,limit: int = 20, skip: int = 0) -> list[Project]:
    statement=(select(Project)
               .join(TeamMember, TeamMember.team_id==Project.team_id)
               .where(TeamMember.user_id==user_id,
                      TeamMember.role==TeamRole.MANAGER,
                      Project.status==required_status).order_by(Project.created_at.desc()).offset(skip).limit(limit))
    return db.scalars(statement).all()

def list_projects_by_status_dev(db: Session, required_status: Status, user_id: int,limit: int = 20, skip: int = 0) -> list[Project]:
    statement=(select(Project)
               .join(TeamMember, TeamMember.team_id==Project.team_id)
               .where(TeamMember.user_id==user_id,
                      TeamMember.role==TeamRole.DEVELOPER,
                      Project.status==required_status).order_by(Project.created_at.desc()).offset(skip).limit(limit))
    return db.scalars(statement).all()

def list_projects_dev(db: Session,user_id: int,limit: int = 20, skip: int = 0) -> list[Project]:
    statement=(select(Project)
               .join(TeamMember, TeamMember.team_id==Project.team_id)
               .where(TeamMember.user_id==user_id,
                      TeamMember.role==TeamRole.DEVELOPER,).order_by(Project.created_at.desc()).offset(skip).limit(limit))
    return db.scalars(statement).all()

def list_projects_for_user(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        status_filter: Status | None,
        team_id: int | None,
        search: str | None,
        sort_by: ProjectSortBy,
        sort_order: SortOrder,
) -> list[Project]:
    statement = select(Project)

    #Authorization : decide which project this user is allowed to see.

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        statement = (
            statement
            .join(
                TeamMember,
                TeamMember.team_id == Project.team_id,
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
                TeamMember.team_id == Project.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.DEVELOPER,
            )
        )

    #filter by exact status.
    if status_filter is not None:
        statement = statement.where(
            Project.status == status_filter
        )

    #filter by exact team.
    if team_id is not None:
        statement = statement.where(
            Project.team_id == team_id
        )

    #search within project name.
    if search is not None:
        statement = statement.where(
            Project.name.ilike(f"%{search}%")
        )

    #only allow known, safe sort columns.
    sortable_columns = {
        ProjectSortBy.NAME: Project.name,
        ProjectSortBy.CREATED_AT: Project.created_at,
        ProjectSortBy.UPDATED_AT: Project.updated_at,
        ProjectSortBy.STATUS: Project.status,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(asc(sort_column))
    else:
        statement = statement.order_by(desc(sort_column))

    #pagination should happen last.
    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())

