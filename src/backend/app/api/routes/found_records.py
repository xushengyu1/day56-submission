from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import APIError
from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.db.enums import RecordKind
from app.images.models import ImageAsset
from app.images.schemas import validate_image_bytes
from app.images.service import create_confirmed_redaction
from app.images.storage import LocalStorage
from app.items.query_service import get_record_detail
from app.items.schemas import (
    FoundConfirmation,
    FoundDraftCreate,
    FoundExtractionResponse,
    IdentityConfirmation,
    ExtractionRequest,
    OtherQuestionConfirmation,
    PublishRequest,
    RedactionRequest,
    ItemRecordPublic,
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
from app.multimodal.schemas import ExtractionDraft
from app.settings import settings


router = APIRouter(prefix="/api/found-records", tags=["found-records"])
_storage = LocalStorage(Path("storage"))


def _extraction_response(draft: ExtractionDraft) -> FoundExtractionResponse:
    return FoundExtractionResponse(
        suggested_name=draft.name_public,
        suggested_description=draft.description_public,
        suggested_item_type=draft.item_type,
        confidence=draft.confidence,
        status=draft.status,
    )


@router.post("/extract-preview", response_model=FoundExtractionResponse)
async def extract_preview(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
    adapter: MultimodalPort = Depends(get_multimodal_adapter),
) -> FoundExtractionResponse:
    """Recognize an image before a found-record draft exists."""
    try:
        data = await file.read()
        validation = validate_image_bytes(data, file.content_type or "")
        image_data_url = encode_image_data_url(data, validation.format_name)
        draft = await adapter.extract_found_item(
            image_data_url, {"flow": "found_draft_preview"}
        )
    except ValueError as error:
        raise APIError(getattr(error, "code", "MODEL_UNAVAILABLE")) from None
    except RuntimeError:
        raise APIError("MODEL_UNAVAILABLE") from None
    return _extraction_response(draft)


@router.get("/{record_id}", response_model=ItemRecordPublic)
async def found_record_detail(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> ItemRecordPublic:
    return await get_record_detail(
        session,
        record_id=record_id,
        kind=RecordKind.FOUND,
        actor_id=user.id,
    )


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
            location_area=payload.location_area,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {"id": str(record.id), "status": record.status.value, "version": record.version}


@router.post("/{record_id}/extract", response_model=FoundExtractionResponse)
async def extract_record(
    record_id: UUID,
    payload: ExtractionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    adapter: MultimodalPort = Depends(get_multimodal_adapter),
) -> FoundExtractionResponse:
    asset = await session.get(ImageAsset, payload.image_asset_id)
    if asset is None or asset.record_id != record_id or asset.uploader_user_id != user.id:
        raise APIError("NOT_FOUND")
    try:
        image_data_url = encode_image_data_url(
            _storage.read(asset.object_key), Path(asset.object_key).suffix
        )
    except (OSError, ValueError):
        raise APIError("IMAGE_UNAVAILABLE") from None
    try:
        draft = await extract_found_record(
            session,
            record_id=record_id,
            actor_id=user.id,
            image_ref=image_data_url,
            adapter=adapter,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return _extraction_response(draft)


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
    except DomainError:
        await session.rollback()
        raise
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
    except DomainError:
        await session.rollback()
        raise
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
        raise APIError("NOT_FOUND")
    try:
        asset = await create_confirmed_redaction(
            session, _storage, original=original, region=payload.region
        )
        await session.commit()
    except ValueError as error:
        await session.rollback()
        raise APIError(str(error)) from None
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
    except DomainError:
        await session.rollback()
        raise
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
            storage=_storage,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {"id": str(record.id), "status": record.status.value, "version": record.version}
