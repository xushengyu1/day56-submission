from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus, ItemType
from app.items.models import ItemRecord
from app.matching.models import CandidateMatch
from app.matching.service import create_lost_record, generate_candidates
from app.reviews.models import Claim


@pytest.mark.asyncio
async def test_recalculation_preserves_candidate_referenced_by_claim(
    matching_database,
) -> None:
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
        lost_id = lost.id
        candidates = await generate_candidates(session, lost_record=lost)
        await session.flush()
        claimed_candidate_id = candidates[0].id
        session.add(
            Claim(
                candidate_id=claimed_candidate_id,
                requester_user_id=owner_id,
                item_type=ItemType.OTHER,
                status=ClaimStatus.PENDING_HANDOFF,
                route_source="OTHER_MODEL",
            )
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        loaded_lost = await session.get(ItemRecord, lost_id)
        assert loaded_lost is not None
        await generate_candidates(session, lost_record=loaded_lost)
        await session.commit()

    async with AsyncSession(engine) as session:
        assert await session.get(CandidateMatch, claimed_candidate_id) is not None
