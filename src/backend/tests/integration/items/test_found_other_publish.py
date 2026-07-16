from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType, RecordStatus
from app.db.enums import ImagePurpose
from app.images.service import store_private_asset
from app.images.storage import LocalStorage
from app.items.service import (
    confirm_found_draft,
    confirm_other_questions,
    create_found_draft,
    publish_found_record,
)
from app.multimodal.mock import MockMultimodalAdapter
from app.verification.models import VerificationQuestion

from .conftest import sample_png


@pytest.mark.asyncio
async def test_other_publish_requires_confirmed_valid_questions(item_database, tmp_path) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await create_found_draft(
            session,
            owner_user_id=owner_id,
            event_time=datetime.now(timezone.utc),
            location_public="教学楼",
        )
        await session.flush()
        await store_private_asset(
            session,
            LocalStorage(tmp_path),
            record_id=record.id,
            uploader_user_id=owner_id,
            data=sample_png(),
            declared_mime="image/png",
            purpose=ImagePurpose.FINDER_ORIGINAL,
        )
        await confirm_found_draft(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=1,
            item_type=ItemType.OTHER,
            name_public="黑色折叠伞",
            description_public="外观完整",
        )
        await confirm_other_questions(
            session,
            record_id=record.id,
            actor_id=owner_id,
            hidden_description="伞柄底部有裂纹，伞套有字母标记",
            adapter=MockMultimodalAdapter(),
        )
        await publish_found_record(
            session, record_id=record.id, actor_id=owner_id, expected_version=2
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        question_count = await session.scalar(select(func.count(VerificationQuestion.id)))
    assert question_count == 2
    assert record.status is RecordStatus.PUBLISHED
