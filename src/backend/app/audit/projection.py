from __future__ import annotations

from collections.abc import Mapping
import re
from typing import cast

from app.audit.schemas import AuditEventInput, AuditEventView


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
