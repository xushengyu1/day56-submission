import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthorizationError
from app.db.enums import UserRole
from app.audit.projection import get_record_timeline


@pytest.mark.asyncio
async def test_timeline_is_related_user_only_and_hides_internal_metadata(
    handoff_database,
) -> None:
    engine, ids = handoff_database
    async with AsyncSession(engine) as session:
        timeline = await get_record_timeline(
            session,
            record_id=ids["found"],
            actor_id=ids["finder"],
            actor_role=UserRole.USER,
        )
        with pytest.raises(AuthorizationError):
            await get_record_timeline(
                session,
                record_id=ids["found"],
                actor_id=ids["other"],
                actor_role=UserRole.USER,
            )

    serialized = str(timeline).casefold()
    assert "found_record_published" in serialized
    assert "admin_note" not in serialized
    assert "private_path" not in serialized
