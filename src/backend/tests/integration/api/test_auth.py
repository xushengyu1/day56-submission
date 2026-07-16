import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.usefixtures("auth_database_engine")
def test_register_login_and_refresh_rotate_tokens() -> None:
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": "User@Example.com", "password": "password-123"},
        )
        assert registered.status_code == 201
        body = registered.json()
        assert body["user"] == {
            "email": "user@example.com",
            "role": "USER",
            "id": body["user"]["id"],
        }
        assert "password_hash" not in body

        duplicate = client.post(
            "/api/auth/register",
            json={"email": "user@example.com", "password": "password-123"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"] == "EMAIL_EXISTS"

        logged_in = client.post(
            "/api/auth/login",
            json={"email": "USER@example.com", "password": "password-123"},
        )
        assert logged_in.status_code == 200
        old_refresh = logged_in.json()["refresh_token"]

        refreshed = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refreshed.status_code == 200
        assert refreshed.json()["refresh_token"] != old_refresh

        reused = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert reused.status_code == 401
        assert reused.json()["detail"] == "TOKEN_REVOKED"


@pytest.mark.usefixtures("auth_database_engine")
def test_login_does_not_reveal_whether_email_exists() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "password-123"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_CREDENTIALS"
