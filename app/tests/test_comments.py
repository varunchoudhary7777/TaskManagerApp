from fastapi.testclient import TestClient

from app.db.models.team_member import TeamRole


REGISTER_TEAM = {
    "name": "Comments-Test-Team",
    "description": "Team used for comment testing.",
}

REGISTER_PROJECT = {
    "name": "Comments-Test-Project",
    "description": "Project used for comment testing.",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_team(
    client: TestClient,
    team_name: str = REGISTER_TEAM["name"],
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
    team_name: str = REGISTER_TEAM["name"],
    project_name: str = REGISTER_PROJECT["name"],
):
    team = create_team(client, team_name)

    response = client.post(
        "/projects/",
        json={
            "name": project_name,
            "description": REGISTER_PROJECT["description"],
            "team_id": team["id"],
        },
    )

    assert response.status_code == 201
    project = response.json()

    return project


def create_task(
    client: TestClient,
    project_id: int,
    title: str = "Comments Test Task",
    description: str = "Task used for testing comments.",
    assignee_id: int | None = None,
):
    payload = {
        "title": title,
        "description": description,
        "project_id": project_id,
    }

    if assignee_id is not None:
        payload["assignee_id"] = assignee_id

    response = client.post(
        "/tasks/",
        json=payload,
    )

    assert response.status_code == 201
    return response.json()


def create_comment(
    client: TestClient,
    task_id: int,
    content: str = "This is a test comment.",
):
    response = client.post(
        "/comments/",
        json={
            "content": content,
            "task_id": task_id,
        },
    )

    assert response.status_code == 201
    return response.json()


# ============================================================
# CREATE COMMENT
# ============================================================

def test_create_comment(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Create-Comment-Team",
            project_name="Create-Comment-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Create Comment Task",
            assignee_id=developer_user.id,
        )

        # ----------------------------------------------------
        # Admin
        # ----------------------------------------------------

        admin_response = admin.post(
            "/comments/",
            json={
                "content": "Admin comment",
                "task_id": task["id"],
            },
        )

    # --------------------------------------------------------
    # Manager
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        manager_response = manager.post(
            "/comments/",
            json={
                "content": "Manager comment",
                "task_id": task["id"],
            },
        )

    # --------------------------------------------------------
    # Developer
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        developer_response = developer.post(
            "/comments/",
            json={
                "content": "Developer comment",
                "task_id": task["id"],
            },
        )

    assert admin_response.status_code == 201
    assert manager_response.status_code == 201
    assert developer_response.status_code == 201

    admin_body = admin_response.json()

    assert admin_body["content"] == "Admin comment"
    assert admin_body["task_id"] == task["id"]
    assert admin_body["author_id"] == admin_user.id

    manager_body = manager_response.json()

    assert manager_body["content"] == "Manager comment"
    assert manager_body["task_id"] == task["id"]
    assert manager_body["author_id"] == manager_user.id

    developer_body = developer_response.json()

    assert developer_body["content"] == "Developer comment"
    assert developer_body["task_id"] == task["id"]
    assert developer_body["author_id"] == developer_user.id


# ============================================================
# DEVELOPER CANNOT COMMENT ON A TASK THEY ARE NOT ASSIGNED TO
# ============================================================

def test_developer_cannot_create_comment_on_unassigned_task(
    auth_client,
    admin_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Unassigned-Comment-Team",
            project_name="Unassigned-Comment-Project",
        )

        team_id = project["team_id"]

        add_member(
            admin,
            team_id,
            developer_user.id,
            TeamRole.DEVELOPER,
        )

        # Developer belongs to the team,
        # but is NOT assigned to this task.
        task = create_task(
            admin,
            project["id"],
            title="Unassigned Developer Task",
        )

    with auth_client(developer_user) as developer:

        response = developer.post(
            "/comments/",
            json={
                "content": "I should not be allowed to comment here.",
                "task_id": task["id"],
            },
        )

    assert response.status_code == 403


# ============================================================
# GET COMMENT
# ============================================================

def test_get_comment(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Get-Comment-Team",
            project_name="Get-Comment-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Get Comment Task",
            assignee_id=developer_user.id,
        )

        comment = create_comment(
            admin,
            task["id"],
            "Comment to retrieve",
        )

    # Manager can access comments in managed team
    with auth_client(manager_user) as manager:

        manager_response = manager.get(
            f"/comments/{comment['id']}"
        )

    # Developer can access comments in their team
    with auth_client(developer_user) as developer:

        developer_response = developer.get(
            f"/comments/{comment['id']}"
        )

    # Admin can access everything
    with auth_client(admin_user) as admin:

        admin_response = admin.get(
            f"/comments/{comment['id']}"
        )

    assert manager_response.status_code == 200
    assert developer_response.status_code == 200
    assert admin_response.status_code == 200

    body = manager_response.json()

    assert body["id"] == comment["id"]
    assert body["content"] == "Comment to retrieve"
    assert body["task_id"] == task["id"]


# ============================================================
# GET COMMENTS FOR TASK
# ============================================================

def test_get_task_comments(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Task-Comments-Team",
            project_name="Task-Comments-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Multiple Comments Task",
            assignee_id=developer_user.id,
        )

        comment1 = create_comment(
            admin,
            task["id"],
            "First comment",
        )

        comment2 = create_comment(
            admin,
            task["id"],
            "Second comment",
        )

    with auth_client(manager_user) as manager:

        manager_response = manager.get(
            f"/comments/task/{task['id']}"
        )

    with auth_client(developer_user) as developer:

        developer_response = developer.get(
            f"/comments/task/{task['id']}"
        )

    with auth_client(admin_user) as admin:

        admin_response = admin.get(
            f"/comments/task/{task['id']}"
        )

    assert manager_response.status_code == 200
    assert developer_response.status_code == 200
    assert admin_response.status_code == 200

    for response in [
        manager_response,
        developer_response,
        admin_response,
    ]:
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 2

        returned_ids = {
            item["id"]
            for item in body
        }

        assert returned_ids == {
            comment1["id"],
            comment2["id"],
        }


# ============================================================
# UPDATE COMMENT
# ============================================================

def test_update_comment(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Update-Comment-Team",
            project_name="Update-Comment-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Update Comment Task",
            assignee_id=developer_user.id,
        )

    # --------------------------------------------------------
    # Manager creates own comment
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        manager_comment = create_comment(
            manager,
            task["id"],
            "Original manager comment",
        )

        manager_response = manager.put(
            f"/comments/{manager_comment['id']}",
            json={
                "content": "Updated manager comment",
            },
        )

    assert manager_response.status_code == 200

    manager_body = manager_response.json()

    assert manager_body["id"] == manager_comment["id"]
    assert manager_body["content"] == "Updated manager comment"
    assert manager_body["author_id"] == manager_user.id

    # --------------------------------------------------------
    # Developer cannot update manager's comment
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        developer_response = developer.put(
            f"/comments/{manager_comment['id']}",
            json={
                "content": "Developer trying to modify manager comment",
            },
        )

    assert developer_response.status_code == 403

    # --------------------------------------------------------
    # Admin can update manager's comment
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        admin_response = admin.put(
            f"/comments/{manager_comment['id']}",
            json={
                "content": "Admin updated comment",
            },
        )

    assert admin_response.status_code == 200

    admin_body = admin_response.json()

    assert admin_body["content"] == "Admin updated comment"


# ============================================================
# DELETE COMMENT
# ============================================================

def test_delete_comment(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Delete-Comment-Team",
            project_name="Delete-Comment-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Delete Comment Task",
            assignee_id=developer_user.id,
        )

    # Manager creates their own comment
    with auth_client(manager_user) as manager:

        manager_comment = create_comment(
            manager,
            task["id"],
            "Manager comment to delete",
        )

        delete_response = manager.delete(
            f"/comments/{manager_comment['id']}"
        )

        assert delete_response.status_code == 204

        get_response = manager.get(
            f"/comments/{manager_comment['id']}"
        )

        assert get_response.status_code == 404

    # Developer creates another comment
    with auth_client(developer_user) as developer:

        developer_comment = create_comment(
            developer,
            task["id"],
            "Developer comment",
        )

    # Manager cannot delete developer's comment
    with auth_client(manager_user) as manager:

        manager_response = manager.delete(
            f"/comments/{developer_comment['id']}"
        )

        assert manager_response.status_code == 403

    # Admin can delete it
    with auth_client(admin_user) as admin:

        admin_response = admin.delete(
            f"/comments/{developer_comment['id']}"
        )

        assert admin_response.status_code == 204

        get_response = admin.get(
            f"/comments/{developer_comment['id']}"
        )

        assert get_response.status_code == 404


# ============================================================
# GET USER COMMENTS
# ============================================================

def test_get_user_comments(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="User-Comments-Team",
            project_name="User-Comments-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="User Comments Task",
            assignee_id=developer_user.id,
        )

    with auth_client(manager_user) as manager:

        manager_comment1 = create_comment(
            manager,
            task["id"],
            "Manager comment one",
        )

        manager_comment2 = create_comment(
            manager,
            task["id"],
            "Manager comment two",
        )

        response = manager.get(
            "/comments/user_comments"
        )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)
    assert len(body) == 2

    returned_ids = {
        item["id"]
        for item in body
    }

    assert returned_ids == {
        manager_comment1["id"],
        manager_comment2["id"],
    }


# ============================================================
# SEARCH COMMENTS
# ============================================================

def test_search_comments(
    auth_client,
    admin_user,
    manager_user,
    developer_user,
):
    with auth_client(admin_user) as admin:

        project = create_project(
            admin,
            team_name="Search-Comments-Team",
            project_name="Search-Comments-Project",
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

        task = create_task(
            admin,
            project["id"],
            title="Search Comments Task",
            assignee_id=developer_user.id,
        )

    # Manager creates a searchable comment
    with auth_client(manager_user) as manager:

        manager_comment = create_comment(
            manager,
            task["id"],
            "manager backend architecture discussion",
        )

    # Developer creates a searchable comment
    with auth_client(developer_user) as developer:

        developer_comment = create_comment(
            developer,
            task["id"],
            "developer backend implementation discussion",
        )

    # --------------------------------------------------------
    # Manager search
    # --------------------------------------------------------

    with auth_client(manager_user) as manager:

        response = manager.get(
            "/comments/search",
            params={
                "keyword": "backend",
            },
        )

    assert response.status_code == 200

    manager_body = response.json()

    assert isinstance(manager_body, list)

    manager_ids = {
        item["id"]
        for item in manager_body
    }

    assert manager_comment["id"] in manager_ids
    assert developer_comment["id"] in manager_ids

    # --------------------------------------------------------
    # Developer search
    # --------------------------------------------------------

    with auth_client(developer_user) as developer:

        response = developer.get(
            "/comments/search",
            params={
                "keyword": "backend",
            },
        )

    assert response.status_code == 200

    developer_body = response.json()

    assert isinstance(developer_body, list)

    developer_ids = {
        item["id"]
        for item in developer_body
    }

    assert manager_comment["id"] in developer_ids
    assert developer_comment["id"] in developer_ids

    # --------------------------------------------------------
    # Admin search
    # --------------------------------------------------------

    with auth_client(admin_user) as admin:

        response = admin.get(
            "/comments/search",
            params={
                "keyword": "backend",
            },
        )

    assert response.status_code == 200

    admin_body = response.json()

    assert isinstance(admin_body, list)

    admin_ids = {
        item["id"]
        for item in admin_body
    }

    assert manager_comment["id"] in admin_ids
    assert developer_comment["id"] in admin_ids