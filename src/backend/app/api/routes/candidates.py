from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.matching.schemas import CandidatePublic
from app.matching.service import get_candidate


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("/{candidate_id}", response_model=CandidatePublic)
async def candidate_detail(
    candidate_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> CandidatePublic:
    return await get_candidate(session, candidate_id, user.id)
