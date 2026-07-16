from uuid import uuid4

import pytest

from app.auth.rbac import (
    Actor,
    AuthorizationError,
    ensure_owner,
    ensure_owner_or_admin,
    require_role,
)
from app.db.enums import UserRole


def test_require_role_allows_matching_role_and_rejects_other_roles() -> None:
    admin = Actor(id=uuid4(), role=UserRole.ADMIN)
    user = Actor(id=uuid4(), role=UserRole.USER)

    assert require_role(UserRole.ADMIN)(admin) is admin
    assert require_role(UserRole.USER, UserRole.ADMIN)(user) is user
    with pytest.raises(AuthorizationError, match="FORBIDDEN"):
        require_role(UserRole.ADMIN)(user)


def test_resource_authorization_uses_owner_id_and_admin_is_explicit() -> None:
    owner = uuid4()
    other = uuid4()
    user = Actor(id=owner, role=UserRole.USER)
    admin = Actor(id=other, role=UserRole.ADMIN)

    assert ensure_owner(user, owner) is user
    with pytest.raises(AuthorizationError, match="FORBIDDEN"):
        ensure_owner(user, other)
    assert ensure_owner_or_admin(admin, owner) is admin
