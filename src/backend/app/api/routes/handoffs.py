from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.items.schemas import HandoffCompleteRequest, HandoffResult
from app.items.service import DomainError, complete_handoff, get_claim_contact


router = APIRouter(prefix="/api/claims", tags=["handoffs"])


@router.get("/{claim_id}/contact")
async def claim_contact(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    try:
        return await get_claim_contact(
            session, claim_id=claim_id, requester_id=user.id
        )
    except DomainError as error:
        raise HTTPException(404, error.code) from None


@router.post("/{claim_id}/handoff-complete", response_model=HandoffResult)
async def handoff_complete(
    claim_id: UUID,
    payload: HandoffCompleteRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> HandoffResult:
    try:
        result = await complete_handoff(
            session,
            claim_id=claim_id,
            finder_id=user.id,
            confirmation=payload.confirmation,
            idempotency_key=idempotency_key,
        )
        await session.commit()
        return result
    except DomainError as error:
        await session.rollback()
        status_code = 404 if error.code == "NOT_FOUND" else 403 if error.code == "NOT_FINDER" else 400
        raise HTTPException(status_code, error.code) from None
