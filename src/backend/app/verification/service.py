from __future__ import annotations

from datetime import datetime, timezone
import hmac
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.service import append_audit_event
from app.auth.models import User  # noqa: F401 - register FK metadata
from app.db.enums import ActorType, ClaimStatus, ItemType, QuestionResult, RecordStatus
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.matching.models import CandidateMatch
from app.reviews.models import Claim, ClaimAttempt
from app.multimodal.ports import ModelAdapterError, MultimodalPort
from app.verification.identity import compute_id_hmac, normalize_cn_id
from app.verification.models import (
    IdentityDocumentSecret,
    VerificationQuestion,
    VerificationSet,
)
from app.verification.other import QuestionDraft, QuestionSetDraft
from app.verification.schemas import ClaimOutcome, QuestionPublic


_ACTIVE_CLAIM_STATUSES = (
    ClaimStatus.SUBMITTED,
    ClaimStatus.VERIFYING,
    ClaimStatus.PENDING_ADMIN_REVIEW,
    ClaimStatus.PENDING_HANDOFF,
)


async def submit_identity_claim(
    session: AsyncSession,
    *,
    candidate_id: UUID,
    requester_id: UUID,
    full_number: str,
    hmac_key: bytes,
) -> ClaimOutcome:
    candidate = await session.scalar(
        select(CandidateMatch)
        .where(CandidateMatch.id == candidate_id)
        .with_for_update()
    )
    if candidate is None:
        raise DomainError("NOT_FOUND")
    lost = await session.get(ItemRecord, candidate.lost_record_id)
    found = await session.get(ItemRecord, candidate.found_record_id)
    if lost is None or found is None or lost.owner_user_id != requester_id:
        raise DomainError("NOT_FOUND")
    if lost.item_type is not ItemType.IDENTITY_DOCUMENT or found.item_type is not ItemType.IDENTITY_DOCUMENT:
        raise DomainError("WRONG_ITEM_TYPE")

    claim = await session.scalar(
        select(Claim)
        .where(
            Claim.candidate_id == candidate_id,
            Claim.requester_user_id == requester_id,
        )
        .order_by(Claim.created_at.desc())
        .limit(1)
    )
    if claim is None:
        claim = Claim(
            candidate_id=candidate_id,
            requester_user_id=requester_id,
            item_type=ItemType.IDENTITY_DOCUMENT,
            status=ClaimStatus.VERIFYING,
            route_source="IDENTITY_RULE",
        )
        session.add(claim)
        await session.flush()

    attempt_count = int(
        await session.scalar(
            select(func.count(ClaimAttempt.id)).where(
                ClaimAttempt.user_id == requester_id,
                ClaimAttempt.candidate_id == candidate_id,
            )
        )
        or 0
    )
    if attempt_count >= 2 or claim.status is ClaimStatus.LOCKED:
        claim.status = ClaimStatus.LOCKED
        raise DomainError("ATTEMPT_LOCKED")

    try:
        normalized = normalize_cn_id(full_number)
    except ValueError:
        raise DomainError("ID_INVALID") from None
    submitted_hmac = compute_id_hmac(normalized, hmac_key).encode("ascii")
    secret = await session.get(IdentityDocumentSecret, found.id)
    exact_match = secret is not None and hmac.compare_digest(
        submitted_hmac, secret.number_hmac
    )
    attempt_no = attempt_count + 1

    if not exact_match:
        status = ClaimStatus.LOCKED if attempt_no >= 2 else ClaimStatus.VERIFYING
        result_code = "ATTEMPT_LOCKED" if status is ClaimStatus.LOCKED else "IDENTITY_NOT_VERIFIED"
        risk_flag = "ATTEMPT_LIMIT" if status is ClaimStatus.LOCKED else None
        claim.status = status
    else:
        duplicate_count = int(
            await session.scalar(
                select(func.count(IdentityDocumentSecret.found_record_id))
                .join(ItemRecord, ItemRecord.id == IdentityDocumentSecret.found_record_id)
                .where(
                    IdentityDocumentSecret.number_hmac == submitted_hmac,
                    ItemRecord.status == RecordStatus.PUBLISHED,
                )
            )
            or 0
        )
        other_active_claims = int(
            await session.scalar(
                select(func.count(Claim.id)).where(
                    Claim.candidate_id == candidate_id,
                    Claim.id != claim.id,
                    Claim.status.in_(_ACTIVE_CLAIM_STATUSES),
                )
            )
            or 0
        )
        if duplicate_count > 1 or other_active_claims:
            status = ClaimStatus.PENDING_ADMIN_REVIEW
            result_code = "DUPLICATE_IDENTITY_REVIEW"
            risk_flag = "DUPLICATE_IDENTITY"
        else:
            status = ClaimStatus.PENDING_HANDOFF
            result_code = "IDENTITY_VERIFIED"
            risk_flag = None
            lost.status = RecordStatus.PENDING_HANDOFF
            found.status = RecordStatus.PENDING_HANDOFF
        claim.status = status

    session.add(
        ClaimAttempt(
            claim_id=claim.id,
            user_id=requester_id,
            candidate_id=candidate_id,
            attempt_no=attempt_no,
            submitted_hmac=submitted_hmac,
            result_code=result_code,
            risk_flag=risk_flag,
        )
    )
    claim.route_source = "IDENTITY_RULE"
    claim.final_reason = result_code
    claim.updated_at = datetime.now(timezone.utc)
    # Get user names for audit
    owner = await session.get(User, requester_id)
    finder = await session.get(User, found.owner_user_id) if found else None

    append_audit_event(
        session,
        AuditEventInput(
            event_type="IDENTITY_CLAIM_ATTEMPTED",
            aggregate_type="claim",
            aggregate_id=claim.id,
            actor_type=ActorType.OWNER,
            actor_id=requester_id,
            result_code=result_code,
            metadata={
                "attempt_no": attempt_no,
                "route_source": claim.route_source,
                "owner_name": owner.username if owner else str(requester_id),
                "owner_email": owner.email if owner else None,
                "finder_name": finder.username if finder else None,
                "finder_email": finder.email if finder else None,
                "item_type": "身份证明文件",
            },
        ),
    )
    return ClaimOutcome(
        claim_id=claim.id,
        status=claim.status,
        result_code=result_code,
        attempt_no=attempt_no,
        attempts_remaining=max(0, 2 - attempt_no),
    )


async def _other_context(
    session: AsyncSession, candidate_id: UUID, requester_id: UUID, *, lock: bool = False
) -> tuple[CandidateMatch, ItemRecord, ItemRecord, VerificationSet]:
    query = select(CandidateMatch).where(CandidateMatch.id == candidate_id)
    if lock:
        query = query.with_for_update()
    candidate = await session.scalar(query)
    if candidate is None:
        raise DomainError("NOT_FOUND")
    lost = await session.get(ItemRecord, candidate.lost_record_id)
    found = await session.get(ItemRecord, candidate.found_record_id)
    if lost is None or found is None or lost.owner_user_id != requester_id:
        raise DomainError("NOT_FOUND")
    if lost.item_type is not ItemType.OTHER or found.item_type is not ItemType.OTHER:
        raise DomainError("WRONG_ITEM_TYPE")
    verification_set = await session.scalar(
        select(VerificationSet).where(
            VerificationSet.found_record_id == found.id,
            VerificationSet.confirmed_at.is_not(None),
        )
    )
    if verification_set is None:
        raise DomainError("QUESTIONS_NOT_READY")
    return candidate, lost, found, verification_set


async def get_other_questions(
    session: AsyncSession, *, candidate_id: UUID, requester_id: UUID
) -> list[QuestionPublic]:
    _, _, _, verification_set = await _other_context(
        session, candidate_id, requester_id
    )
    questions = (
        await session.scalars(
            select(VerificationQuestion)
            .where(VerificationQuestion.verification_set_id == verification_set.id)
            .order_by(VerificationQuestion.id)
        )
    ).all()
    return [
        QuestionPublic(
            id=question.id,
            question_text=question.question_text,
            dimension=question.dimension,
        )
        for question in questions
    ]


async def submit_other_claim(
    session: AsyncSession,
    *,
    candidate_id: UUID,
    requester_id: UUID,
    answers: dict[UUID, str],
    adapter: MultimodalPort,
) -> ClaimOutcome:
    candidate, lost, found, verification_set = await _other_context(
        session, candidate_id, requester_id, lock=True
    )
    questions = (
        await session.scalars(
            select(VerificationQuestion)
            .where(VerificationQuestion.verification_set_id == verification_set.id)
            .order_by(VerificationQuestion.id)
        )
    ).all()
    if set(answers) != {question.id for question in questions}:
        raise DomainError("ANSWER_INVALID")

    claim = Claim(
        candidate_id=candidate_id,
        requester_user_id=requester_id,
        item_type=ItemType.OTHER,
        status=ClaimStatus.VERIFYING,
        route_source="OTHER_MODEL",
    )
    session.add(claim)
    await session.flush()
    draft = QuestionSetDraft(
        questions=tuple(
            QuestionDraft(
                question_text=question.question_text,
                answer_key=question.answer_key,
                dimension=question.dimension,
            )
            for question in questions
        )
    )
    answer_by_dimension = {
        question.dimension: answers[question.id] for question in questions
    }
    try:
        verification = await adapter.verify_answers(draft, answer_by_dimension)
        result_code = verification.reason_code or "UNKNOWN"
        summary = {
            "result": verification.result.value,
            "confidence": verification.confidence,
            "reason_code": verification.reason_code,
        }
    except (ModelAdapterError, RuntimeError, ValueError) as error:
        result_code = getattr(error, "code", "MODEL_UNAVAILABLE")
        verification = None
        summary = {"result": "UNDETERMINED", "reason_code": result_code}

    other_active_claims = int(
        await session.scalar(
            select(func.count(Claim.id)).where(
                Claim.candidate_id == candidate_id,
                Claim.id != claim.id,
                Claim.status.in_(_ACTIVE_CLAIM_STATUSES),
            )
        )
        or 0
    )
    if (
        verification is not None
        and verification.result is QuestionResult.MATCH
        and verification.confidence >= 0.8
        and not other_active_claims
    ):
        claim.status = ClaimStatus.PENDING_HANDOFF
        result_code = "ANSWERS_VERIFIED"
        lost.status = RecordStatus.PENDING_HANDOFF
        found.status = RecordStatus.PENDING_HANDOFF
        risk_flag = None
    else:
        claim.status = ClaimStatus.PENDING_ADMIN_REVIEW
        risk_flag = "OTHER_VERIFICATION_REVIEW"

    claim.final_reason = result_code
    session.add(
        ClaimAttempt(
            claim_id=claim.id,
            user_id=requester_id,
            candidate_id=candidate_id,
            attempt_no=1,
            result_code=result_code,
            answer_summary=summary,
            risk_flag=risk_flag,
        )
    )
    # Get user names for audit
    owner = await session.get(User, requester_id)
    finder = await session.get(User, found.owner_user_id) if found else None

    append_audit_event(
        session,
        AuditEventInput(
            event_type="OTHER_CLAIM_VERIFIED",
            aggregate_type="claim",
            aggregate_id=claim.id,
            actor_type=ActorType.OWNER,
            actor_id=requester_id,
            result_code=result_code,
            metadata={
                "route_source": claim.route_source,
                "owner_name": owner.username if owner else str(requester_id),
                "owner_email": owner.email if owner else None,
                "finder_name": finder.username if finder else None,
                "finder_email": finder.email if finder else None,
                "item_type": "其他物品",
                "verification_result": verification.result.value if verification else "UNDETERMINED",
            },
        ),
    )
    return ClaimOutcome(
        claim_id=claim.id,
        status=claim.status,
        result_code=result_code,
        attempt_no=1,
        attempts_remaining=0,
    )
