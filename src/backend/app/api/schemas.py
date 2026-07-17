from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    field_errors: dict[str, str] | None = None
