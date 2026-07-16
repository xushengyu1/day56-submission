from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ItemType, RecordStatus
from app.db.enums import ImagePurpose
from app.images.schemas import RedactionRegion
from app.images.service import create_confirmed_redaction, store_private_asset
from app.images.storage import LocalStorage
from app.items.service import (
    confirm_found_draft,
    confirm_identity_document,
    create_found_draft,
    publish_found_record,
)
from app.verification.models import IdentityDocumentSecret

from .conftest import sample_png


VALID_ID = "110101200001010010"


@pytest.mark.asyncio
async def test_identity_publish_persists_only_hmac_and_mask(item_database, tmp_path) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await create_found_draft(
            session,
            owner_user_id=owner_id,
            event_time=datetime.now(timezone.utc),
            location_public="图书馆",
        )
        await session.flush()
        storage = LocalStorage(tmp_path)
        original = await store_private_asset(
            session,
            storage,
            record_id=record.id,
            uploader_user_id=owner_id,
            data=sample_png(),
            declared_mime="image/png",
            purpose=ImagePurpose.FINDER_ORIGINAL,
        )
        await create_confirmed_redaction(
            session,
            storage,
            original=original,
            region=RedactionRegion(x=0, y=0, width=2, height=2),
        )
        await confirm_found_draft(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=1,
            item_type=ItemType.IDENTITY_DOCUMENT,
            name_public="居民身份证",
            description_public="拾获证件",
        )
        await confirm_identity_document(
            session,
            record_id=record.id,
            actor_id=owner_id,
            full_number=VALID_ID,
            digits_confirmed=True,
            hmac_key=b"synthetic-test-key",
        )
        await publish_found_record(
            session, record_id=record.id, actor_id=owner_id, expected_version=2
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        secret = await session.scalar(select(IdentityDocumentSecret))
    assert secret is not None
    assert secret.number_masked == "110***********0010"
    assert VALID_ID not in secret.number_hmac.decode("ascii", errors="ignore")
    assert record.status is RecordStatus.PUBLISHED
