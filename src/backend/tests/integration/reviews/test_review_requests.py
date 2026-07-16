import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.items.service import DomainError
from app.reviews.service import create_claim_review_request, create_unmatched_review_request


@pytest.mark.asyncio
async def test_owner_can_create_one_active_unmatched_and_claim_review(review_database) -> None:
    engine, ids = review_database
    async with AsyncSession(engine) as session:
        unmatched = await create_unmatched_review_request(
            session, lost_record_id=ids["lost"], requester_id=ids["owner"], reason="没有合适候选"
        )
        claim_review = await create_claim_review_request(
            session, claim_id=ids["claim"], requester_id=ids["owner"], reason="请求人工复核"
        )
        await session.flush()
        assert unmatched.active and claim_review.active
        with pytest.raises(DomainError, match="ACTIVE_REVIEW_EXISTS"):
            await create_claim_review_request(
                session, claim_id=ids["claim"], requester_id=ids["owner"], reason="重复"
            )
