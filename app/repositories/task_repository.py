from datetime import datetime, timedelta
from datetime import UTC
from operator import or_

from sqlalchemy import select, asc, desc
from sqlalchemy.orm import Session

from app.db.models.projects import Project
from app.db.models.task import Task, TaskStatus, Priority
from app.db.models.team_member import TeamMember, TeamRole
from app.db.models.user import User, UserRole
from app.schemas.task import CreateTaskRequest, TaskResponse

from app.schemas.task import(
    TaskSortBy,
    SortOrder,
)

def create_task(db: Session, new_task: Task) -> Task:
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_task_by_id(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)

def get_all_tasks(db: Session) -> list[Task]:
    statement=select(Task)
    return list(db.scalars(statement).all())

def get_tasks_by_project(db: Session, project_id: int) -> list[Task]:
    statement=select(Task).where(Task.project_id==project_id)
    return list(db.scalars(statement).all())

def get_task_by_title(db: Session, project_id: int, title: str) -> Task | None:
    statement=select(Task).where(Task.title==title, Task.project_id==project_id)
    return db.scalar(statement)

def get_task_assigned_to_a_user(db: Session, user_id: int) -> list[Task]:
    statement=select(Task).where(Task.assignee_id==user_id)
    return list(db.scalars(statement).all())

def get_tasks_created_by_a_user(db: Session, user_id: int) -> list[Task]:
    statement=select(Task).where(Task.created_by_id==user_id)
    return list(db.scalars(statement).all())

def update_task(db: Session, updated_task: Task) -> Task:
    db.commit()
    db.refresh(updated_task)
    return updated_task

def delete_task(db: Session, task_id: int) -> None:
    task=db.get(Task, task_id)
    if task is None:
        return
    db.delete(task)
    db.commit()

def get_all_tasks_by_status(db: Session, task_status: TaskStatus) -> list[Task]:
    statement=select(Task).where(Task.status==task_status)
    return list(db.scalars(statement).all())

def get_tasks_by_status(db: Session, task_status: TaskStatus, current_user: int) -> list[Task]:
    statement=select(Task).where(Task.status == task_status, Task.assignee_id == current_user)
    return list(db.scalars(statement).all())

def get_managed_task_by_status(db: Session, task_status: TaskStatus, current_user: int) -> list[Task]:
    statement=(select(Task)
               .join(Project)
               .join(TeamMember,
                TeamMember.team_id == Project.team_id)
                    .where(TeamMember.user_id == current_user,
                           TeamMember.role ==  TeamRole.MANAGER,
                           Task.status == task_status)
               )
    return list(db.scalars(statement).all())

def get_all_tasks_by_priority(db: Session, task_priority: Priority) -> list[Task]:
    statement=select(Task).where(Task.priority==task_priority)
    return list(db.scalars(statement).all())

def get_managed_tasks_by_priority(db: Session, task_priority: Priority, current_user: int) -> list[Task]:
    statement=(select(Task)
               .join(Project)
               .join(TeamMember,
                     TeamMember.team_id == Project.team_id)
               .where(TeamMember.user_id == current_user,
                      TeamMember.role == TeamRole.MANAGER,
                      Task.priority == task_priority,)
               )
    return list(db.scalars(statement).all())

def get_tasks_by_priority(db: Session, task_priority: Priority, current_user: int) -> list[Task]:
    statement=select(Task).where(Task.priority==task_priority, Task.assignee_id==current_user)
    return list(db.scalars(statement).all())

def tasks_due_today(db: Session, user_id: int) -> list[Task]:
    today=datetime.now(UTC).date()
    start=datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    end=start+timedelta(days=1)
    statement=select(Task).where(Task.assignee_id==user_id).where(Task.due_date>=start, Task.due_date<end)
    return list(db.scalars(statement).all())

def all_tasks_due_today(db: Session) -> list[Task]:
    today=datetime.now(UTC).date()
    start=datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    end=start+timedelta(days=1)
    statement=select(Task).where(Task.due_date>=start, Task.due_date<end)
    return list(db.scalars(statement).all())

def managed_tasks_due_today(db: Session, current_user: User) -> list[Task]:
    today = datetime.now(UTC).date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    end = start + timedelta(days=1)
    statement=(select(Task)
               .join(Project)
               .join(TeamMember,
                     Project.team_id == TeamMember.team_id,
               )
               .where(TeamMember.user_id == current_user.id,
                      TeamMember.role == TeamRole.MANAGER,
                      Task.due_date>=start,
                      Task.due_date<end
               )
    )

    return list(db.scalars(statement).all())


def overdue_tasks(db: Session, user_id: int) -> list[Task]:
    statement=select(Task).where(Task.assignee_id==user_id,
                                 Task.due_date<datetime.now(UTC),
                                 Task.status!=TaskStatus.COMPLETED).order_by(Task.due_date.asc())
    return list(db.scalars(statement).all())

def all_over_due_tasks(db: Session) -> list[Task]:
    statement=select(Task).where(Task.due_date<datetime.now(UTC),
                                 Task.status != TaskStatus.COMPLETED).order_by(Task.due_date.asc())
    return list(db.scalars(statement).all())

def managed_overdue_tasks(db: Session, current_user: int) -> list[Task]:
    statement=(select(Task)
               .join(Project)
               .join(TeamMember,
                     Project.team_id == TeamMember.team_id,
                ).where(TeamMember.user_id == current_user.id,
                        TeamMember.role == TeamRole.MANAGER,
                        Task.due_date<datetime.now(UTC),
                        Task.status != TaskStatus.COMPLETED).order_by(Task.due_date.asc())

               )

    return list(db.scalars(statement).all())

def tasks_due_this_week(db: Session, user_id: int) -> list[Task]:
    today=datetime.now(UTC).date()
    week_start=today - timedelta(days=today.weekday())
    week_end=week_start + timedelta(days=7)

    start=datetime.combine(week_start,
                           datetime.min.time(),
                           tzinfo=UTC,)
    end=datetime.combine(week_end,
                         datetime.min.time(),
                         tzinfo=UTC,)

    statement=select(Task).where(Task.assignee_id==user_id,
                                 Task.due_date>=start,
                                 Task.due_date<end,
                                 Task.status!=TaskStatus.COMPLETED).order_by(Task.due_date.asc())

    return list(db.scalars(statement).all())

def all_tasks_due_this_week(db: Session) -> list[Task]:
    today=datetime.now(UTC).date()
    week_start=today - timedelta(days=today.weekday())
    week_end=week_start + timedelta(days=7)

    start=datetime.combine(week_start,
                           datetime.min.time(),
                           tzinfo=UTC,)
    end=datetime.combine(week_end,
                         datetime.min.time(),
                         tzinfo=UTC,)

    statement=select(Task).where(Task.due_date>=start,
                                 Task.due_date<end,
                                 Task.status!=TaskStatus.COMPLETED).order_by(Task.due_date.asc())

    return list(db.scalars(statement).all())

def managed_tasks_due_this_week(db: Session, current_user: int) -> list[Task]:
    today=datetime.now(UTC).date()
    week_start=today - timedelta(days=today.weekday())
    week_end=week_start + timedelta(days=7)

    start=datetime.combine(week_start, datetime.min.time(), tzinfo=UTC,)
    end=datetime.combine(week_end, datetime.min.time(), tzinfo=UTC,)

    statement=(select(Task)
               .join(Project)
               .join(TeamMember,
                    Project.team_id == TeamMember.team_id,)
               .where(TeamMember.user_id == current_user,
                      TeamMember.role == TeamRole.MANAGER,
                      Task.due_date >= start,
                      Task.due_date < end,
                      )
               )
    return list(db.scalars(statement).all())

def task_exists(db: Session, task_id: int) -> bool:
    return db.get(Task, task_id) is not None

def task_exists_info(db: Session, task_id: int, user_id: int) -> bool:
    statement=select(Task).where(
        Task.id==task_id,
        Task.assignee_id==user_id
    )
    return db.scalar(statement) is not None

def change_priority(db: Session, new_priority: Priority, task_id: int, user_id: int) -> Task | None:
    statement=select(Task).where(
        Task.id==task_id,
        Task.assignee_id==user_id,
    )

    task=db.scalar(statement)

    if task is None:
        return None

    task.priority=new_priority
    db.commit()
    db.refresh(task)

    return task


def search_all_tasks(db: Session, keyword: str) -> list[Task]:
    keyword=keyword.strip()
    statement=select(Task).where(Task.title.ilike(f"%{keyword}%"))
    return list(db.scalars(statement).all())

def search_tasks(db: Session, keyword: str, project_id: int) -> list[Task]:
    keyword=keyword.strip()
    statement=select(Task).where(Task.project_id == project_id, or_(Task.title.ilike(f"%{keyword}%"), Task.description.ilike(f"%{keyword}%"),))
    return list(db.scalars(statement).all())

def list_tasks_for_user(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        status_filter: TaskStatus | None,
        assignee_id: int | None,
        project_id: int | None,
        priority: Priority | None,
        due_before: datetime | None,
        due_after: datetime | None,
        search: str | None,
        sort_by: TaskSortBy,
        sort_order: SortOrder,
) -> list[Task]:
    statement = select(Task)

    #Authorization: decide which projects this user is allowed to see.

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER:
        statement = (
            statement
            .join(Project)
            .join(
                TeamMember,
                Project.team_id == TeamMember.team_id
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.MANAGER,
            )
        )

    elif current_user.role == UserRole.DEVELOPER:
        statement = (
            statement
            .join(Project)
            .join(
                TeamMember,
                Project.team_id == TeamMember.team_id,
            )
            .where(
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamRole.DEVELOPER,
            )
        )

    #filter by exact status.
    if status_filter is not None:
        statement = statement.where(
            Task.status == status_filter
        )

    #filter by exact assignee.
    if assignee_id is not None:
        statement = statement.where(
            Task.assignee_id == assignee_id
        )

    #filter by priority.
    if priority is not None:
        statement = statement.where(
            Task.priority == priority
        )

    #filter by exact project_id.
    if project_id is not None:
        statement = statement.where(
            Task.project_id == project_id
        )

    #filter by exact due_before.
    if due_before is not None:
        statement = statement.where(
            Task.due_date < due_before
        )

    #filter by exact due_after.
    if due_after is not None:
        statement = statement.where(
            Task.due_date > due_after
        )

    #search within task name.
    if search is not None:
        statement = statement.where(
            Task.title.ilike(f"%{search}%")
        )

    #only allow known, safe sort columns.
    sortable_columns={
        TaskSortBy.CREATED_AT : Task.created_at,
        TaskSortBy.UPDATED_AT : Task.updated_at,
        TaskSortBy.DUE_DATE : Task.due_date,
        TaskSortBy.PRIORITY : Task.priority,
        TaskSortBy.STATUS : Task.status,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(asc(sort_column))

    else:
        statement = statement.order_by(desc(sort_column))

    #pagination should happen last.
    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())