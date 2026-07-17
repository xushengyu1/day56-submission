from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.models import AuditEvent
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
    RecordKind,
    RecordStatus,
    ReviewRequestType,
    UserRole,
)
from app.items.models import ItemRecord
from app.items.projections import project_records
from app.items.service import DomainError
from app.matching.models import CandidateMatch
from app.reviews.models import AdminReview, Claim, ClaimAttempt, ReviewRequest
from app.reviews.schemas import (
    ClaimDetail,
    ClaimTimelineEvent,
    ReviewCandidatePublic,
    ReviewDecisionResult,
    ReviewDetail,
    ReviewEvidence,
    ReviewQueueItem,
)


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
    if (
        record.kind is not RecordKind.LOST
        or record.status is not RecordStatus.PUBLISHED
    ):
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


async def get_claim_detail(
    session: AsyncSession,
    *,
    claim_id: UUID,
    actor_id: UUID,
    actor_role: UserRole,
) -> ClaimDetail:
    claim = await session.get(Claim, claim_id)
    if claim is None:
        raise DomainError("NOT_FOUND")
    candidate = await session.get(CandidateMatch, claim.candidate_id)
    if candidate is None:
        raise DomainError("NOT_FOUND")
    found = await session.get(ItemRecord, candidate.found_record_id)
    if found is None or not (
        actor_role is UserRole.ADMIN
        or actor_id == claim.requester_user_id
        or actor_id == found.owner_user_id
    ):
        raise DomainError("NOT_FOUND")
    attempts = (
        await session.scalars(
            select(ClaimAttempt)
            .where(ClaimAttempt.claim_id == claim.id)
            .order_by(ClaimAttempt.attempt_no, ClaimAttempt.created_at)
        )
    ).all()
    events = (
        await session.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.aggregate_type == "claim",
                AuditEvent.aggregate_id == claim.id,
            )
            .order_by(AuditEvent.created_at, AuditEvent.event_id)
        )
    ).all()
    max_attempts = 2 if claim.item_type.value == "IDENTITY_DOCUMENT" else 1
    return ClaimDetail(
        id=claim.id,
        candidate_id=claim.candidate_id,
        requester_user_id=claim.requester_user_id,
        item_type=claim.item_type,
        status=claim.status,
        route_source=claim.route_source,
        result_code=claim.final_reason,
        attempt_count=len(attempts),
        attempts_remaining=max(0, max_attempts - len(attempts)),
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        timeline=[
            ClaimTimelineEvent(
                event_type=event.event_type,
                result_code=event.result_code,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


async def _valid_unmatched_candidate_rows(
    session: AsyncSession, *, lost_record_id: UUID
) -> list[tuple[CandidateMatch, ItemRecord]]:
    lost = await session.get(ItemRecord, lost_record_id)
    if (
        lost is None
        or lost.kind is not RecordKind.LOST
        or lost.status is not RecordStatus.PUBLISHED
    ):
        return []
    rows = await session.execute(
        select(CandidateMatch, ItemRecord)
        .join(ItemRecord, ItemRecord.id == CandidateMatch.found_record_id)
        .where(
            CandidateMatch.lost_record_id == lost_record_id,
            ItemRecord.kind == RecordKind.FOUND,
            ItemRecord.status == RecordStatus.PUBLISHED,
            ItemRecord.item_type == lost.item_type,
            ItemRecord.public_category == lost.public_category,
            ItemRecord.location_area == lost.location_area,
        )
        .order_by(CandidateMatch.total_score.desc(), CandidateMatch.id)
        .limit(5)
    )
    return [(candidate, found) for candidate, found in rows.all()]


async def get_admin_review_detail(
    session: AsyncSession,
    *,
    review_id: UUID,
    actor_id: UUID,
    actor_role: UserRole,
) -> ReviewDetail:
    if actor_role is not UserRole.ADMIN:
        raise AuthorizationError()
    claim = await session.get(Claim, review_id)
    request: ReviewRequest | None = None
    if claim is None:
        request = await session.get(ReviewRequest, review_id)
        if request is None:
            raise DomainError("NOT_FOUND")
        if request.claim_id is not None:
            claim = await session.get(Claim, request.claim_id)

    candidate: CandidateMatch | None = None
    if claim is not None:
        candidate = await session.get(CandidateMatch, claim.candidate_id)
    elif request is not None and request.candidate_snapshot_id is not None:
        candidate = await session.get(CandidateMatch, request.candidate_snapshot_id)

    lost: ItemRecord | None = None
    found: ItemRecord | None = None
    if candidate is not None:
        lost = await session.get(ItemRecord, candidate.lost_record_id)
        found = await session.get(ItemRecord, candidate.found_record_id)
    elif request is not None and request.lost_record_id is not None:
        lost = await session.get(ItemRecord, request.lost_record_id)

    candidate_rows: list[tuple[CandidateMatch, ItemRecord]] = []
    if (
        request is not None
        and request.request_type is ReviewRequestType.UNMATCHED
        and request.active
        and request.lost_record_id is not None
    ):
        candidate_rows = await _valid_unmatched_candidate_rows(
            session, lost_record_id=request.lost_record_id
        )

    records_by_id = {
        record.id: record
        for record in (lost, found, *(row[1] for row in candidate_rows))
        if record is not None
    }
    records = list(records_by_id.values())
    projected = await project_records(session, records, actor_id=actor_id)
    projections = {
        record.id: projection for record, projection in zip(records, projected)
    }
    attempts: list[ClaimAttempt] = []
    if claim is not None:
        attempts = list(
            await session.scalars(
                select(ClaimAttempt)
                .where(ClaimAttempt.claim_id == claim.id)
                .order_by(ClaimAttempt.attempt_no, ClaimAttempt.created_at)
            )
        )
    candidate_public = None
    if candidate is not None and found is not None:
        candidate_public = ReviewCandidatePublic(
            id=candidate.id,
            lost_record_id=candidate.lost_record_id,
            found_record_id=candidate.found_record_id,
            total_score=float(candidate.total_score),
            reason_codes=tuple(candidate.reason_codes),
            conflict_codes=tuple(candidate.conflict_codes),
            found_record=projections[found.id],
            created_at=candidate.created_at,
        )
    source = "CLAIM" if request is None else request.request_type.value
    if request is None:
        if claim is None:
            raise DomainError("NOT_FOUND")
        requester_id = claim.requester_user_id
        status = claim.status.value
        created_at = claim.created_at
    else:
        requester_id = request.requester_user_id
        status = request.status
        created_at = request.created_at
    return ReviewDetail(
        id=review_id,
        source=source,
        item_type=claim.item_type if claim is not None else None,
        status=status,
        route_source=claim.route_source if claim is not None else None,
        result_code=claim.final_reason if claim is not None else None,
        requester_user_id=requester_id,
        reason=request.reason if request is not None else None,
        created_at=created_at,
        lost_record=projections.get(lost.id) if lost is not None else None,
        candidate=candidate_public,
        candidates=[
            ReviewCandidatePublic(
                id=candidate.id,
                lost_record_id=candidate.lost_record_id,
                found_record_id=found_record.id,
                total_score=float(candidate.total_score),
                reason_codes=tuple(candidate.reason_codes),
                conflict_codes=tuple(candidate.conflict_codes),
                found_record=projections[found_record.id],
                created_at=candidate.created_at,
            )
            for candidate, found_record in candidate_rows
        ],
        evidence=[
            ReviewEvidence(
                attempt_no=attempt.attempt_no,
                result_code=attempt.result_code,
                answer_summary=attempt.answer_summary,
                risk_flag=attempt.risk_flag,
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ],
    )


async def decide_review(
    session: AsyncSession,
    *,
    review_id: UUID,
    admin_id: UUID,
    decision: AdminDecision,
    candidate_id: UUID | None,
    reason: str,
    idempotency_key: str,
) -> ReviewDecisionResult:
    admin = await session.get(User, admin_id)
    if admin is None or admin.role is not UserRole.ADMIN:
        raise AuthorizationError()
    if not reason.strip():
        raise DomainError("REASON_REQUIRED")
    request_hash = hash_request(
        {
            "review_id": str(review_id),
            "decision": decision.value,
            "candidate_id": str(candidate_id) if candidate_id else None,
            "reason": reason.strip(),
        }
    )
    replay = await get_idempotent_result(
        session, admin_id, idempotency_key, request_hash
    )
    if replay is not None:
        return ReviewDecisionResult.model_validate(replay.response_body)

    claim = await session.scalar(
        select(Claim).where(Claim.id == review_id).with_for_update()
    )
    request: ReviewRequest | None = None
    if claim is None:
        request = await session.scalar(
            select(ReviewRequest)
            .where(ReviewRequest.id == review_id)
            .with_for_update()
        )
        if request is None:
            raise DomainError("NOT_FOUND")
        if not request.active:
            raise DomainError("REVIEW_STATE_INVALID")
        if request.claim_id is not None:
            claim = await session.scalar(
                select(Claim).where(Claim.id == request.claim_id).with_for_update()
            )

    recommended_candidate: CandidateMatch | None = None
    if request is not None and request.request_type is ReviewRequestType.UNMATCHED:
        if decision not in {AdminDecision.RECOMMEND_CANDIDATE, AdminDecision.REJECT}:
            raise DomainError("DECISION_NOT_ALLOWED")
        if decision is AdminDecision.RECOMMEND_CANDIDATE:
            if candidate_id is None:
                raise DomainError("CANDIDATE_REQUIRED")
            if request.lost_record_id is None:
                raise DomainError("REVIEW_STATE_INVALID")
            candidate_rows = await _valid_unmatched_candidate_rows(
                session, lost_record_id=request.lost_record_id
            )
            recommended_candidate = next(
                (
                    candidate
                    for candidate, _ in candidate_rows
                    if candidate.id == candidate_id
                ),
                None,
            )
            if recommended_candidate is None:
                raise DomainError("CANDIDATE_INVALID")
            request.candidate_snapshot_id = candidate_id
        elif candidate_id is not None:
            raise DomainError("DECISION_NOT_ALLOWED")
        request.active = False
        request.status = "RESOLVED"
        request.resolved_at = datetime.now(timezone.utc)
    else:
        if decision not in {AdminDecision.APPROVE_TO_HANDOFF, AdminDecision.REJECT}:
            raise DomainError("DECISION_NOT_ALLOWED")
        if candidate_id is not None:
            raise DomainError("DECISION_NOT_ALLOWED")
        if claim is None or claim.status is not ClaimStatus.PENDING_ADMIN_REVIEW:
            raise DomainError("REVIEW_STATE_INVALID")
        if decision is AdminDecision.APPROVE_TO_HANDOFF:
            claim.status = ClaimStatus.PENDING_HANDOFF
            matched = await session.get(CandidateMatch, claim.candidate_id)
            if matched is not None:
                lost = await session.get(ItemRecord, matched.lost_record_id)
                found = await session.get(ItemRecord, matched.found_record_id)
                if lost is not None:
                    lost.status = RecordStatus.PENDING_HANDOFF
                if found is not None:
                    found.status = RecordStatus.PENDING_HANDOFF
        else:
            claim.status = ClaimStatus.REJECTED
        claim.final_reason = reason.strip()
        claim.route_source = "ADMIN_REVIEW"
        claim.updated_at = datetime.now(timezone.utc)
        active_requests = (
            await session.scalars(
                select(ReviewRequest).where(
                    ReviewRequest.claim_id == claim.id,
                    ReviewRequest.active.is_(True),
                )
            )
        ).all()
        for active_request in active_requests:
            active_request.active = False
            active_request.status = "RESOLVED"
            active_request.resolved_at = datetime.now(timezone.utc)

    session.add(
        AdminReview(
            review_request_id=request.id if request is not None else None,
            claim_id=claim.id if claim is not None else None,
            reviewer_user_id=admin_id,
            decision=decision,
            reason=reason.strip(),
            evidence_data_class=DataClass.VERIFICATION,
        )
    )
    if claim is not None:
        aggregate_type = "claim"
        aggregate_id = claim.id
        result_status = claim.status.value
    else:
        assert request is not None
        aggregate_type = "review_request"
        aggregate_id = request.id
        result_status = request.status
    append_audit_event(
        session,
        AuditEventInput(
            event_type="ADMIN_REVIEW_DECIDED",
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            actor_type=ActorType.ADMIN,
            actor_id=admin_id,
            result_code=decision.value,
            metadata={"reason_present": True},
        ),
    )
    result = ReviewDecisionResult(
        review_id=review_id,
        claim_id=claim.id if claim is not None else None,
        candidate_id=(
            recommended_candidate.id if recommended_candidate is not None else None
        ),
        status=result_status,
        decision=decision,
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


async def decide_claim_review(
    session: AsyncSession,
    *,
    claim_id: UUID,
    admin_id: UUID,
    decision: AdminDecision,
    reason: str,
    idempotency_key: str,
) -> ReviewDecisionResult:
    return await decide_review(
        session,
        review_id=claim_id,
        admin_id=admin_id,
        decision=decision,
        candidate_id=None,
        reason=reason,
        idempotency_key=idempotency_key,
    )
