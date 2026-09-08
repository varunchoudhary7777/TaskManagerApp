from fastapi.testclient import TestClient

from datetime import datetime, timedelta, timezone

from app.core.security import hash_refresh_token
from app.repositories import refresh_token_repository

REGISTER_DATA={
    "email": "varun@example.com",
    "full_name": "Varun Choudhary",
    "password": "strongpassword123",
}

def register_user(client: TestClient):
    response=client.post(
        "/auth/register",
        json=REGISTER_DATA,
    )
    assert response.status_code==201
    return response.json()

def login_user(client: TestClient):
    response=client.post(
        "/auth/login",
        json={
            "email": REGISTER_DATA["email"],
            "password": REGISTER_DATA["password"],
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]

def test_register_creates_developer_user(client: TestClient):
    response=client.post(
        "/auth/register",
        json=REGISTER_DATA,
    )
    assert response.status_code == 201
    body=response.json()

    assert body["email"] == "varun@example.com"
    assert body["full_name"] == "Varun Choudhary"
    assert body["role"] == "developer"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body

def test_register_rejects_duplicate_email(client: TestClient):
    register_user(client)
    response=client.post(
        "/auth/register",
        json=REGISTER_DATA,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An account with this email already exists."
    )

def test_login_returns_access_and_refresh_token(
    client: TestClient,
):
    register_user(client)

    token_pair = login_token_pair(client)

    assert "access_token" in token_pair
    assert "refresh_token" in token_pair
    assert token_pair["token_type"] == "bearer"

    assert token_pair["access_token"]
    assert token_pair["refresh_token"]

def test_login_rejects_wrong_password(client: TestClient):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_DATA["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401

def test_me_requires_token(client: TestClient):
    response=client.get("/auth/me")
    assert response.status_code == 401

def test_me_return_current_user(client: TestClient):
    register_user(client)

    access_token = login_user(client)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "varun@example.com"
    assert body["role"] == "developer"

def login_token_pair(client: TestClient) -> dict:
    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_DATA["email"],
            "password": REGISTER_DATA["password"],
        },
    )

    assert response.status_code == 200

    return response.json()

def test_refresh_returns_new_token_pair(
    client: TestClient,
):
    register_user(client)

    original_pair = login_token_pair(client)

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": original_pair["refresh_token"],
        },
    )

    assert response.status_code == 200

    new_pair = response.json()

    assert "access_token" in new_pair
    assert "refresh_token" in new_pair
    assert new_pair["token_type"] == "bearer"

    # Refresh-token rotation means a new refresh token is created.
    assert (
        new_pair["refresh_token"]
        != original_pair["refresh_token"]
    )

def test_old_refresh_token_cannot_be_reused_after_rotation(
    client: TestClient,
):
    register_user(client)

    original_pair = login_token_pair(client)
    old_refresh_token = original_pair["refresh_token"]

    first_refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert first_refresh_response.status_code == 200

    # The old token was revoked during refresh-token rotation.
    second_refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert second_refresh_response.status_code == 401

def test_logged_out_refresh_token_returns_401(
    client: TestClient,
):
    register_user(client)

    token_pair = login_token_pair(client)
    refresh_token = token_pair["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 401

def test_expired_refresh_token_returns_401(
    client: TestClient,
    db_session,
):
    register_user(client)

    token_pair = login_token_pair(client)
    refresh_token = token_pair["refresh_token"]

    stored_token = refresh_token_repository.get_by_token_hash(
        db_session,
        hash_refresh_token(refresh_token),
    )

    assert stored_token is not None

    # Pretend this token expired one minute ago.
    stored_token.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )

    db_session.commit()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
