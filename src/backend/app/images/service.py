from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.images.models import ImageAsset
from app.images.redaction import redact_image_bytes
from app.images.schemas import ImageValidation, RedactionRegion, validate_image_bytes
from app.images.storage import LocalStorage
from app.db.enums import DataClass, ImagePurpose, RedactionStatus


def _extension(validation: ImageValidation) -> str:
    return {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[validation.format_name]


async def store_private_asset(
    session: AsyncSession,
    storage: LocalStorage,
    *,
    record_id: UUID,
    uploader_user_id: UUID,
    data: bytes,
    declared_mime: str,
    purpose: ImagePurpose,
) -> ImageAsset:
    if purpose not in {ImagePurpose.FINDER_ORIGINAL, ImagePurpose.OWNER_SUPPORT}:
        raise ValueError("PRIVATE_PURPOSE_REQUIRED")
    validation = validate_image_bytes(data, declared_mime)
    object_key = storage.save(data, namespace="private", suffix=_extension(validation))
    asset = ImageAsset(
        record_id=record_id,
        uploader_user_id=uploader_user_id,
        purpose=purpose,
        data_class=DataClass.PRIVATE,
        object_key=object_key,
        sha256=hashlib.sha256(data).hexdigest(),
        mime_type=validation.mime_type,
        size_bytes=validation.size_bytes,
        redaction_status=RedactionStatus.NOT_REQUIRED,
    )
    session.add(asset)
    return asset


async def create_confirmed_redaction(
    session: AsyncSession,
    storage: LocalStorage,
    *,
    original: ImageAsset,
    region: RedactionRegion,
) -> ImageAsset:
    if original.purpose is not ImagePurpose.FINDER_ORIGINAL:
        raise ValueError("REDACTION_SOURCE_INVALID")
    source = storage.read(original.object_key)
    redacted = redact_image_bytes(source, region)
    object_key = storage.save(redacted, namespace="public", suffix="png")
    asset = ImageAsset(
        record_id=original.record_id,
        uploader_user_id=original.uploader_user_id,
        purpose=ImagePurpose.PUBLIC_REDACTED,
        data_class=DataClass.PUBLIC,
        object_key=object_key,
        sha256=hashlib.sha256(redacted).hexdigest(),
        mime_type="image/png",
        size_bytes=len(redacted),
        redaction_status=RedactionStatus.CONFIRMED,
    )
    session.add(asset)
    return asset


async def cleanup_private_assets(
    session: AsyncSession,
    storage: LocalStorage,
    *,
    record_id: UUID,
) -> int:
    assets = (
        await session.scalars(
            select(ImageAsset).where(
                ImageAsset.record_id == record_id,
                ImageAsset.data_class == DataClass.PRIVATE,
            )
        )
    ).all()
    for asset in assets:
        storage.delete(asset.object_key)
        await session.delete(asset)
    return len(assets)
