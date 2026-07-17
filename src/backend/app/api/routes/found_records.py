from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.images.models import ImageAsset
from app.images.service import create_confirmed_redaction
from app.images.storage import LocalStorage
from app.items.schemas import (
    FoundConfirmation,
    FoundDraftCreate,
    IdentityConfirmation,
    OtherQuestionConfirmation,
    PublishRequest,
    RedactionRequest,
)
from app.items.service import (
    DomainError,
    confirm_found_draft,
    confirm_identity_document,
    confirm_other_questions,
    create_found_draft,
    extract_found_record,
    publish_found_record,
)
from app.multimodal.factory import get_multimodal_adapter
from app.multimodal.image_data import encode_image_data_url
from app.multimodal.ports import MultimodalPort
from app.settings import settings


router = APIRouter(prefix="/api/found-records", tags=["found-records"])
_storage = LocalStorage(Path("storage"))


def _http_error(error: DomainError) -> HTTPException:
    if error.code == "NOT_FOUND":
        return HTTPException(404, error.code)
    if error.code == "NOT_OWNER":
        return HTTPException(403, error.code)
    if error.code == "VERSION_CONFLICT":
        return HTTPException(409, error.code)
    return HTTPException(400, error.code)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_record(
    payload: FoundDraftCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        record = await create_found_draft(
            session,
            owner_user_id=user.id,
            event_time=payload.event_time,
            location_public=payload.location_public,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return {"id": str(record.id), "status": record.status.value, "version": record.version}


@router.post("/{record_id}/extract")
async def extract_record(
    record_id: UUID,
    image_asset_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    adapter: MultimodalPort = Depends(get_multimodal_adapter),
) -> dict[str, object]:
    asset = await session.get(ImageAsset, image_asset_id)
    if asset is None or asset.record_id != record_id or asset.uploader_user_id != user.id:
        raise HTTPException(404, "NOT_FOUND")
    try:
        image_data_url = encode_image_data_url(
            _storage.read(asset.object_key), Path(asset.object_key).suffix
        )
    except (OSError, ValueError):
        raise HTTPException(400, "IMAGE_UNAVAILABLE") from None
    try:
        draft = await extract_found_record(
            session,
            record_id=record_id,
            actor_id=user.id,
            image_ref=image_data_url,
            adapter=adapter,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return draft.model_dump(mode="json")


@router.put("/{record_id}/confirmation")
async def confirm_record(
    record_id: UUID,
    payload: FoundConfirmation,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        record = await confirm_found_draft(
            session,
            record_id=record_id,
            actor_id=user.id,
            **payload.model_dump(),
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return {"id": str(record.id), "version": record.version}


@router.post("/{record_id}/identity-confirmation")
async def confirm_identity(
    record_id: UUID,
    payload: IdentityConfirmation,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    try:
        secret = await confirm_identity_document(
            session,
            record_id=record_id,
            actor_id=user.id,
            full_number=payload.full_number,
            digits_confirmed=payload.digits_confirmed,
            hmac_key=settings.id_hmac_key_v1.encode("utf-8"),
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return {"number_masked": secret.number_masked}


@router.post("/{record_id}/redaction", status_code=status.HTTP_201_CREATED)
async def redact_record_image(
    record_id: UUID,
    payload: RedactionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    original = await session.get(ImageAsset, payload.original_asset_id)
    if original is None or original.record_id != record_id or original.uploader_user_id != user.id:
        raise HTTPException(404, "NOT_FOUND")
    try:
        asset = await create_confirmed_redaction(
            session, _storage, original=original, region=payload.region
        )
        await session.commit()
    except ValueError as error:
        await session.rollback()
        raise HTTPException(400, str(error)) from None
    return {"asset_id": str(asset.id), "status": asset.redaction_status.value}


@router.post("/{record_id}/questions")
async def confirm_questions(
    record_id: UUID,
    payload: OtherQuestionConfirmation,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    adapter: MultimodalPort = Depends(get_multimodal_adapter),
) -> dict[str, str]:
    try:
        question_set = await confirm_other_questions(
            session,
            record_id=record_id,
            actor_id=user.id,
            hidden_description=payload.hidden_description,
            adapter=adapter,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return {"verification_set_id": str(question_set.id)}


@router.post("/{record_id}/publish")
async def publish_record(
    record_id: UUID,
    payload: PublishRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        record = await publish_found_record(
            session,
            record_id=record_id,
            actor_id=user.id,
            expected_version=payload.expected_version,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        raise _http_error(error) from None
    return {"id": str(record.id), "status": record.status.value, "version": record.version}
