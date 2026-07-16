import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus
from app.reviews.models import ClaimAttempt
from app.verification.service import submit_identity_claim


@pytest.mark.asyncio
async def test_two_concurrent_failures_create_exactly_two_attempts_and_lock(
    identity_claim_database,
) -> None:
    engine, ids = identity_claim_database

    async def attempt():
        async with AsyncSession(engine) as session:
            result = await submit_identity_claim(
                session,
                candidate_id=ids["candidate"],
                requester_id=ids["owner"],
                full_number=ids["wrong_id"],
                hmac_key=ids["hmac_key"],
            )
            await session.commit()
            return result

    results = await asyncio.gather(attempt(), attempt())

    async with AsyncSession(engine) as session:
        count = await session.scalar(select(func.count(ClaimAttempt.id)))
    assert count == 2
    assert sorted(result.attempt_no for result in results) == [1, 2]
    assert any(result.status is ClaimStatus.LOCKED for result in results)
