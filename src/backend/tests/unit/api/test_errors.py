import pytest

from app.api.errors import APIError, api_error_for
from app.auth.rbac import AuthorizationError
from app.auth.security import AuthenticationError
from app.items.service import DomainError


@pytest.mark.parametrize(
    ("exception", "error_code", "status_code", "message"),
    [
        (
            AuthenticationError("INVALID_CREDENTIALS"),
            "INVALID_CREDENTIALS",
            401,
            "邮箱或密码错误",
        ),
        (AuthorizationError(), "FORBIDDEN", 403, "无权执行此操作"),
        (DomainError("NOT_OWNER"), "NOT_OWNER", 403, "无权执行此操作"),
        (DomainError("NOT_FOUND"), "NOT_FOUND", 404, "资源不存在"),
        (
            DomainError("VERSION_CONFLICT"),
            "VERSION_CONFLICT",
            409,
            "记录已被更新，请重新加载",
        ),
        (
            DomainError("ATTEMPT_LOCKED"),
            "ATTEMPT_LOCKED",
            423,
            "尝试次数已用尽，请联系管理员",
        ),
    ],
)
def test_exception_mapping_is_closed_and_stable(
    exception, error_code, status_code, message
) -> None:
    error = api_error_for(exception)

    assert error.error_code == error_code
    assert error.status_code == status_code
    assert error.message == message


def test_api_error_carries_validation_fields_without_detail_wrapper() -> None:
    error = APIError(
        "VALIDATION_ERROR",
        field_errors={"email": "Value error, email must be valid"},
    )

    assert error.status_code == 422
    assert error.as_dict() == {
        "error_code": "VALIDATION_ERROR",
        "message": "请求参数不正确",
        "field_errors": {"email": "Value error, email must be valid"},
    }
