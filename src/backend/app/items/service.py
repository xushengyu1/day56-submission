from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.service import append_audit_event
from app.auth.models import User  # noqa: F401 - registers FK target metadata
from app.core.idempotency import get_idempotent_result, hash_request, store_idempotent_result
from app.db.enums import (
    ActorType,
    ClaimStatus,
    DataClass,
    DocumentType,
    ImagePurpose,
    ItemType,
    RecordKind,
    RecordStatus,
    RedactionStatus,
)
from app.images.models import ImageAsset
from app.items.models import ItemRecord
from app.items.schemas import HandoffResult
from app.items.policies import validate_common_publish_fields
from app.matching.embedding import EmbeddingError, EmbeddingPort
from app.matching.embedding_factory import build_embedding_adapter
from app.matching.models import CandidateMatch
from app.multimodal.ports import MultimodalPort
from app.multimodal.models import AIExtraction
from app.multimodal.schemas import ExtractionDraft
from app.reviews.models import Claim
from app.verification.identity import compute_id_hmac, mask_cn_id, normalize_cn_id
from app.verification.models import (
    IdentityDocumentSecret,
    VerificationQuestion,
    VerificationSet,
)
from app.verification.other import validate_question_set


class DomainError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


async def _owned_record(
    session: AsyncSession, record_id: UUID, actor_id: UUID
) -> ItemRecord:
    record = await session.get(ItemRecord, record_id)
    if record is None:
        raise DomainError("NOT_FOUND")
    if record.owner_user_id != actor_id:
        raise DomainError("NOT_OWNER")
    return record


async def create_found_draft(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    event_time: datetime,
    location_public: str,
) -> ItemRecord:
    if not location_public.strip():
        raise DomainError("FIELD_INVALID")
    record = ItemRecord(
        owner_user_id=owner_user_id,
        kind=RecordKind.FOUND,
        item_type=ItemType.OTHER,
        status=RecordStatus.DRAFT,
        event_time_exact=event_time,
        event_time_public=event_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        location_public=location_public.strip(),
        version=1,
    )
    session.add(record)
    return record


async def confirm_found_draft(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    expected_version: int,
    item_type: ItemType,
    name_public: str,
    description_public: str,
) -> ItemRecord:
    record = await _owned_record(session, record_id, actor_id)
    if record.status is not RecordStatus.DRAFT:
        raise DomainError("RECORD_NOT_DRAFT")
    if record.version != expected_version:
        raise DomainError("VERSION_CONFLICT")
    if not name_public.strip() or not description_public.strip():
        raise DomainError("FIELD_INVALID")
    record.item_type = item_type
    record.name_public = name_public.strip()
    record.description_public = description_public.strip()
    record.version += 1
    return record


async def extract_found_record(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    image_ref: str,
    adapter: MultimodalPort,
) -> ExtractionDraft:
    record = await _owned_record(session, record_id, actor_id)
    if record.status is not RecordStatus.DRAFT:
        raise DomainError("RECORD_NOT_DRAFT")
    try:
        draft = adapter.extract_found_item(image_ref, {"record_id": str(record_id)})
    except (RuntimeError, ValueError):
        raise DomainError("MODEL_UNAVAILABLE") from None
    extraction = AIExtraction(
        record_id=record_id,
        provider=draft.provider,
        model=draft.model,
        version=draft.version,
        raw_result_redacted=draft.raw_result_redacted,
        suggested_item_type=draft.item_type,
        draft_snapshot={
            "name_public": draft.name_public,
            "description_public": draft.description_public,
        },
        confidence={"overall": draft.confidence},
        status=draft.status,
    )
    session.add(extraction)
    await session.flush()
    record.ai_extraction_id = extraction.id
    return draft


async def confirm_identity_document(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    full_number: str,
    digits_confirmed: bool,
    hmac_key: bytes,
) -> IdentityDocumentSecret:
    record = await _owned_record(session, record_id, actor_id)
    if record.item_type is not ItemType.IDENTITY_DOCUMENT or not digits_confirmed:
        raise DomainError("ID_INVALID")
    try:
        normalized = normalize_cn_id(full_number)
    except ValueError:
        raise DomainError("ID_INVALID") from None
    digest = compute_id_hmac(normalized, hmac_key).encode("ascii")
    secret = await session.get(IdentityDocumentSecret, record_id)
    if secret is None:
        secret = IdentityDocumentSecret(
            found_record_id=record_id,
            item_type=ItemType.IDENTITY_DOCUMENT,
            document_type=DocumentType.CN_RESIDENT_ID,
            number_hmac=digest,
            number_masked=mask_cn_id(normalized),
            key_version=1,
        )
        session.add(secret)
    else:
        secret.number_hmac = digest
        secret.number_masked = mask_cn_id(normalized)
    secret.finder_confirmed_at = datetime.now(timezone.utc)
    return secret


async def confirm_other_questions(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    hidden_description: str,
    adapter: MultimodalPort,
) -> VerificationSet:
    record = await _owned_record(session, record_id, actor_id)
    if record.item_type is not ItemType.OTHER or not hidden_description.strip():
        raise DomainError("HIDDEN_INFO_INSUFFICIENT")
    draft = adapter.generate_questions(hidden_description)
    if not validate_question_set(draft).valid:
        raise DomainError("QUESTION_GENERATION_FAILED")
    verification_set = VerificationSet(
        found_record_id=record_id,
        item_type=ItemType.OTHER,
        hidden_description=hidden_description.strip(),
        confirmed_by=actor_id,
        confirmed_at=datetime.now(timezone.utc),
    )
    session.add(verification_set)
    await session.flush()
    for question in draft.questions:
        session.add(
            VerificationQuestion(
                verification_set_id=verification_set.id,
                question_text=question.question_text,
                answer_key=question.answer_key,
                dimension=question.dimension,
                provider_model=getattr(adapter, "model", "unknown"),
                schema_version=getattr(adapter, "version", "unknown"),
                confirmed_by=actor_id,
                confirmed_at=datetime.now(timezone.utc),
            )
        )
    return verification_set


async def publish_found_record(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    expected_version: int,
    embedding_adapter: EmbeddingPort | None = None,
) -> ItemRecord:
    record = await _owned_record(session, record_id, actor_id)
    if record.status is not RecordStatus.DRAFT:
        raise DomainError("RECORD_NOT_DRAFT")
    if record.version != expected_version:
        raise DomainError("VERSION_CONFLICT")
    if validate_common_publish_fields(record):
        raise DomainError("PUBLISH_GUARD_FAILED")

    original_count = await session.scalar(
        select(func.count(ImageAsset.id)).where(
            ImageAsset.record_id == record_id,
            ImageAsset.purpose == ImagePurpose.FINDER_ORIGINAL,
            ImageAsset.data_class == DataClass.PRIVATE,
        )
    )
    if not original_count:
        raise DomainError("PUBLISH_GUARD_FAILED")

    if record.item_type is ItemType.IDENTITY_DOCUMENT:
        secret = await session.get(IdentityDocumentSecret, record_id)
        public_count = await session.scalar(
            select(func.count(ImageAsset.id)).where(
                ImageAsset.record_id == record_id,
                ImageAsset.purpose == ImagePurpose.PUBLIC_REDACTED,
                ImageAsset.redaction_status == RedactionStatus.CONFIRMED,
            )
        )
        if secret is None or secret.finder_confirmed_at is None or not public_count:
            raise DomainError("PUBLISH_GUARD_FAILED")
    else:
        verification_set = await session.scalar(
            select(VerificationSet).where(VerificationSet.found_record_id == record_id)
        )
        if verification_set is None or verification_set.confirmed_at is None:
            raise DomainError("PUBLISH_GUARD_FAILED")

    text = f"{record.name_public}\n{record.description_public}\n{record.location_public}"
    try:
        adapter = embedding_adapter or build_embedding_adapter()
        embedding = (await adapter.embed([text]))[0]
    except EmbeddingError:
        raise DomainError("EMBEDDING_UNAVAILABLE") from None
    record.embedding = embedding
    record.embedding_model = adapter.model
    record.embedding_dimensions = adapter.dimension
    record.status = RecordStatus.PUBLISHED
    record.published_at = datetime.now(timezone.utc)
    record.version += 1
    append_audit_event(
        session,
        AuditEventInput(
            event_type="FOUND_RECORD_PUBLISHED",
            aggregate_type="item_record",
            aggregate_id=record.id,
            actor_type=ActorType.FINDER,
            actor_id=actor_id,
            result_code="PUBLISHED",
            metadata={"item_type": record.item_type.value},
        ),
    )
    return record


async def get_claim_contact(
    session: AsyncSession, *, claim_id: UUID, requester_id: UUID
) -> dict[str, str]:
    claim = await session.get(Claim, claim_id)
    if (
        claim is None
        or claim.requester_user_id != requester_id
        or claim.status is not ClaimStatus.PENDING_HANDOFF
    ):
        raise DomainError("NOT_FOUND")
    candidate = await session.get(CandidateMatch, claim.candidate_id)
    if candidate is None:
        raise DomainError("NOT_FOUND")
    found = await session.get(ItemRecord, candidate.found_record_id)
    if found is None:
        raise DomainError("NOT_FOUND")
    finder = await session.get(User, found.owner_user_id)
    if finder is None:
        raise DomainError("NOT_FOUND")
    return {"email": finder.email}


async def complete_handoff(
    session: AsyncSession,
    *,
    claim_id: UUID,
    finder_id: UUID,
    confirmation: bool,
    idempotency_key: str,
) -> HandoffResult:
    if not confirmation:
        raise DomainError("CONFIRMATION_REQUIRED")
    request_hash = hash_request(
        {"claim_id": str(claim_id), "confirmation": confirmation}
    )
    replay = await get_idempotent_result(
        session, finder_id, idempotency_key, request_hash
    )
    if replay is not None:
        return HandoffResult.model_validate(replay.response_body)
    claim = await session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
    if claim is None:
        raise DomainError("NOT_FOUND")
    candidate = await session.get(CandidateMatch, claim.candidate_id)
    if candidate is None:
        raise DomainError("NOT_FOUND")
    found = await session.get(ItemRecord, candidate.found_record_id)
    lost = await session.get(ItemRecord, candidate.lost_record_id)
    if found is None or lost is None or found.owner_user_id != finder_id:
        raise DomainError("NOT_FINDER")
    if claim.status is not ClaimStatus.PENDING_HANDOFF:
        raise DomainError("HANDOFF_NOT_READY")
    claim.status = ClaimStatus.CLAIMED
    claim.final_reason = "HANDOFF_COMPLETED"
    claim.updated_at = datetime.now(timezone.utc)
    found.status = RecordStatus.CLAIMED
    lost.status = RecordStatus.CLAIMED
    append_audit_event(
        session,
        AuditEventInput(
            event_type="HANDOFF_COMPLETED",
            aggregate_type="claim",
            aggregate_id=claim.id,
            actor_type=ActorType.FINDER,
            actor_id=finder_id,
            result_code="CLAIMED",
            metadata={"confirmation": True},
        ),
    )
    result = HandoffResult(claim_id=claim.id, status=claim.status)
    store_idempotent_result(
        session,
        finder_id,
        idempotency_key,
        request_hash,
        200,
        result.model_dump(mode="json"),
    )
    return result
