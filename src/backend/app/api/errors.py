from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(ValueError):
    def __init__(self, code: str, *, status_code: int = 400) -> None:
        if not code:
            raise ValueError("error code must not be empty")
        super().__init__(code)
        self.code = code
        self.status_code = status_code


async def api_error_handler(_request: Request, error: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.code},
    )
