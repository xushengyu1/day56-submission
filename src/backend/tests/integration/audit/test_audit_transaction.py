from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.audit.schemas import AuditEventInput
from app.audit.service import append_audit_event
from app.db.enums import ActorType


@pytest.mark.asyncio
async def test_audit_event_commits_with_transaction(audit_database) -> None:
    engine, actor_id, _ = audit_database
    aggregate_id = uuid4()
    async with AsyncSession(engine) as session:
        append_audit_event(
            session,
            AuditEventInput(
                event_type="TEST_COMMITTED",
                aggregate_type="test",
                aggregate_id=aggregate_id,
                actor_type=ActorType.OWNER,
                actor_id=actor_id,
                metadata={"identity_number": "110101200001010010", "safe": "ok"},
            ),
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        event = await session.scalar(
            select(AuditEvent).where(AuditEvent.aggregate_id == aggregate_id)
        )

    assert event is not None
    assert event.metadata_redacted == {"identity_number": "[REDACTED]", "safe": "ok"}


@pytest.mark.asyncio
async def test_audit_event_rolls_back_with_business_transaction(audit_database) -> None:
    engine, actor_id, _ = audit_database
    aggregate_id = uuid4()
    async with AsyncSession(engine) as session:
        append_audit_event(
            session,
            AuditEventInput(
                event_type="TEST_ROLLED_BACK",
                aggregate_type="test",
                aggregate_id=aggregate_id,
                actor_type=ActorType.OWNER,
                actor_id=actor_id,
            ),
        )
        await session.rollback()

    async with AsyncSession(engine) as session:
        assert await session.scalar(
            select(AuditEvent).where(AuditEvent.aggregate_id == aggregate_id)
        ) is None
