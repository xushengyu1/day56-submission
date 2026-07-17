from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import APIError
from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.db.enums import ImagePurpose
from app.images.service import store_private_asset
from app.images.storage import LocalStorage
from app.items.models import ItemRecord


router = APIRouter(prefix="/api", tags=["uploads"])
_storage = LocalStorage(Path("storage"))


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_image(
    record_id: UUID = Form(...),
    purpose: ImagePurpose = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    record = await session.get(ItemRecord, record_id)
    if record is None or record.owner_user_id != user.id:
        raise APIError("NOT_FOUND")
    try:
        asset = await store_private_asset(
            session,
            _storage,
            record_id=record_id,
            uploader_user_id=user.id,
            data=await file.read(),
            declared_mime=file.content_type or "",
            purpose=purpose,
        )
        await session.commit()
    except ValueError as error:
        await session.rollback()
        raise APIError(str(error)) from None
    return {"asset_id": str(asset.id), "purpose": asset.purpose.value}
