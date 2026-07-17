from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler
from typing import cast

from app.api.schemas import ErrorResponse
from app.auth.rbac import AuthorizationError
from app.auth.security import AuthenticationError
from app.auth.service import AuthServiceError
from app.items.service import DomainError


_ERROR_SPECS: dict[str, tuple[int, str]] = {
    "UNAUTHENTICATED": (401, "请先登录"),
    "INVALID_TOKEN": (401, "登录状态无效，请重新登录"),
    "INVALID_CREDENTIALS": (401, "邮箱或密码错误"),
    "TOKEN_REVOKED": (401, "登录状态已失效，请重新登录"),
    "FORBIDDEN": (403, "无权执行此操作"),
    "NOT_OWNER": (403, "无权执行此操作"),
    "NOT_FINDER": (403, "无权执行此操作"),
    "NOT_FOUND": (404, "资源不存在"),
    "EMAIL_EXISTS": (409, "该邮箱已注册"),
    "VERSION_CONFLICT": (409, "记录已被更新，请重新加载"),
    "ACTIVE_REVIEW_EXISTS": (409, "已存在待处理的复核申请"),
    "VALIDATION_ERROR": (422, "请求参数不正确"),
    "ATTEMPT_LOCKED": (423, "尝试次数已用尽，请联系管理员"),
}


class APIError(ValueError):
    def __init__(
        self,
        error_code: str,
        *,
        status_code: int | None = None,
        message: str | None = None,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        if not error_code:
            raise ValueError("error code must not be empty")
        mapped_status, mapped_message = _ERROR_SPECS.get(
            error_code, (400, "请求无法处理")
        )
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code or mapped_status
        self.message = message or mapped_message
        self.field_errors = field_errors

    @property
    def code(self) -> str:
        return self.error_code

    def as_dict(self) -> dict[str, object]:
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            field_errors=self.field_errors,
        ).model_dump(exclude_none=True)


def api_error_for(error: Exception) -> APIError:
    code = getattr(error, "code", "REQUEST_FAILED")
    return APIError(str(code))


async def api_error_handler(_request: Request, error: APIError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=error.as_dict())


async def mapped_error_handler(_request: Request, error: Exception) -> JSONResponse:
    mapped = api_error_for(error)
    return JSONResponse(status_code=mapped.status_code, content=mapped.as_dict())


async def validation_error_handler(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    field_errors: dict[str, str] = {}
    for item in error.errors():
        location = item.get("loc", ())
        field = str(location[-1]) if location else "request"
        field_errors.setdefault(field, str(item.get("msg", "Invalid value")))
    mapped = APIError("VALIDATION_ERROR", field_errors=field_errors)
    return JSONResponse(status_code=mapped.status_code, content=mapped.as_dict())


async def http_error_handler(
    _request: Request, error: StarletteHTTPException
) -> JSONResponse:
    detail = error.detail
    if isinstance(detail, str) and detail.replace("_", "").isalnum():
        code = detail
    else:
        code = {
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
        }.get(error.status_code, "REQUEST_FAILED")
    mapped = APIError(code, status_code=error.status_code)
    return JSONResponse(status_code=mapped.status_code, content=mapped.as_dict())


def register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(
        APIError, cast(ExceptionHandler, api_error_handler)
    )
    for exception_type in (
        AuthenticationError,
        AuthorizationError,
        AuthServiceError,
        DomainError,
    ):
        application.add_exception_handler(
            exception_type, cast(ExceptionHandler, mapped_error_handler)
        )
    application.add_exception_handler(
        RequestValidationError, cast(ExceptionHandler, validation_error_handler)
    )
    application.add_exception_handler(
        StarletteHTTPException, cast(ExceptionHandler, http_error_handler)
    )
