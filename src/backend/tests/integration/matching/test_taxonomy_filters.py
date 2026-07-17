from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import (
    LocationArea,
    PublicCategory,
    RecordKind,
    RecordStatus,
)
from app.items.models import ItemRecord
from app.matching.service import create_lost_record, generate_candidates


@pytest.mark.asyncio
async def test_candidates_require_exact_public_category_and_location_area(
    matching_database,
) -> None:
    engine, owner_id, _ = matching_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        found = (
            await session.scalars(
                select(ItemRecord)
                .where(ItemRecord.kind == RecordKind.FOUND)
                .order_by(ItemRecord.id)
            )
        ).all()
        exact = found[0]
        exact.public_category = PublicCategory.ELECTRONICS

        found[1].public_category = PublicCategory.CLOTHING
        found[2].public_category = PublicCategory.ELECTRONICS
        found[2].location_area = LocationArea.TEACHING_BUILDING
        found[3].public_category = PublicCategory.ELECTRONICS
        found[3].kind = RecordKind.LOST
        found[4].public_category = PublicCategory.ELECTRONICS
        found[4].status = RecordStatus.DRAFT
        found[5].public_category = PublicCategory.ELECTRONICS
        found[5].embedding_model = "legacy-model"

        lost = await create_lost_record(
            session,
            owner_user_id=owner_id,
            public_category=PublicCategory.ELECTRONICS,
            location_area=LocationArea.LIBRARY,
            event_time=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
            name_public="黑色折叠伞",
            description_public="图书馆三楼 302 室，伞柄有划痕",
        )
        await session.flush()
        candidates = await generate_candidates(session, lost_record=lost)

    assert [candidate.found_record_id for candidate in candidates] == [exact.id]
