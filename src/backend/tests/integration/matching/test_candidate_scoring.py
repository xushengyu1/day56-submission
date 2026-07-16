from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType
from app.matching.models import CandidateMatch
from app.matching.service import create_lost_record, generate_candidates


@pytest.mark.asyncio
async def test_candidate_component_scores_sum_to_persisted_total(matching_database) -> None:
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

    async with AsyncSession(engine) as session:
        candidates = (await session.scalars(select(CandidateMatch))).all()
    assert candidates
    for candidate in candidates:
        expected = (
            candidate.semantic_score
            + candidate.time_score
            + candidate.location_score
            + candidate.completeness_score
        )
        assert candidate.total_score == expected
