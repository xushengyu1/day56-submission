import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.usefixtures("auth_database_engine")
def test_register_login_and_refresh_rotate_tokens() -> None:
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "username": "zhangsan",
                "email": "User@Example.com",
                "password": "password-123",
            },
        )
        assert registered.status_code == 201
        body = registered.json()
        assert set(body) == {"user", "tokens"}
        assert body["user"] == {
            "username": "zhangsan",
            "email": "user@example.com",
            "role": "USER",
            "id": body["user"]["id"],
            "created_at": body["user"]["created_at"],
        }
        assert set(body["tokens"]) == {"access_token", "refresh_token", "token_type"}
        assert "password_hash" not in body

        duplicate = client.post(
            "/api/auth/register",
            json={
                "username": "another-name",
                "email": "user@example.com",
                "password": "password-123",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json() == {
            "error_code": "EMAIL_EXISTS",
            "message": "该邮箱已注册",
        }

        logged_in = client.post(
            "/api/auth/login",
            json={"email": "USER@example.com", "password": "password-123"},
        )
        assert logged_in.status_code == 200
        assert set(logged_in.json()) == {"user", "tokens"}
        assert logged_in.json()["user"] == body["user"]
        old_refresh = logged_in.json()["tokens"]["refresh_token"]

        refreshed = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refreshed.status_code == 200
        assert set(refreshed.json()) == {"user", "tokens"}
        assert refreshed.json()["tokens"]["refresh_token"] != old_refresh

        reused = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert reused.status_code == 401
        assert reused.json() == {
            "error_code": "TOKEN_REVOKED",
            "message": "登录状态已失效，请重新登录",
        }

        me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {body['tokens']['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json() == body["user"]

        unauthenticated_me = client.get("/api/auth/me")
        assert unauthenticated_me.status_code == 401
        assert unauthenticated_me.json()["error_code"] == "UNAUTHENTICATED"


@pytest.mark.usefixtures("auth_database_engine")
def test_login_does_not_reveal_whether_email_exists() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "password-123"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "error_code": "INVALID_CREDENTIALS",
        "message": "邮箱或密码错误",
    }
