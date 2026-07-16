from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.db.enums import UserRole


class AuthorizationError(PermissionError):
    """Stable authorization failure."""

    def __init__(self, code: str = "FORBIDDEN") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Actor:
    id: UUID
    role: UserRole


def require_role(*roles: UserRole):
    if not roles:
        raise ValueError("at least one role is required")
    required = frozenset(UserRole(role) for role in roles)

    def checker(actor: Actor) -> Actor:
        if actor.role not in required:
            raise AuthorizationError()
        return actor

    return checker


def ensure_owner(actor: Actor, owner_id: UUID) -> Actor:
    if actor.id != owner_id:
        raise AuthorizationError()
    return actor


def ensure_owner_or_admin(actor: Actor, owner_id: UUID) -> Actor:
    if actor.role is not UserRole.ADMIN and actor.id != owner_id:
        raise AuthorizationError()
    return actor
