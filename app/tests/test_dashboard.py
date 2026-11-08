from datetime import UTC, datetime, timedelta

from app.db.models.projects import Project, Status
from app.db.models.task import Priority, Task, TaskStatus
from app.db.models.team import Team
from app.db.models.team_member import TeamMember, TeamRole
from app.db.models.user import User


def _seed_dashboard_data(
    db_session,
    admin_user: User,
    manager_user: User,
    developer_user: User,
) -> dict[str, object]:
    """Create one dashboard scope for each role plus unrelated data."""
    managed_team = Team(name="Managed dashboard team", description="Manager scope")
    developer_team = Team(name="Developer dashboard team", description="Developer scope")
    admin_team = Team(name="Admin dashboard team", description="Admin-only scope")
    db_session.add_all([managed_team, developer_team, admin_team])
    db_session.flush()

    db_session.add_all(
        [
            TeamMember(
                team_id=managed_team.id,
                user_id=manager_user.id,
                role=TeamRole.MANAGER,
            ),
            TeamMember(
                team_id=developer_team.id,
                user_id=developer_user.id,
                role=TeamRole.DEVELOPER,
            ),
        ]
    )

    managed_project = Project(
        name="Managed dashboard project",
        description="Visible to the manager",
        status=Status.ACTIVE,
        team_id=managed_team.id,
        created_by_id=admin_user.id,
    )
    developer_project = Project(
        name="Developer dashboard project",
        description="Visible to the developer",
        status=Status.ACTIVE,
        team_id=developer_team.id,
        created_by_id=admin_user.id,
    )
    admin_project = Project(
        name="Admin dashboard project",
        description="Not visible to non-admin users",
        status=Status.ACTIVE,
        team_id=admin_team.id,
        created_by_id=admin_user.id,
    )
    db_session.add_all([managed_project, developer_project, admin_project])
    db_session.flush()

    now = datetime.now(UTC)
    managed_task = Task(
        title="Managed team task",
        description="Visible to the manager only",
        project_id=managed_project.id,
        created_by_id=admin_user.id,
        assignee_id=manager_user.id,
        status=TaskStatus.TODO,
        priority=Priority.HIGH,
        due_date=now + timedelta(days=1),
    )
    managed_completed_task = Task(
        title="Managed completed task",
        description="Still included in the summary count",
        project_id=managed_project.id,
        created_by_id=admin_user.id,
        status=TaskStatus.COMPLETED,
        priority=Priority.LOW,
        due_date=now + timedelta(days=2),
    )
    developer_team_task = Task(
        title="Developer team task",
        description="Visible because the developer belongs to this team",
        project_id=developer_project.id,
        created_by_id=admin_user.id,
        # Deliberately assigned to someone else. This confirms that the
        # developer dashboard is scoped by team/project membership, not only
        # by direct task assignment.
        assignee_id=admin_user.id,
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.MEDIUM,
        due_date=now + timedelta(days=3),
    )
    developer_completed_task = Task(
        title="Developer completed task",
        description="Visible completed work",
        project_id=developer_project.id,
        created_by_id=admin_user.id,
        status=TaskStatus.COMPLETED,
        priority=Priority.LOW,
        due_date=now + timedelta(days=4),
    )
    admin_task = Task(
        title="Admin-only task",
        description="Must never appear for a manager or developer",
        project_id=admin_project.id,
        created_by_id=admin_user.id,
        status=TaskStatus.TODO,
        priority=Priority.URGENT,
        due_date=now + timedelta(days=5),
    )
    db_session.add_all(
        [
            managed_task,
            managed_completed_task,
            developer_team_task,
            developer_completed_task,
            admin_task,
        ]
    )
    db_session.commit()

    return {
        "managed_project": managed_project,
        "developer_project": developer_project,
        "admin_project": admin_project,
        "managed_task": managed_task,
        "developer_team_task": developer_team_task,
        "admin_task": admin_task,
    }


def test_manager_dashboard_is_limited_to_managed_teams(
    db_session,
    admin_user,
    manager_user,
    developer_user,
    manager_client,
):
    data = _seed_dashboard_data(
        db_session,
        admin_user,
        manager_user,
        developer_user,
    )

    response = manager_client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "manager"
    assert body["visible_team_count"] == 1
    assert body["active_projects"] == 1
    assert body["total_tasks"] == 2
    assert body["todo_tasks"] == 1
    assert body["completed_tasks"] == 1
    assert [project["id"] for project in body["recent_projects"]] == [
        data["managed_project"].id
    ]
    assert [task["id"] for task in body["upcoming_tasks"]] == [
        data["managed_task"].id
    ]


def test_developer_dashboard_is_limited_to_member_team_projects(
    db_session,
    admin_user,
    manager_user,
    developer_user,
    user_client,
):
    data = _seed_dashboard_data(
        db_session,
        admin_user,
        manager_user,
        developer_user,
    )

    response = user_client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "developer"
    assert body["visible_team_count"] == 1
    assert body["active_projects"] == 1
    assert body["total_tasks"] == 2
    assert body["in_progress_tasks"] == 1
    assert body["completed_tasks"] == 1
    assert [project["id"] for project in body["recent_projects"]] == [
        data["developer_project"].id
    ]
    assert [task["id"] for task in body["upcoming_tasks"]] == [
        data["developer_team_task"].id
    ]


def test_admin_dashboard_includes_every_workspace_scope(
    db_session,
    admin_user,
    manager_user,
    developer_user,
    admin_client,
):
    _seed_dashboard_data(
        db_session,
        admin_user,
        manager_user,
        developer_user,
    )

    response = admin_client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "admin"
    assert body["visible_team_count"] == 3
    assert body["active_projects"] == 3
    assert body["total_tasks"] == 5


def test_dashboard_returns_empty_scope_when_user_is_not_on_a_team(
    manager_client,
):
    response = manager_client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["visible_team_count"] == 0
    assert body["active_projects"] == 0
    assert body["total_tasks"] == 0
    assert body["recent_projects"] == []
    assert body["upcoming_tasks"] == []


def test_developer_can_list_only_their_own_teams(
    db_session,
    admin_user,
    manager_user,
    developer_user,
    user_client,
):
    data = _seed_dashboard_data(
        db_session,
        admin_user,
        manager_user,
        developer_user,
    )

    response = user_client.get(f"/teams/users/{developer_user.id}/teams")

    assert response.status_code == 200
    assert [team["id"] for team in response.json()] == [
        data["developer_project"].team_id
    ]


def test_visible_tasks_endpoint_uses_the_same_team_scope_as_the_dashboard(
    db_session,
    admin_user,
    manager_user,
    developer_user,
    auth_client,
):
    data = _seed_dashboard_data(
        db_session,
        admin_user,
        manager_user,
        developer_user,
    )

    with auth_client(manager_user) as manager_client:
        manager_response = manager_client.get("/tasks/visible/?limit=20")

    with auth_client(developer_user) as developer_client:
        developer_response = developer_client.get("/tasks/visible/?limit=20")

    assert manager_response.status_code == 200
    assert developer_response.status_code == 200
    assert {task["project_id"] for task in manager_response.json()} == {
        data["managed_project"].id
    }
    assert {task["project_id"] for task in developer_response.json()} == {
        data["developer_project"].id
    }
