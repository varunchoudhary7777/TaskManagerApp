from fastapi.testclient import TestClient

from app.db.models.team_member import TeamRole
from app.db.models.user import UserRole
from app.tests.test_auth import register_user

REGISTER_TEAM={
    "name":"Backend-Team",
    "description":"This team is responsible for the backend operations.",
}

REGISTER_DATA={
    "email": "varun@example.com",
    "full_name": "Varun Choudhary",
    "password": "strongpassword123",
}

def create_team(admin_client: TestClient):
    response=admin_client.post("/teams/", json=REGISTER_TEAM)
    assert response.status_code==201
    return response.json()

def add_member(admin_client: TestClient, client: TestClient):
    team=create_team(admin_client)
    team_id=team["id"]
    user=register_user(client)
    userid=user["id"]
    response=admin_client.post(
        f"/teams/{team_id}/members",
        json={
            "user_id": userid,
            "role": TeamRole.DEVELOPER.value,
        }
    )
    assert response.status_code==201
    return response.json()

def get_team_members(admin_client: TestClient, team_id: int):
    response=admin_client.get(f"/teams/{team_id}/members")
    assert response.status_code==200
    return response.json()


def test_get_teams(admin_client: TestClient):
    create_team(admin_client)
    response=admin_client.get("/teams/")
    assert response.status_code==200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == REGISTER_TEAM["name"]
    assert body[0]["description"] == REGISTER_TEAM["description"]

def test_get_team(admin_client: TestClient):
    team=create_team(admin_client)
    team_id=team["id"]
    response=admin_client.get(f"/teams/{team_id}")
    assert response.status_code==200
    body=response.json()
    assert body["name"]==REGISTER_TEAM["name"]
    assert body["description"]==REGISTER_TEAM["description"]
    assert body["id"]==team_id

def test_update_team(admin_client: TestClient):
    team=create_team(admin_client)
    team_id=team["id"]
    response=admin_client.put(
        f"/teams/{team_id}",
        json={
            "name":"Backend-Team",
            "description":"This is the second backend-team",
        }
    )
    assert response.status_code==200
    body=response.json()
    assert body["id"]==team_id
    assert body["name"]=="Backend-Team"
    assert body["description"]=="This is the second backend-team"

def test_delete_team(admin_client: TestClient):
    team=create_team(admin_client)
    team_id=team["id"]
    response=admin_client.delete(f"/teams/{team_id}")
    assert response.status_code==204

def test_add_member(admin_client: TestClient, client: TestClient):
    team=create_team(admin_client)
    team_id=team["id"]
    user=register_user(client)
    user_id=user["id"]
    response=admin_client.post(
        f"/teams/{team_id}/members",
        json={
            "user_id":user_id
        }
    )
    assert response.status_code==201
    body=response.json()
    assert body["user_id"]==user_id
    assert body["team_id"]==team_id

def test_get_team_members(admin_client: TestClient, client: TestClient):
    team_member=add_member(admin_client, client)
    user_id=team_member["user_id"]
    team_id=team_member["team_id"]
    response=admin_client.get(f"/teams/{team_id}/members")
    assert response.status_code==200
    body=response.json()
    assert len(body)==1
    assert body[0]["id"]==user_id
    assert body[0]["full_name"]==REGISTER_DATA["full_name"]
    assert body[0]["email"]==REGISTER_DATA["email"]

def test_remove_member(admin_client: TestClient, client: TestClient):
    team_member=add_member(admin_client, client)
    user_id=team_member["user_id"]
    team_id=team_member["team_id"]
    response=admin_client.delete(f"/teams/{team_id}/members/{user_id}")
    assert response.status_code==204
    team_member_response=get_team_members(admin_client, team_id)
    assert all(
        member["user_id"] != user_id
        for member in team_member_response
    )

def test_get_user_teams(admin_client: TestClient, client: TestClient):
    team_member=add_member(admin_client,client)
    print(team_member)

    user_id=team_member["user_id"]
    team_id=team_member["team_id"]
    response=admin_client.get(f"/teams/users/{user_id}/teams")
    assert response.status_code==200
    body=response.json()
    assert len(body)==1
    assert body[0]["id"]==team_id


#def test_user_cannot_get_other_users_teams(
#        admin_client: TestClient,
#        client: TestClient,
#        user_client: TestClient,
#):
#    other_user=register_user(client)
#    other_user_id=other_user["id"]
#
#    team=create_team(admin_client)
#    response=admin_client.post(
#        f"/teams/{team['id']}/members",
#        json={
#            "user_id": other_user_id,
#        }
#    )
#    assert response.status_code==200
#    response=user_client.get(f"/teams/users/{other_user_id}/teams")
#
#    assert response.status_code==403


def test_user_cannot_get_other_users_teams(
        auth_client,
        developer_user,
        admin_user,
        client,
):
    other_user = register_user(client)

    # authenticate as admin
    with auth_client(admin_user) as admin_client:
        team = create_team(admin_client)

        response = admin_client.post(
            f"/teams/{team['id']}/members",
            json={
                "user_id": other_user["id"]
            }
        )

        assert response.status_code == 201

    # authenticate as developer
    with auth_client(developer_user) as user_client:
        response = user_client.get(
            f"/teams/users/{other_user['id']}/teams"
        )

    assert response.status_code == 403

