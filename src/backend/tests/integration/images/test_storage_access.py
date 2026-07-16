from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User  # noqa: F401 - register FK metadata
from app.images.models import ImageAsset
from app.items.models import ItemRecord  # noqa: F401 - register FK metadata
from app.images.service import create_confirmed_redaction, store_private_asset
from app.images.schemas import RedactionRegion
from app.images.storage import LocalStorage
from app.db.enums import ImagePurpose

from .conftest import sample_png


@pytest.mark.asyncio
async def test_private_upload_and_confirmed_public_redaction_are_isolated(
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
            region=RedactionRegion(x=1, y=1, width=2, height=2),
        )
        private_key = original.object_key
        public_key = public.object_key
        await session.commit()

    assert private_key.startswith("private/")
    assert public_key.startswith("public/")
    assert storage.read(private_key) == sample_png()
    assert storage.read(public_key) != sample_png()

    async with AsyncSession(engine) as session:
        assets = (await session.scalars(select(ImageAsset))).all()
    assert len(assets) == 2
