from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.service import append_audit_event
from app.auth.models import User
from app.auth.rbac import AuthorizationError
from app.core.idempotency import (
    get_idempotent_result,
    hash_request,
    store_idempotent_result,
)
from app.db.enums import (
    ActorType,
    AdminDecision,
    ClaimStatus,
    DataClass,
    RecordStatus,
    ReviewRequestType,
    UserRole,
)
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.matching.models import CandidateMatch
from app.reviews.models import AdminReview, Claim, ReviewRequest
from app.reviews.schemas import ReviewDecisionResult, ReviewQueueItem


async def create_unmatched_review_request(
    session: AsyncSession,
    *,
    lost_record_id: UUID,
    requester_id: UUID,
    reason: str,
) -> ReviewRequest:
    record = await session.get(ItemRecord, lost_record_id)
    if record is None or record.owner_user_id != requester_id:
        raise DomainError("NOT_FOUND")
    existing = await session.scalar(
        select(ReviewRequest).where(
            ReviewRequest.requester_user_id == requester_id,
            ReviewRequest.lost_record_id == lost_record_id,
            ReviewRequest.active.is_(True),
        )
    )
    if existing is not None:
        raise DomainError("ACTIVE_REVIEW_EXISTS")
    request = ReviewRequest(
        requester_user_id=requester_id,
        request_type=ReviewRequestType.UNMATCHED,
        lost_record_id=lost_record_id,
        reason=reason.strip(),
    )
    session.add(request)
    return request


async def create_claim_review_request(
    session: AsyncSession,
    *,
    claim_id: UUID,
    requester_id: UUID,
    reason: str,
) -> ReviewRequest:
    claim = await session.get(Claim, claim_id)
    if claim is None or claim.requester_user_id != requester_id:
        raise DomainError("NOT_FOUND")
    existing = await session.scalar(
        select(ReviewRequest).where(
            ReviewRequest.requester_user_id == requester_id,
            ReviewRequest.claim_id == claim_id,
            ReviewRequest.active.is_(True),
        )
    )
    if existing is not None:
        raise DomainError("ACTIVE_REVIEW_EXISTS")
    request = ReviewRequest(
        requester_user_id=requester_id,
        request_type=ReviewRequestType.CLAIM_REVIEW,
        claim_id=claim_id,
        reason=reason.strip(),
    )
    session.add(request)
    return request


async def list_admin_review_queue(
    session: AsyncSession, *, actor_role: UserRole
) -> list[ReviewQueueItem]:
    if actor_role is not UserRole.ADMIN:
        raise AuthorizationError()
    claims = (
        await session.scalars(
            select(Claim)
            .where(Claim.status == ClaimStatus.PENDING_ADMIN_REVIEW)
            .order_by(Claim.created_at)
        )
    ).all()
    requests = (
        await session.scalars(
            select(ReviewRequest)
            .where(ReviewRequest.active.is_(True))
            .order_by(ReviewRequest.created_at)
        )
    ).all()
    items = [
        ReviewQueueItem(
            id=claim.id,
            source="CLAIM",
            item_type=claim.item_type,
            status=claim.status.value,
            route_source=claim.route_source,
            result_code=claim.final_reason,
            created_at=claim.created_at,
        )
        for claim in claims
    ]
    items.extend(
        ReviewQueueItem(
            id=request.id,
            source=request.request_type.value,
            item_type=None,
            status=request.status,
            result_code=None,
            created_at=request.created_at,
        )
        for request in requests
    )
    return items


async def decide_claim_review(
    session: AsyncSession,
    *,
    claim_id: UUID,
    admin_id: UUID,
    decision: AdminDecision,
    reason: str,
    idempotency_key: str,
) -> ReviewDecisionResult:
    admin = await session.get(User, admin_id)
    if admin is None or admin.role is not UserRole.ADMIN:
        raise AuthorizationError()
    if not reason.strip():
        raise DomainError("REASON_REQUIRED")
    request_hash = hash_request(
        {"claim_id": str(claim_id), "decision": decision.value, "reason": reason.strip()}
    )
    replay = await get_idempotent_result(
        session, admin_id, idempotency_key, request_hash
    )
    if replay is not None:
        return ReviewDecisionResult.model_validate(replay.response_body)

    claim = await session.scalar(
        select(Claim).where(Claim.id == claim_id).with_for_update()
    )
    if claim is None:
        raise DomainError("NOT_FOUND")
    if claim.status is not ClaimStatus.PENDING_ADMIN_REVIEW:
        raise DomainError("REVIEW_STATE_INVALID")
    if decision is AdminDecision.APPROVE_TO_HANDOFF:
        claim.status = ClaimStatus.PENDING_HANDOFF
        candidate = await session.get(CandidateMatch, claim.candidate_id)
        if candidate is not None:
            lost = await session.get(ItemRecord, candidate.lost_record_id)
            found = await session.get(ItemRecord, candidate.found_record_id)
            if lost is not None:
                lost.status = RecordStatus.PENDING_HANDOFF
            if found is not None:
                found.status = RecordStatus.PENDING_HANDOFF
    else:
        claim.status = ClaimStatus.REJECTED
    claim.final_reason = reason.strip()
    claim.route_source = "ADMIN_REVIEW"
    claim.updated_at = datetime.now(timezone.utc)
    session.add(
        AdminReview(
            claim_id=claim.id,
            reviewer_user_id=admin_id,
            decision=decision,
            reason=reason.strip(),
            evidence_data_class=DataClass.VERIFICATION,
        )
    )
    active_requests = (
        await session.scalars(
            select(ReviewRequest).where(
                ReviewRequest.claim_id == claim.id, ReviewRequest.active.is_(True)
            )
        )
    ).all()
    for request in active_requests:
        request.active = False
        request.status = "RESOLVED"
        request.resolved_at = datetime.now(timezone.utc)
    append_audit_event(
        session,
        AuditEventInput(
            event_type="ADMIN_REVIEW_DECIDED",
            aggregate_type="claim",
            aggregate_id=claim.id,
            actor_type=ActorType.ADMIN,
            actor_id=admin_id,
            result_code=decision.value,
            metadata={"reason_present": True},
        ),
    )
    result = ReviewDecisionResult(
        claim_id=claim.id, status=claim.status, decision=decision
    )
    store_idempotent_result(
        session,
        admin_id,
        idempotency_key,
        request_hash,
        200,
        result.model_dump(mode="json"),
    )
    return result
