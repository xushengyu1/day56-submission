from __future__ import annotations

from collections.abc import Mapping
import re
from typing import cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditEventInput
from app.audit.models import AuditEvent
from app.auth.rbac import AuthorizationError
from app.db.enums import UserRole
from app.items.models import ItemRecord
from app.matching.models import CandidateMatch
from app.reviews.models import Claim


_SENSITIVE_KEY_PARTS = (
    "password",
    "token",
    "secret",
    "answer",
    "phone",
    "identity",
    "document_number",
    "authorization",
    "cookie",
    "private",
    "raw_output",
    "contact",
)
_IDENTITY_RE = re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)")
_PHONE_RE = re.compile(r"(?<!\d)1\d{10}(?!\d)")
_JWT_RE = re.compile(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


def _sensitive_key(key: str) -> bool:
    normalized = key.casefold()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_string(value: str) -> str:
    if _IDENTITY_RE.search(value) or _PHONE_RE.search(value) or _JWT_RE.search(value):
        return "[REDACTED]"
    if "private/" in value.casefold() or value.casefold().startswith("file:"):
        return "[REDACTED]"
    return value


def redact_metadata(value: object, *, _key: str | None = None) -> object:
    """Return a recursively copied JSON-like value with sensitive data removed."""

    if _key is not None and _sensitive_key(_key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            str(key): redact_metadata(item, _key=str(key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_metadata(item) for item in value]
    if isinstance(value, tuple):
        return [redact_metadata(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def project_audit_event(event: AuditEventInput) -> dict[str, object]:
    return {
        "event_id": None,
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": str(event.aggregate_id),
        "actor_type": event.actor_type.value,
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "request_id": event.request_id,
        "result_code": event.result_code,
        "metadata_redacted": cast(dict[str, object], redact_metadata(event.metadata)),
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


async def get_record_timeline(
    session: AsyncSession,
    *,
    record_id: UUID,
    actor_id: UUID,
    actor_role: UserRole,
) -> list[dict[str, object]]:
    record = await session.get(ItemRecord, record_id)
    if record is None:
        raise AuthorizationError()
    related_claim_ids = (
        await session.scalars(
            select(Claim.id)
            .join(CandidateMatch, CandidateMatch.id == Claim.candidate_id)
            .where(
                or_(
                    CandidateMatch.lost_record_id == record_id,
                    CandidateMatch.found_record_id == record_id,
                )
            )
        )
    ).all()
    requester_related = await session.scalar(
        select(Claim.id)
        .join(CandidateMatch, CandidateMatch.id == Claim.candidate_id)
        .where(
            Claim.requester_user_id == actor_id,
            or_(
                CandidateMatch.lost_record_id == record_id,
                CandidateMatch.found_record_id == record_id,
            ),
        )
        .limit(1)
    )
    if (
        actor_role is not UserRole.ADMIN
        and record.owner_user_id != actor_id
        and requester_related is None
    ):
        raise AuthorizationError()
    aggregate_ids = [record_id, *related_claim_ids]
    events = (
        await session.scalars(
            select(AuditEvent)
            .where(AuditEvent.aggregate_id.in_(aggregate_ids))
            .order_by(AuditEvent.created_at, AuditEvent.event_id)
        )
    ).all()
    timeline: list[dict[str, object]] = []
    for event in events:
        metadata = dict(event.metadata_redacted)
        if actor_role is not UserRole.ADMIN:
            metadata = {
                key: value
                for key, value in metadata.items()
                if not any(part in key.casefold() for part in ("admin", "private", "internal"))
            }
        timeline.append(
            {
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "result_code": event.result_code,
                "metadata": metadata,
                "created_at": event.created_at.isoformat(),
            }
        )
    return timeline
