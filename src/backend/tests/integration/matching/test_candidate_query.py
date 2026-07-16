from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType
from app.items.service import DomainError
from app.matching.service import create_lost_record, generate_candidates, list_candidates


@pytest.mark.asyncio
async def test_owner_receives_at_most_top_five_candidates(matching_database) -> None:
    engine, owner_id, finder_id = matching_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        lost = await create_lost_record(
            session,
            owner_user_id=owner_id,
            item_type=ItemType.OTHER,
            event_time=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
            location_public="图书馆",
            name_public="黑色折叠伞",
            description_public="外观完整",
        )
        await session.flush()
        await generate_candidates(session, lost_record=lost)
        await session.commit()

        candidates = await list_candidates(session, lost.id, owner_id)
        assert 1 <= len(candidates) <= 5
        with pytest.raises(DomainError, match="NOT_OWNER"):
            await list_candidates(session, lost.id, finder_id)
