from datetime import UTC, datetime
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models.projects import Project, Status
from app.db.models.task import Task, TaskStatus
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
            ).where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.MANAGER,
            )
        )

    # Developer sees only tasks assigned to them.
    return statement.where(
        Task.assignee_id == current_user.id
    )

def get_task_summary(
        db: Session,
        current_user: User,
) -> dict[str,int]:
    now = datetime.now(UTC)

    statement = select(
        func.count(Task.id).label("total_tasks"),

        func.colasce(
            func.sum(
                case(
                    (Task.status == TaskStatus.TODO, 1),
                    else_=0,
                )
            ),
            0,
        ).label("todo_tasks"),

        func.colasce(
            func.sum(
                case(
                    (Task.status == TaskStatus.IN_PROGRESS, 1),
                    else_=0,
                )
            ),
            0,
        ).label("in_progress_tasks"),

        func.colasce(
            func.sum(
                case(
                    (Task.status == TaskStatus.COMPLETED, 1),
                    else_=0,
                )
            ),
            0,
        ).label("completed_tasks"),

        func.colasce(
            func.sum(
                case(
                    (
                    (Task.due_date < now)
                        & (TaskStatus.status != TaskStatus.COMPLETED),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("overdue_tasks"),

        func.colasce(
            func.sum(
                case(
                    (Task.assignee_id.is_(None), 1),
                    else_=0,
                )
            ),
            0,
        ).label("unassigned_tasks"),
    ).select_from(Task)

    statement = _apply_task_visibility(
        statement=statement,
        current_user=current_user,
    )

    row=db.execute(statement).mappings().one()

    return {
        "total_tasks": int(row["total_tasks"] or 0),
        "todo_tasks": int(row["todo_tasks"] or 0),
        "in_progress_tasks": int(
            row["in_progress_tasks"] or 0
        ),
        "completed_tasks": int(
            row["completed_tasks"] or 0
        ),
        "overdue_tasks": int(row["overdue_tasks"] or 0),
        "unassigned_tasks": int(
            row["unassigned_tasks"] or 0
        ),
    }

def get_active_project_count(
        db: Session,
        current_user: User,
) -> int:
    statement = (
        select(func.count(Project.id))
        .where(Project.status == Status.ACTIVE)
    )

    if current_user.role == UserRole.MANAGER:
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

    result = db.scalar(statement)

    return int(result or 0)

