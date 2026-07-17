import pytest
from pydantic import ValidationError

from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest


def test_register_and_login_normalize_email_without_accepting_role() -> None:
    register = RegisterRequest(
        username="  zhangsan  ",
        email=" User@Example.COM ",
        password="password-123",
    )
    login = LoginRequest(email=" USER@example.com ", password="password-123")

    assert register.username == "zhangsan"
    assert register.email == "user@example.com"
    assert login.email == "user@example.com"
    assert "role" not in register.model_fields_set


def test_auth_inputs_reject_short_password_and_empty_refresh() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(username="zhangsan", email="a@example.com", password="short")
    with pytest.raises(ValidationError):
        RegisterRequest(username=" ", email="a@example.com", password="password-123")
    with pytest.raises(ValidationError):
        RegisterRequest(username="a", email="a@example.com", password="password-123")
    with pytest.raises(ValidationError):
        RefreshRequest(refresh_token="")
