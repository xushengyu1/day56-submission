from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType, RecordStatus
from app.items.service import DomainError, confirm_found_draft, create_found_draft


@pytest.mark.asyncio
async def test_found_draft_requires_owner_and_expected_version(item_database) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await create_found_draft(
            session,
            owner_user_id=owner_id,
            event_time=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
            location_public="A 楼一层",
        )
        await session.flush()
        assert record.status is RecordStatus.DRAFT

        await confirm_found_draft(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=1,
            item_type=ItemType.OTHER,
            name_public="黑色折叠伞",
            description_public="外观完整",
        )
        assert record.version == 2

        with pytest.raises(DomainError, match="VERSION_CONFLICT"):
            await confirm_found_draft(
                session,
                record_id=record.id,
                actor_id=owner_id,
                expected_version=1,
                item_type=ItemType.OTHER,
                name_public="黑色折叠伞",
                description_public="修改",
            )
