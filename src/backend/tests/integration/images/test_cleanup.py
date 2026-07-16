from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User  # noqa: F401 - register FK metadata
from app.images.models import ImageAsset
from app.items.models import ItemRecord  # noqa: F401 - register FK metadata
from app.images.service import cleanup_private_assets, create_confirmed_redaction, store_private_asset
from app.images.schemas import RedactionRegion
from app.images.storage import LocalStorage
from app.db.enums import ImagePurpose

from .conftest import sample_png


@pytest.mark.asyncio
async def test_cleanup_removes_private_files_but_preserves_public(
    image_database, tmp_path: Path
) -> None:
    engine, user_id, record_id = image_database
    storage = LocalStorage(tmp_path)
    async with AsyncSession(engine) as session:
        original = await store_private_asset(
            session,
            storage,
            record_id=record_id,
            uploader_user_id=user_id,
            data=sample_png(),
            declared_mime="image/png",
            purpose=ImagePurpose.FINDER_ORIGINAL,
        )
        public = await create_confirmed_redaction(
            session,
            storage,
            original=original,
            region=RedactionRegion(x=0, y=0, width=1, height=1),
        )
        private_key = original.object_key
        public_key = public.object_key
        await session.commit()
        async with session.begin():
            assert await cleanup_private_assets(
                session, storage, record_id=record_id
            ) == 1

    assert not storage.path_for(private_key).exists()
    assert storage.path_for(public_key).exists()
    async with AsyncSession(engine) as session:
        remaining = (await session.scalars(select(ImageAsset))).all()
    assert len(remaining) == 1
    assert remaining[0].object_key == public_key
