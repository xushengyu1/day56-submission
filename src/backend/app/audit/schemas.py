from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.db.enums import ActorType


@dataclass(frozen=True)
class AuditEventInput:
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    actor_type: ActorType
    actor_id: UUID | None = None
    request_id: str | None = None
    rule_version: str | None = None
    model_version: str | None = None
    input_snapshot_hash: str | None = None
    result_code: str = "OK"
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True)
class AuditEventView:
    event_id: UUID | None
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    actor_type: ActorType
    actor_id: UUID | None
    request_id: str | None
    result_code: str
    metadata_redacted: dict[str, object]
    created_at: datetime | None
