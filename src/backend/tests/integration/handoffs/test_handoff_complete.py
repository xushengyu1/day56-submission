import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.db.enums import ClaimStatus, RecordStatus
from app.items.models import ItemRecord
from app.items.service import complete_handoff
from app.reviews.models import Claim


@pytest.mark.asyncio
async def test_finder_completes_handoff_idempotently(handoff_database) -> None:
    engine, ids = handoff_database
    async with AsyncSession(engine) as session:
        first = await complete_handoff(
            session,
            claim_id=ids["claim"],
            finder_id=ids["finder"],
            confirmation=True,
            idempotency_key="handoff-key-1",
        )
        await session.commit()
    async with AsyncSession(engine) as session:
        second = await complete_handoff(
            session,
            claim_id=ids["claim"],
            finder_id=ids["finder"],
            confirmation=True,
            idempotency_key="handoff-key-1",
        )
        await session.commit()
        claim = await session.get(Claim, ids["claim"])
        found = await session.get(ItemRecord, ids["found"])
        events = await session.scalar(
            select(func.count(AuditEvent.event_id)).where(
                AuditEvent.event_type == "HANDOFF_COMPLETED"
            )
        )

    assert first == second
    assert claim is not None
    assert found is not None
    assert claim.status is ClaimStatus.CLAIMED
    assert found.status is RecordStatus.CLAIMED
    assert events == 1
