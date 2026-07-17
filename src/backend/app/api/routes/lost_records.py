from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.service import DomainError
from app.matching.schemas import CandidatePublic, LostRecordCreate
from app.matching.service import create_lost_record, generate_candidates, list_candidates
from app.reviews.schemas import ReviewRequestCreate
from app.reviews.service import create_unmatched_review_request


router = APIRouter(prefix="/api/lost-records", tags=["lost-records"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lost(
    payload: LostRecordCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        record = await create_lost_record(
            session, owner_user_id=user.id, **payload.model_dump()
        )
        await session.flush()
        candidates = await generate_candidates(session, lost_record=record)
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {
        "id": str(record.id),
        "status": record.status.value,
        "candidate_count": len(candidates),
    }


@router.get("/{record_id}/candidates", response_model=list[CandidatePublic])
async def candidate_list(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[CandidatePublic]:
    return await list_candidates(session, record_id, user.id)


@router.post("/{record_id}/review-requests", status_code=status.HTTP_201_CREATED)
async def unmatched_review_request(
    record_id: UUID,
    payload: ReviewRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    try:
        request = await create_unmatched_review_request(
            session,
            lost_record_id=record_id,
            requester_id=user.id,
            reason=payload.reason,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {"id": str(request.id), "status": request.status}
