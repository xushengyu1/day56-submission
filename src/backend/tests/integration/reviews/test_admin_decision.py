import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import AdminDecision, ClaimStatus
from app.reviews.models import AdminReview, Claim
from app.reviews.service import decide_claim_review


@pytest.mark.asyncio
async def test_admin_decision_is_idempotent_and_only_moves_to_handoff(review_database) -> None:
    engine, ids = review_database
    async with AsyncSession(engine) as session:
        first = await decide_claim_review(
            session,
            claim_id=ids["claim"],
            admin_id=ids["admin"],
            decision=AdminDecision.APPROVE_TO_HANDOFF,
            reason="证据充分",
            idempotency_key="decision-key-1",
        )
        await session.commit()
    async with AsyncSession(engine) as session:
        second = await decide_claim_review(
            session,
            claim_id=ids["claim"],
            admin_id=ids["admin"],
            decision=AdminDecision.APPROVE_TO_HANDOFF,
            reason="证据充分",
            idempotency_key="decision-key-1",
        )
        await session.commit()
        count = await session.scalar(select(func.count(AdminReview.id)))
        claim = await session.get(Claim, ids["claim"])

    assert first == second
    assert count == 1
    assert claim is not None
    assert claim.status is ClaimStatus.PENDING_HANDOFF
