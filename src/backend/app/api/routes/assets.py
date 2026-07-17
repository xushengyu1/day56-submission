from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.errors import APIError
from app.auth.models import User
from app.database import get_database_session
from app.db.enums import DataClass, ImagePurpose, RedactionStatus
from app.images.models import ImageAsset
from app.images.storage import LocalStorage
from app.items.models import ItemRecord


router = APIRouter(prefix="/api/assets", tags=["assets"])
_storage = LocalStorage(Path("storage"))


@router.get("/{asset_id}")
async def download_asset(
    asset_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> Response:
    asset = await session.get(ImageAsset, asset_id)
    if asset is None:
        raise APIError("NOT_FOUND")
    record = await session.get(ItemRecord, asset.record_id)
    is_confirmed_public = (
        asset.purpose is ImagePurpose.PUBLIC_REDACTED
        and asset.data_class is DataClass.PUBLIC
        and asset.redaction_status is RedactionStatus.CONFIRMED
    )
    is_owner = asset.uploader_user_id == user.id or (
        record is not None and record.owner_user_id == user.id
    )
    if not is_confirmed_public and not is_owner:
        raise APIError("NOT_FOUND")
    try:
        content = _storage.read(asset.object_key)
    except (OSError, ValueError):
        raise APIError("IMAGE_UNAVAILABLE") from None
    return Response(content=content, media_type=asset.mime_type)
