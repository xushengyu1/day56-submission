from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType
from app.matching.service import create_lost_record, generate_candidates, list_candidates


@pytest.mark.asyncio
async def test_candidate_dto_contains_public_fields_only(matching_database) -> None:
    engine, owner_id, _ = matching_database
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
        body = [item.model_dump(mode="json") for item in await list_candidates(session, lost.id, owner_id)]

    serialized = str(body).casefold()
    for forbidden in ("embedding", "event_time_exact", "location_normalized", "answer_key", "hmac", "object_key", "contact"):
        assert forbidden not in serialized
