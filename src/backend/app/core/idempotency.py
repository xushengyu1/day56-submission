from __future__ import annotations

import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import IdempotencyResult
from app.audit.projection import redact_metadata


class IdempotencyConflict(ValueError):
    def __init__(self) -> None:
        super().__init__("IDEMPOTENCY_KEY_REUSED")
        self.code = "IDEMPOTENCY_KEY_REUSED"


def hash_request(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def get_idempotent_result(
    session: AsyncSession,
    actor_id: UUID,
    idempotency_key: str,
    request_hash: str,
) -> IdempotencyResult | None:
    result = await session.scalar(
        select(IdempotencyResult).where(
            IdempotencyResult.actor_user_id == actor_id,
            IdempotencyResult.idempotency_key == idempotency_key,
        )
    )
    if result is None:
        return None
    if result.request_hash != request_hash:
        raise IdempotencyConflict()
    return result


def store_idempotent_result(
    session: AsyncSession,
    actor_id: UUID,
    idempotency_key: str,
    request_hash: str,
    response_status: int,
    response_body: dict[str, object],
) -> IdempotencyResult:
    result = IdempotencyResult(
        actor_user_id=actor_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_status=response_status,
        response_body=redact_metadata(response_body),
    )
    session.add(result)
    return result
