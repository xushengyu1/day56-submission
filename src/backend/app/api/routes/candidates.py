from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.service import DomainError
from app.matching.schemas import CandidatePublic
from app.matching.service import get_candidate


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("/{candidate_id}", response_model=CandidatePublic)
async def candidate_detail(
    candidate_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> CandidatePublic:
    try:
        return await get_candidate(session, candidate_id, user.id)
    except DomainError as error:
        status_code = 403 if error.code == "NOT_OWNER" else 404
        raise HTTPException(status_code, error.code) from None
