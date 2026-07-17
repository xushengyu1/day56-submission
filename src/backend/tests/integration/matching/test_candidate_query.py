from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LocationArea, PublicCategory
from app.items.service import DomainError
from app.matching.service import create_lost_record, generate_candidates, list_candidates


@pytest.mark.asyncio
async def test_owner_receives_at_most_top_five_candidates(matching_database) -> None:
    engine, owner_id, finder_id = matching_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        lost = await create_lost_record(
            session,
            owner_user_id=owner_id,
            public_category=PublicCategory.OTHER_CATEGORY,
            location_area=LocationArea.LIBRARY,
            event_time=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
            name_public="黑色折叠伞",
            description_public="外观完整",
        )
        await session.flush()
        await generate_candidates(session, lost_record=lost)
        await session.commit()

        first_candidates = await list_candidates(session, lost.id, owner_id)
        assert 1 <= len(first_candidates) <= 5
        first_ids = [candidate.id for candidate in first_candidates]

        await generate_candidates(session, lost_record=lost)
        await session.commit()

        candidates = await list_candidates(session, lost.id, owner_id)
        assert [candidate.id for candidate in candidates] == first_ids
        with pytest.raises(DomainError, match="NOT_OWNER"):
            await list_candidates(session, lost.id, finder_id)
