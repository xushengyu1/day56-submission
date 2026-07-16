import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthorizationError
from app.db.enums import UserRole
from app.reviews.service import list_admin_review_queue


@pytest.mark.asyncio
async def test_admin_queue_is_role_guarded_and_minimized(review_database) -> None:
    engine, _ = review_database
    async with AsyncSession(engine) as session:
        queue = await list_admin_review_queue(session, actor_role=UserRole.ADMIN)
        with pytest.raises(AuthorizationError):
            await list_admin_review_queue(session, actor_role=UserRole.USER)

    assert queue
    serialized = str([item.model_dump(mode="json") for item in queue]).casefold()
    for forbidden in ("hmac", "answer_key", "submitted_hmac", "object_key", "password", "token"):
        assert forbidden not in serialized
