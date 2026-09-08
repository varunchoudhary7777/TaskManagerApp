from fastapi.testclient import TestClient

from app.db.models.team_member import TeamRole
from app.db.models.user import User


REGISTER_TEAM = {
    "name": "Backend-Team",
    "description": "This team is responsible for the backend operations.",
}

REGISTER_PROJECT = {
    "name": "Backend-Project",
    "description": "This project is for all the backend-operations",
}

REGISTER_ARCHIVED_PROJECT = {
    "name": "Backend-Project",
    "description": "This project is for all the backend-operations",
    "status": "archived",
}


def create_team(client: TestClient,  team_name: str = "Backend-Team"):
    response = client.post("/teams/", json={"name":team_name, "description":REGISTER_TEAM["description"]})
    assert response.status_code == 201
    return response.json()


def add_member(
    client: TestClient,
    team_id: int,
    user_id: int,
    role: TeamRole,
):
    response = client.post(
        f"/teams/{team_id}/members",
        json={
            "user_id": user_id,
            "role": role.value,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_project(client: TestClient, team_name: str = "Backend-Team"):
    team = create_team(client, team_name)

    response = client.post(
        "/projects/",
        json={
            "name": REGISTER_PROJECT["name"],
            "description": REGISTER_PROJECT["description"],
            "team_id": team["id"],
        },
    )
    assert response.status_code == 201
    return response.json()


def create_archived_project(client: TestClient):
    team = create_team(client)

    response = client.post(
        "/projects/",
        json={
            "name": REGISTER_ARCHIVED_PROJECT["name"],
            "description": REGISTER_ARCHIVED_PROJECT["description"],
            "team_id": team["id"],
            "status": "archived",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_project_with_team_id(client: TestClient, team_id: int, project_name: str):
    response = client.post(
        "/projects/",
        json={
            "name": project_name,
            "description": REGISTER_PROJECT["description"],
            "team_id": team_id,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_update_project(auth_client, admin_user: User):
    with auth_client(admin_user) as admin:
        project = create_project(admin)

        response = admin.put(
            f"/projects/{project['id']}",
            json={
                "name": "new_project",
                "description": "new_one",
                "team_id": project["team_id"],
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == project["id"]
    assert body["name"] == "new_project"
    assert body["description"] == "new_one"
    assert body["team_id"] == project["team_id"]


def test_list_projects(auth_client, admin_user, manager_user, developer_user):
    with auth_client(admin_user) as admin:
        project = create_project(admin)
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.get("/projects/")

    with auth_client(manager_user) as manager:
        manager_response = manager.get("/projects/")

    with auth_client(developer_user) as developer:
        developer_response = developer.get("/projects/")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 200

    for response in [admin_response, manager_response, developer_response]:
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == project["id"]
        assert body[0]["name"] == REGISTER_PROJECT["name"]


def test_search_projects(auth_client, admin_user, manager_user, developer_user):
    with auth_client(admin_user) as admin:
        project = create_project(admin)
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.get("/projects/search/Backend")

    with auth_client(manager_user) as manager:
        manager_response = manager.get("/projects/search/Backend")

    with auth_client(developer_user) as developer:
        developer_response = developer.get("/projects/search/Backend")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 403

    for response in [admin_response, manager_response]:
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == project["id"]
        assert body[0]["name"] == REGISTER_PROJECT["name"]


def test_list_projects_by_status_active(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:
        project = create_project(admin)
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.get("/projects/active_projects")

    with auth_client(manager_user) as manager:
        manager_response = manager.get("/projects/active_projects")

    with auth_client(developer_user) as developer:
        developer_response = developer.get("/projects/active_projects")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 200

    for response in [admin_response, manager_response, developer_response]:
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == project["id"]
        assert body[0]["name"] == REGISTER_PROJECT["name"]
        assert body[0]["status"] == "active"


def test_list_projects_by_status_archived(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:
        project = create_archived_project(admin)
        team_id = project["team_id"]

        create_project_with_team_id(admin, team_id, "Another Backend Project")

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.get("/projects/archived_projects")

    with auth_client(manager_user) as manager:
        manager_response = manager.get("/projects/archived_projects")

    with auth_client(developer_user) as developer:
        developer_response = developer.get("/projects/archived_projects")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 200

    for response in [admin_response, manager_response, developer_response]:
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == project["id"]
        assert body[0]["name"] == REGISTER_ARCHIVED_PROJECT["name"]
        assert body[0]["status"] == "archived"


def test_get_project(auth_client, admin_user, manager_user, developer_user):
    with auth_client(admin_user) as admin:
        project = create_project(admin, )
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.get(f"/projects/{project['id']}")

    with auth_client(manager_user) as manager:
        manager_response = manager.get(f"/projects/{project['id']}")

    with auth_client(developer_user) as developer:
        developer_response = developer.get(f"/projects/{project['id']}")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 200

    for response in [admin_response, manager_response, developer_response]:
        body = response.json()
        assert body["id"] == project["id"]
        assert body["name"] == REGISTER_PROJECT["name"]


def test_get_project_developer_not_part_of_team(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:
        project = create_project(admin)
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)

        admin_response = admin.get(f"/projects/{project['id']}")

    with auth_client(manager_user) as manager:
        manager_response = manager.get(f"/projects/{project['id']}")

    with auth_client(developer_user) as developer:
        developer_response = developer.get(f"/projects/{project['id']}")

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 403


def test_delete_project(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:
        admin_project = create_project(admin, "Admin-Team")

        response = admin.delete(f"/projects/{admin_project['id']}")
        assert response.status_code == 204

        response = admin.get(f"/projects/{admin_project['id']}")
        assert response.status_code == 404

        manager_project = create_project(admin, "Manager-Team")
        add_member(
            admin,
            manager_project["team_id"],
            manager_user.id,
            TeamRole.MANAGER,
        )

        developer_project = create_project(admin, "Developer-Team")
        add_member(
            admin,
            developer_project["team_id"],
            developer_user.id,
            TeamRole.DEVELOPER,
        )

    with auth_client(manager_user) as manager:
        manager_response = manager.delete(
            f"/projects/{manager_project['id']}"
        )

    with auth_client(developer_user) as developer:
        developer_response = developer.delete(
            f"/projects/{developer_project['id']}"
        )

    assert manager_response.status_code == 403
    assert developer_response.status_code == 403


def test_change_status(auth_client, admin_user, manager_user, developer_user):
    with auth_client(admin_user) as admin:
        project = create_project(admin)
        team_id = project["team_id"]

        add_member(admin, team_id, manager_user.id, TeamRole.MANAGER)
        add_member(admin, team_id, developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.put(
            f"/projects/status/{project['id']}",
            json={"status": "planning"},
        )

    with auth_client(manager_user) as manager:
        manager_response = manager.put(
            f"/projects/status/{project['id']}",
            json={"status": "planning"},
        )

    with auth_client(developer_user) as developer:
        developer_response = developer.put(
            f"/projects/status/{project['id']}",
            json={"status": "planning"},
        )

    assert admin_response.status_code == 200
    assert manager_response.status_code == 200
    assert developer_response.status_code == 403

    assert admin_response.json()["status"] == "planning"
    assert manager_response.json()["status"] == "planning"


def test_change_status_project_not_exist(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    project_id = 9999

    with auth_client(admin_user) as admin:
        team = create_team(admin)

        add_member(admin, team["id"], manager_user.id, TeamRole.MANAGER)
        add_member(admin, team["id"], developer_user.id, TeamRole.DEVELOPER)

        admin_response = admin.put(
            f"/projects/status/{project_id}",
            json={"status": "planning"},
        )

    with auth_client(manager_user) as manager:
        manager_response = manager.put(
            f"/projects/status/{project_id}",
            json={"status": "planning"},
        )

    with auth_client(developer_user) as developer:
        developer_response = developer.put(
            f"/projects/status/{project_id}",
            json={"status": "planning"},
        )

    assert admin_response.status_code == 404
    assert manager_response.status_code == 404
    assert developer_response.status_code == 404

def test_list_projects_with_pagination(auth_client, admin_user):
    with auth_client(admin_user) as admin:
        create_project(admin, "Team-one")
        create_project(admin, "Team-two")
        create_project(admin, "Team-three")

        response = admin.get("/projects/?limit=2&skip=0")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_list_projects_filtered_by_status(auth_client, admin_user):
    with auth_client(admin_user) as admin:
        active_project = create_project(admin, "Active-Team")
        archived_project = create_project(admin)

        response = admin.get("/projects/?status=active")

    assert response.status_code == 200

    projects = response.json()
    assert any(project["id"] == active_project["id"] for project in projects)
    assert all(project["status"] == "active"  for project in projects)
    assert all(project["id"] != archived_project["id"] for project in projects)

def test_list_projects_rejects_invalid_limits(auth_client, admin_user):
    with auth_client(admin_user) as admin:
        response = admin.get("/projects/?limit=0")

    assert response.status_code == 422

