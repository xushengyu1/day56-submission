from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import APIError
from app.api.deps import get_current_user
from app.audit.models import AuditEvent
from app.auth.models import User
from app.auth.rbac import AuthorizationError
from app.database import get_database_session
from app.items.service import DomainError
from app.reviews.schemas import AdminDecisionRequest, ReviewDecisionResult, ReviewQueueItem
from app.reviews.service import decide_claim_review, list_admin_review_queue


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/reviews", response_model=list[ReviewQueueItem])
async def review_queue(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[ReviewQueueItem]:
    return await list_admin_review_queue(session, actor_role=user.role)


@router.get("/reviews/{review_id}", response_model=ReviewQueueItem)
async def review_detail(
    review_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> ReviewQueueItem:
    items = await list_admin_review_queue(session, actor_role=user.role)
    for item in items:
        if item.id == review_id:
            return item
    raise APIError("NOT_FOUND")


@router.post("/reviews/{claim_id}/decision", response_model=ReviewDecisionResult)
async def review_decision(
    claim_id: UUID,
    payload: AdminDecisionRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> ReviewDecisionResult:
    try:
        result = await decide_claim_review(
            session,
            claim_id=claim_id,
            admin_id=user.id,
            decision=payload.decision,
            reason=payload.reason,
            idempotency_key=idempotency_key,
        )
        await session.commit()
        return result
    except (DomainError, AuthorizationError):
        await session.rollback()
        raise


@router.get("/audit-events")
async def audit_events(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[dict[str, object]]:
    await list_admin_review_queue(session, actor_role=user.role)
    events = (
        await session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100))
    ).all()
    return [
        {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": str(event.aggregate_id),
            "result_code": event.result_code,
            "metadata_redacted": event.metadata_redacted,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]
