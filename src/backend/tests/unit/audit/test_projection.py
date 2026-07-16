from datetime import datetime, timezone
from uuid import uuid4

from app.audit.schemas import AuditEventInput
from app.audit.projection import project_audit_event
from app.db.enums import ActorType


def test_projection_contains_trace_fields_and_redacted_metadata() -> None:
    event = AuditEventInput(
        event_type="CLAIM_SUBMITTED",
        aggregate_type="claim",
        aggregate_id=uuid4(),
        actor_type=ActorType.OWNER,
        actor_id=uuid4(),
        request_id="req-123",
        result_code="OK",
        metadata={"answer": "private answer", "reason_code": "MATCH"},
        created_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
    )

    projected = project_audit_event(event)

    assert projected["event_type"] == "CLAIM_SUBMITTED"
    assert projected["request_id"] == "req-123"
    assert projected["metadata_redacted"] == {
        "answer": "[REDACTED]",
        "reason_code": "MATCH",
    }
