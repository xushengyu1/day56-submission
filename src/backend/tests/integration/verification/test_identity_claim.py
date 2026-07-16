import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus
from app.verification.service import submit_identity_claim


@pytest.mark.asyncio
async def test_unique_exact_identity_match_enters_pending_handoff(
    identity_claim_database,
) -> None:
    engine, ids = identity_claim_database
    async with AsyncSession(engine) as session:
        result = await submit_identity_claim(
            session,
            candidate_id=ids["candidate"],
            requester_id=ids["owner"],
            full_number=ids["valid_id"],
            hmac_key=ids["hmac_key"],
        )
        await session.commit()

    assert result.status is ClaimStatus.PENDING_HANDOFF
    assert result.result_code == "IDENTITY_VERIFIED"
    assert result.attempt_no == 1
