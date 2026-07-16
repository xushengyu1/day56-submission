from uuid import uuid4

import pytest

from app.auth.rbac import Actor, AuthorizationError, ensure_owner, require_role
from app.db.enums import UserRole


def test_user_cannot_pass_admin_role_or_other_user_owner_check() -> None:
    user = Actor(id=uuid4(), role=UserRole.USER)

    with pytest.raises(AuthorizationError):
        require_role(UserRole.ADMIN)(user)
    with pytest.raises(AuthorizationError):
        ensure_owner(user, uuid4())
