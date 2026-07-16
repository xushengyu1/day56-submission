from __future__ import annotations

from datetime import datetime, timezone
import hmac
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.service import append_audit_event
from app.auth.models import User  # noqa: F401 - register FK metadata
from app.db.enums import ActorType, ClaimStatus, ItemType, RecordStatus
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.matching.models import CandidateMatch
from app.reviews.models import Claim, ClaimAttempt
from app.verification.identity import compute_id_hmac, normalize_cn_id
from app.verification.models import IdentityDocumentSecret
from app.verification.schemas import ClaimOutcome


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
    append_audit_event(
        session,
        AuditEventInput(
            event_type="IDENTITY_CLAIM_ATTEMPTED",
            aggregate_type="claim",
            aggregate_id=claim.id,
            actor_type=ActorType.OWNER,
            actor_id=requester_id,
            result_code=result_code,
            metadata={"attempt_no": attempt_no, "route_source": claim.route_source},
        ),
    )
    return ClaimOutcome(
        claim_id=claim.id,
        status=claim.status,
        result_code=result_code,
        attempt_no=attempt_no,
    )
