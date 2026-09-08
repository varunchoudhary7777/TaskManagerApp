from fastapi.testclient import TestClient

from app.db.models.team_member import TeamRole


REGISTER_TEAM = {
    "name": "Backend-Team",
    "description": "This team is responsible for the backend operations.",
}

REGISTER_PROJECT = {
    "name": "Backend-Project",
    "description": "This project is for all the backend-operations.",
}

REGISTER_TASK = {
    "title": "make the backend apis",
    "description": "Use fastapi to make the backend apis for the given project.",
}


# ============================================================
# Helper functions
# ============================================================

def create_team(
    client: TestClient,
    team_name: str = "Backend-Team",
):
    response = client.post(
        "/teams/",
        json={
            "name": team_name,
            "description": REGISTER_TEAM["description"],
        },
    )

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


def create_project(
    client: TestClient,
    team_name: str = "Backend-Team",
    project_name: str = REGISTER_PROJECT["name"],
):
    team = create_team(
        client,
        team_name,
    )

    response = client.post(
        "/projects/",
        json={
            "name": project_name,
            "description": REGISTER_PROJECT["description"],
            "team_id": team["id"],
        },
    )

    assert response.status_code == 201

    return response.json()


def create_task(
    client: TestClient,
    task_title: str = "full_stack",
    task_description: str = "This is a full stack application task.",
    project_name: str = "manager_project",
):
    project = create_project(
        client,
        project_name=project_name,
    )

    response = client.post(
        "/tasks/",
        json={
            "title": task_title,
            "description": task_description,
            "project_id": project["id"],
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# CREATE TASK
# ============================================================

def test_create_task(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Create-Task-Team",
            project_name="Create-Task-Project",
        )

        team_id = project["team_id"]

        add_member(
            admin,
            team_id,
            manager_user.id,
            TeamRole.MANAGER,
        )

        add_member(
            admin,
            team_id,
            developer_user.id,
            TeamRole.DEVELOPER,
        )

        # ----------------------------------------------------
        # Admin creates task
        # ----------------------------------------------------

        admin_response = admin.post(
            "/tasks/",
            json={
                "title": REGISTER_TASK["title"],
                "description": REGISTER_TASK["description"],
                "project_id": project["id"],
                "assignee_id": developer_user.id,
            },
        )

    # --------------------------------------------------------
    # Manager creates task
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        manager_response = manager.post(
            "/tasks/",
            json={
                "title": "front-end task",
                "description": "make the front-end for the project.",
                "project_id": project["id"],
                "assignee_id": developer_user.id,
            },
        )

    # --------------------------------------------------------
    # Developer attempts to create task
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        developer_response = developer.post(
            "/tasks/",
            json={
                "title": "developer task",
                "description": "developer should not create this task.",
                "project_id": project["id"],
                "assignee_id": developer_user.id,
            },
        )

    assert admin_response.status_code == 201
    assert manager_response.status_code == 201
    assert developer_response.status_code == 403

    # --------------------------------------------------------
    # Validate admin task response
    # --------------------------------------------------------

    admin_body = admin_response.json()

    assert admin_body["title"] == REGISTER_TASK["title"]
    assert admin_body["project_id"] == project["id"]
    assert admin_body["description"] == REGISTER_TASK["description"]
    assert admin_body["assignee_id"] == developer_user.id

    # --------------------------------------------------------
    # Validate manager task response
    # --------------------------------------------------------

    manager_body = manager_response.json()

    assert manager_body["title"] == "front-end task"
    assert manager_body["project_id"] == project["id"]
    assert manager_body["description"] == "make the front-end for the project."
    assert manager_body["assignee_id"] == developer_user.id


# ============================================================
# UPDATE TASK
# ============================================================

def test_update_task(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        # ----------------------------------------------------
        # Admin-owned project/task
        # ----------------------------------------------------

        admin_project = create_project(
            admin,
            team_name="Admin-Update-Team",
            project_name="Admin-Update-Project",
        )

        admin_task_response = admin.post(
            "/tasks/",
            json={
                "title": "admin task",
                "description": "admin task description",
                "project_id": admin_project["id"],
            },
        )

        assert admin_task_response.status_code == 201

        admin_task = admin_task_response.json()

        # ----------------------------------------------------
        # Manager-managed team/project/task
        # ----------------------------------------------------

        manager_project = create_project(
            admin,
            team_name="Manager-Update-Team",
            project_name="Manager-Update-Project",
        )

        add_member(
            admin,
            manager_project["team_id"],
            manager_user.id,
            TeamRole.MANAGER,
        )

        manager_task_response = admin.post(
            "/tasks/",
            json={
                "title": "manager task",
                "description": "manager task description",
                "project_id": manager_project["id"],
            },
        )

        assert manager_task_response.status_code == 201

        manager_task = manager_task_response.json()

        # ----------------------------------------------------
        # Developer project/task
        #
        # Developer is deliberately NOT added to the team.
        # Therefore developer should not be authorized to
        # update this task.
        # ----------------------------------------------------

        developer_project = create_project(
            admin,
            team_name="Developer-Update-Team",
            project_name="Developer-Update-Project",
        )

        developer_task_response = admin.post(
            "/tasks/",
            json={
                "title": "developer task",
                "description": "developer task description",
                "project_id": developer_project["id"],
            },
        )

        assert developer_task_response.status_code == 201

        developer_task = developer_task_response.json()

    # --------------------------------------------------------
    # Admin updates task
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.put(
            f"/tasks/update/{admin_task['project_id']}/{admin_task['id']}",
            json={
                "title": "admin updated task",
                "description": "admin updated description",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == admin_task["id"]
        assert body["title"] == "admin updated task"
        assert body["description"] == "admin updated description"
        assert body["project_id"] == admin_task["project_id"]

    # --------------------------------------------------------
    # Manager updates task belonging to managed team
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.put(
            f"/tasks/update/{manager_task['project_id']}/{manager_task['id']}",
            json={
                "title": "manager updated task",
                "description": "manager updated description",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == manager_task["id"]
        assert body["title"] == "manager updated task"
        assert body["description"] == "manager updated description"
        assert body["project_id"] == manager_task["project_id"]

    # --------------------------------------------------------
    # Developer attempts to update task
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.put(
            f"/tasks/update/{developer_task['project_id']}/{developer_task['id']}",
            json={
                "title": "developer updated task",
                "description": "developer updated description",
            },
        )

        assert response.status_code == 403


# ============================================================
# DELETE TASK
# ============================================================

def test_delete_task(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        # ----------------------------------------------------
        # Admin task
        # ----------------------------------------------------

        admin_task = create_task(
            admin,
            "admin delete task",
            "task created for admin deletion",
            "Admin-Delete-Project",
        )

        # ----------------------------------------------------
        # Manager task
        # ----------------------------------------------------

        manager_project = create_project(
            admin,
            team_name="Manager-Delete-Team",
            project_name="Manager-Delete-Project",
        )

        add_member(
            admin,
            manager_project["team_id"],
            manager_user.id,
            TeamRole.MANAGER,
        )

        manager_task_response = admin.post(
            "/tasks/",
            json={
                "title": "manager delete task",
                "description": "task created for manager deletion",
                "project_id": manager_project["id"],
            },
        )

        assert manager_task_response.status_code == 201

        manager_task = manager_task_response.json()

        # ----------------------------------------------------
        # Developer task
        #
        # Developer is not given team membership.
        # ----------------------------------------------------

        developer_project = create_project(
            admin,
            team_name="Developer-Delete-Team",
            project_name="Developer-Delete-Project",
        )

        developer_task_response = admin.post(
            "/tasks/",
            json={
                "title": "developer delete task",
                "description": "task created for developer access test",
                "project_id": developer_project["id"],
            },
        )

        assert developer_task_response.status_code == 201

        developer_task = developer_task_response.json()

    # --------------------------------------------------------
    # Admin deletes task
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.delete(
            f"/tasks/{admin_task['project_id']}/{admin_task['id']}"
        )

        assert response.status_code == 200

        # Verify deletion
        response = admin.get(
            f"/tasks/{admin_task['id']}"
        )

        assert response.status_code == 404

    # --------------------------------------------------------
    # Manager deletes task belonging to managed team
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.delete(
            f"/tasks/{manager_task['project_id']}/{manager_task['id']}"
        )

        assert response.status_code == 200

        # Verify deletion
        response = manager.get(
            f"/tasks/{manager_task['id']}"
        )

        assert response.status_code == 404

    # --------------------------------------------------------
    # Developer attempts to delete task
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.delete(
            f"/tasks/{developer_task['project_id']}/{developer_task['id']}"
        )

        assert response.status_code == 403

        # Task must still exist
        response = developer.get(
            f"/tasks/{developer_task['id']}"
        )

        # Developer is not a member of the team, so they cannot
        # access the task either.
        assert response.status_code == 403


# ============================================================
# LIST ALL TASKS
# ============================================================

def test_list_tasks(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        task = create_task(
            admin,
            "admin task",
            "admin task description",
            "Admin-List-Project",
        )

        manager_task = create_task(
            admin,
            "manager task",
            "manager task description",
            "Manager-List-Project",
        )

        developer_task = create_task(
            admin,
            "developer task",
            "developer task description",
            "Developer-List-Project",
        )

    # --------------------------------------------------------
    # Manager cannot list ALL tasks
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.get("/tasks/")

        assert response.status_code == 403

    # --------------------------------------------------------
    # Developer cannot list ALL tasks
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.get("/tasks/")

        assert response.status_code == 403

    # --------------------------------------------------------
    # Admin can list ALL tasks
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.get("/tasks/")

        assert response.status_code == 200

        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 3

        returned_ids = {
            item["id"]
            for item in body
        }

        assert returned_ids == {
            task["id"],
            manager_task["id"],
            developer_task["id"],
        }


# ============================================================
# SEARCH ALL TASKS
# ============================================================

def test_search_all_tasks(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        admin_task = create_task(
            admin,
            "admin backend task",
            "admin task description",
            "Admin-Search-Project",
        )

        manager_task = create_task(
            admin,
            "manager backend task",
            "manager task description",
            "Manager-Search-Project",
        )

        developer_task = create_task(
            admin,
            "developer backend task",
            "developer task description",
            "Developer-Search-Project",
        )

    # --------------------------------------------------------
    # Manager attempts global search
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.get(
            "/tasks/search/backend"
        )

        assert response.status_code == 403

    # --------------------------------------------------------
    # Developer attempts global search
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.get(
            "/tasks/search/backend"
        )

        assert response.status_code == 403

    # --------------------------------------------------------
    # Admin performs global search
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.get(
            "/tasks/search/backend"
        )

        assert response.status_code == 200

        body = response.json()

        assert isinstance(body, list)

        returned_ids = {
            item["id"]
            for item in body
        }

        assert admin_task["id"] in returned_ids

# ============================================================
# SEARCH TASKS WITHIN A PROJECT
# ============================================================

def test_search_tasks(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Search-Team",
            project_name="Search-Project",
        )

        team_id = project["team_id"]

        # Manager manages this team
        add_member(
            admin,
            team_id,
            manager_user.id,
            TeamRole.MANAGER,
        )

        # Developer belongs to this team
        add_member(
            admin,
            team_id,
            developer_user.id,
            TeamRole.DEVELOPER,
        )

        manager_task_response = admin.post(
            "/tasks/",
            json={
                "title": "manager backend task",
                "description": "task created by manager workflow",
                "project_id": project["id"],
            },
        )

        assert manager_task_response.status_code == 201

        manager_task = manager_task_response.json()

        developer_task_response = admin.post(
            "/tasks/",
            json={
                "title": "developer backend task",
                "description": "task created for developer workflow",
                "project_id": project["id"],
            },
        )

        assert developer_task_response.status_code == 201

        developer_task = developer_task_response.json()

    # --------------------------------------------------------
    # Manager can search tasks in managed team
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.get(
            f"/tasks/search_all/manager/{manager_task['project_id']}"
        )

        # NOTE:
        # search_all is admin-only, so this MUST be 403.
        assert response.status_code == 403

        # Correct manager endpoint:
        response = manager.get(
            f"/tasks/search_all/manager/{manager_task['project_id']}"
        )

        assert response.status_code == 403

        body = response.json()

        returned_ids = {
            item["id"]
            for item in body
        }

        assert manager_task["id"] in returned_ids

    # --------------------------------------------------------
    # Developer can search tasks in their team
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.get(
            f"/tasks/search_all/developer/{project['id']}"
        )

        assert response.status_code == 403

        body = response.json()

        returned_ids = {
            item["id"]
            for item in body
        }

        assert developer_task["id"] in returned_ids

    # --------------------------------------------------------
    # Admin can search tasks in project
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.get(
            f"/tasks/search_all/backend/{project['id']}"
        )

        assert response.status_code == 200

        body = response.json()

        returned_ids = {
            item["id"]
            for item in body
        }

        assert manager_task["id"] in returned_ids
        assert developer_task["id"] in returned_ids


# ============================================================
# GET TASK BY ID
# ============================================================

def test_get_task(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        # ----------------------------------------------------
        # Admin-only project
        # ----------------------------------------------------

        admin_project = create_project(
            admin,
            team_name="Admin-Get-Team",
            project_name="Admin-Get-Project",
        )

        admin_task_response = admin.post(
            "/tasks/",
            json={
                "title": "admin task",
                "description": "admin task description",
                "project_id": admin_project["id"],
            },
        )

        assert admin_task_response.status_code == 201

        admin_task = admin_task_response.json()

        # ----------------------------------------------------
        # Shared manager/developer team
        # ----------------------------------------------------

        shared_project = create_project(
            admin,
            team_name="Shared-Get-Team",
            project_name="Shared-Get-Project",
        )

        team_id = shared_project["team_id"]

        add_member(
            admin,
            team_id,
            manager_user.id,
            TeamRole.MANAGER,
        )

        add_member(
            admin,
            team_id,
            developer_user.id,
            TeamRole.DEVELOPER,
        )

        manager_task_response = admin.post(
            "/tasks/",
            json={
                "title": "manager task",
                "description": "manager task description",
                "project_id": shared_project["id"],
            },
        )

        assert manager_task_response.status_code == 201

        manager_task = manager_task_response.json()

        developer_task_response = admin.post(
            "/tasks/",
            json={
                "title": "developer task",
                "description": "developer task description",
                "project_id": shared_project["id"],
            },
        )

        assert developer_task_response.status_code == 201

        developer_task = developer_task_response.json()

    # ========================================================
    # Manager
    # ========================================================

    with auth_client(manager_user) as manager:

        # Manager can access task in managed team
        response = manager.get(
            f"/tasks/{manager_task['id']}"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == manager_task["id"]
        assert body["title"] == manager_task["title"]
        assert body["project_id"] == manager_task["project_id"]

        # Manager can also access developer's task because
        # both tasks belong to the team managed by the manager.
        response = manager.get(
            f"/tasks/{developer_task['id']}"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == developer_task["id"]
        assert body["title"] == developer_task["title"]
        assert body["project_id"] == developer_task["project_id"]

        # Manager cannot access admin-only team's task
        response = manager.get(
            f"/tasks/{admin_task['id']}"
        )

        assert response.status_code == 403

    # ========================================================
    # Developer
    # ========================================================

    with auth_client(developer_user) as developer:

        # Developer can access task in their team
        response = developer.get(
            f"/tasks/{developer_task['id']}"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == developer_task["id"]
        assert body["title"] == developer_task["title"]
        assert body["project_id"] == developer_task["project_id"]

        # IMPORTANT:
        # The service checks TEAM MEMBERSHIP, not task assignment.
        # Therefore developer can also access manager_task because
        # both tasks belong to the same team.
        response = developer.get(
            f"/tasks/{manager_task['id']}"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == manager_task["id"]
        assert body["title"] == manager_task["title"]
        assert body["project_id"] == manager_task["project_id"]

        # Developer is not part of admin's team
        response = developer.get(
            f"/tasks/{admin_task['id']}"
        )

        assert response.status_code == 403

    # ========================================================
    # Admin
    # ========================================================

    with auth_client(admin_user) as admin:

        for task in [
            admin_task,
            manager_task,
            developer_task,
        ]:
            response = admin.get(
                f"/tasks/{task['id']}"
            )

            assert response.status_code == 200

            body = response.json()

            assert body["id"] == task["id"]
            assert body["title"] == task["title"]
            assert body["project_id"] == task["project_id"]