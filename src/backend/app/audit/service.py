from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.audit.projection import redact_metadata
from app.audit.schemas import AuditEventInput


def append_audit_event(session: AsyncSession, event: AuditEventInput) -> AuditEvent:
    """Add one redacted append-only event to the caller's current transaction."""

    model = AuditEvent(
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        request_id=event.request_id,
        rule_version=event.rule_version,
        model_version=event.model_version,
        input_snapshot_hash=event.input_snapshot_hash,
        result_code=event.result_code,
        metadata_redacted=redact_metadata(event.metadata),
    )
    if event.created_at is not None:
        model.created_at = event.created_at
    session.add(model)
    return model
