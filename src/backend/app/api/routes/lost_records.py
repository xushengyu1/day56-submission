from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.service import DomainError
from app.matching.schemas import CandidatePublic, LostRecordCreate
from app.matching.service import create_lost_record, generate_candidates, list_candidates


router = APIRouter(prefix="/api/lost-records", tags=["lost-records"])


def _error(error: DomainError) -> HTTPException:
    return HTTPException(
        status_code=403 if error.code == "NOT_OWNER" else 404 if error.code == "NOT_FOUND" else 400,
        detail=error.code,
    )


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
    except DomainError as error:
        await session.rollback()
        raise _error(error) from None
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
    try:
        return await list_candidates(session, record_id, user.id)
    except DomainError as error:
        raise _error(error) from None
