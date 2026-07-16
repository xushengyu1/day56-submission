import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.items.service import DomainError, get_claim_contact


@pytest.mark.asyncio
async def test_only_pending_handoff_requester_can_read_finder_contact(
    handoff_database,
) -> None:
    engine, ids = handoff_database
    async with AsyncSession(engine) as session:
        contact = await get_claim_contact(
            session, claim_id=ids["claim"], requester_id=ids["owner"]
        )
        with pytest.raises(DomainError, match="NOT_FOUND"):
            await get_claim_contact(
                session, claim_id=ids["claim"], requester_id=ids["other"]
            )

    assert contact == {"email": "finder-contact@example.test"}
