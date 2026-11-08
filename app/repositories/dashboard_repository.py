from datetime import UTC, datetime

from sqlalchemy import asc, case, desc, func, select
from sqlalchemy.orm import Session

from app.db.models.projects import Project, Status
from app.db.models.task import Task, TaskStatus
from app.db.models.team import Team
from app.db.models.team_member import TeamMember, TeamRole
from app.db.models.user import User, UserRole


def _apply_task_visibility(
    statement,
    current_user: User,
):
    """
    Adds role-based filtering to a Task query.
    """
    if current_user.role == UserRole.ADMIN:
        return statement

    if current_user.role == UserRole.MANAGER:
        return (
            statement
            .join(
                Project,
                Task.project_id == Project.id,
            )
            .join(
                TeamMember,
                TeamMember.team_id == Project.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.MANAGER,
            )
        )

    # Developers can already view tasks in projects that belong to their teams.
    # The dashboard must use the same visibility rule; otherwise it would show
    # a different (and confusing) subset of data than the rest of the product.
    return (
        statement
        .join(
            Project,
            Task.project_id == Project.id,
        )
        .join(
            TeamMember,
            TeamMember.team_id == Project.team_id,
        )
        .where(
            TeamMember.user_id == current_user.id,
            TeamMember.role == TeamRole.DEVELOPER,
        )
    )


def _apply_project_visibility(
    statement,
    current_user: User,
):
    """Limit a Project query to the teams the current user can access."""
    if current_user.role == UserRole.ADMIN:
        return statement

    membership_role = (
        TeamRole.MANAGER
        if current_user.role == UserRole.MANAGER
        else TeamRole.DEVELOPER
    )

    return (
        statement
        .join(
            TeamMember,
            TeamMember.team_id == Project.team_id,
        )
        .where(
            TeamMember.user_id == current_user.id,
            TeamMember.role == membership_role,
        )
    )


def get_task_summary(
    db: Session,
    current_user: User,
) -> dict[str, int]:
    now = datetime.now(UTC)

    statement = (
        select(
            func.count(Task.id).label("total_tasks"),

            func.coalesce(
                func.sum(
                    case(
                        (Task.status == TaskStatus.TODO, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("todo_tasks"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            Task.status == TaskStatus.IN_PROGRESS,
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("in_progress_tasks"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            Task.status == TaskStatus.COMPLETED,
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("completed_tasks"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            (Task.due_date < now)
                            & (Task.status != TaskStatus.COMPLETED),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("overdue_tasks"),

            func.coalesce(
                func.sum(
                    case(
                        (Task.assignee_id.is_(None), 1),
                        else_=0,
                    )
                ),
                0,
            ).label("unassigned_tasks"),
        )
        .select_from(Task)
    )

    statement = _apply_task_visibility(
        statement=statement,
        current_user=current_user,
    )

    row = db.execute(statement).mappings().one()

    return {
        "total_tasks": int(row["total_tasks"] or 0),
        "todo_tasks": int(row["todo_tasks"] or 0),
        "in_progress_tasks": int(row["in_progress_tasks"] or 0),
        "completed_tasks": int(row["completed_tasks"] or 0),
        "overdue_tasks": int(row["overdue_tasks"] or 0),
        "unassigned_tasks": int(row["unassigned_tasks"] or 0),
    }


def get_active_project_count(
    db: Session,
    current_user: User,
) -> int:
    statement = (
        select(func.count(func.distinct(Project.id)))
        .where(Project.status == Status.ACTIVE)
    )

    statement = _apply_project_visibility(
        statement=statement,
        current_user=current_user,
    )

    result = db.scalar(statement)

    return int(result or 0)


def get_visible_team_count(
    db: Session,
    current_user: User,
) -> int:
    """Return the number of teams represented by this dashboard's data."""
    if current_user.role == UserRole.ADMIN:
        statement = select(func.count(Team.id))
    else:
        membership_role = (
            TeamRole.MANAGER
            if current_user.role == UserRole.MANAGER
            else TeamRole.DEVELOPER
        )
        statement = (
            select(func.count(func.distinct(TeamMember.team_id)))
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == membership_role,
            )
        )

    result = db.scalar(statement)
    return int(result or 0)


def get_recent_projects(
    db: Session,
    current_user: User,
    limit: int = 5,
) -> list[Project]:
    """Return the most recently updated projects in the user's dashboard scope."""
    statement = select(Project)
    statement = _apply_project_visibility(
        statement=statement,
        current_user=current_user,
    )
    statement = statement.order_by(desc(Project.updated_at)).limit(limit)
    return list(db.scalars(statement).all())


def get_upcoming_tasks(
    db: Session,
    current_user: User,
    limit: int = 5,
) -> list[Task]:
    """Return incomplete tasks ordered by due date in the user's dashboard scope."""
    statement = select(Task).where(Task.status != TaskStatus.COMPLETED)
    statement = _apply_task_visibility(
        statement=statement,
        current_user=current_user,
    )
    statement = statement.order_by(asc(Task.due_date)).limit(limit)
    return list(db.scalars(statement).all())
