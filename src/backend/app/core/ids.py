from __future__ import annotations

from uuid import UUID, uuid4


def new_request_id() -> str:
    return str(uuid4())


def validate_request_id(value: str) -> bool:
    try:
        UUID(value)
    except (TypeError, ValueError, AttributeError):
        return False
    return True
