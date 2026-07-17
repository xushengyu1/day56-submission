from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.service import DomainError
from app.multimodal.factory import get_multimodal_adapter
from app.multimodal.ports import MultimodalPort
from app.settings import settings
from app.reviews.schemas import ReviewRequestCreate
from app.reviews.service import create_claim_review_request
from app.verification.schemas import (
    ClaimOutcome,
    IdentityClaimRequest,
    OtherClaimRequest,
    QuestionPublic,
)
from app.verification.service import (
    get_other_questions,
    submit_identity_claim,
    submit_other_claim,
)


router = APIRouter(prefix="/api/candidates", tags=["claims"])
claim_review_router = APIRouter(prefix="/api/claims", tags=["claims"])


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
    except DomainError:
        await session.rollback()
        raise


@router.get("/{candidate_id}/questions", response_model=list[QuestionPublic])
async def other_questions(
    candidate_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[QuestionPublic]:
    return await get_other_questions(
        session, candidate_id=candidate_id, requester_id=user.id
    )


@router.post("/{candidate_id}/claims/answers", response_model=ClaimOutcome)
async def other_claim(
    candidate_id: UUID,
    payload: OtherClaimRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    adapter: MultimodalPort = Depends(get_multimodal_adapter),
) -> ClaimOutcome:
    try:
        result = await submit_other_claim(
            session,
            candidate_id=candidate_id,
            requester_id=user.id,
            answers={answer.question_id: answer.answer for answer in payload.answers},
            adapter=adapter,
        )
        await session.commit()
        return result
    except DomainError:
        await session.rollback()
        raise


@claim_review_router.post("/{claim_id}/review-requests")
async def claim_review_request(
    claim_id: UUID,
    payload: ReviewRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    try:
        request = await create_claim_review_request(
            session,
            claim_id=claim_id,
            requester_id=user.id,
            reason=payload.reason,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {"id": str(request.id), "status": request.status}
