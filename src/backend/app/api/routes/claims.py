from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.service import DomainError
from app.settings import settings
from app.verification.schemas import ClaimOutcome, IdentityClaimRequest
from app.verification.service import submit_identity_claim


router = APIRouter(prefix="/api/candidates", tags=["claims"])


@router.post("/{candidate_id}/claims/identity", response_model=ClaimOutcome)
async def identity_claim(
    candidate_id: UUID,
    payload: IdentityClaimRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> ClaimOutcome:
    try:
        result = await submit_identity_claim(
            session,
            candidate_id=candidate_id,
            requester_id=user.id,
            full_number=payload.full_number,
            hmac_key=settings.id_hmac_key_v1.encode("utf-8"),
        )
        await session.commit()
        return result
    except DomainError as error:
        await session.rollback()
        status_code = 404 if error.code == "NOT_FOUND" else 423 if error.code == "ATTEMPT_LOCKED" else 400
        raise HTTPException(status_code, error.code) from None
