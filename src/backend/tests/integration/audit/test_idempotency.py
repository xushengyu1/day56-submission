import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User  # noqa: F401 - registers the FK target metadata
from app.core.idempotency import (
    IdempotencyConflict,
    get_idempotent_result,
    hash_request,
    store_idempotent_result,
)


@pytest.mark.asyncio
async def test_same_actor_and_key_replays_result_and_conflicting_body_fails(
    audit_database,
) -> None:
    engine, actor_id, _ = audit_database
    request_hash = hash_request({"decision": "APPROVE"})
    async with AsyncSession(engine) as session:
        store_idempotent_result(
            session,
            actor_id,
            "key-1",
            request_hash,
            200,
            {"status": "PENDING_HANDOFF", "token": "secret"},
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        result = await get_idempotent_result(session, actor_id, "key-1", request_hash)
        assert result is not None
        assert result.response_body == {"status": "PENDING_HANDOFF", "token": "[REDACTED]"}
        with pytest.raises(IdempotencyConflict, match="IDEMPOTENCY_KEY_REUSED"):
            await get_idempotent_result(
                session, actor_id, "key-1", hash_request({"decision": "REJECT"})
            )


@pytest.mark.asyncio
async def test_same_key_can_be_used_by_different_actor(audit_database) -> None:
    engine, actor_id, other_actor_id = audit_database
    request_hash = hash_request({"decision": "APPROVE"})
    async with AsyncSession(engine) as session:
        store_idempotent_result(session, actor_id, "key-2", request_hash, 200, {})
        store_idempotent_result(
            session, other_actor_id, "key-2", request_hash, 200, {}
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        assert await get_idempotent_result(
            session, other_actor_id, "key-2", request_hash
        ) is not None
