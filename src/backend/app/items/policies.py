from __future__ import annotations

from app.db.enums import ItemType
from app.items.models import ItemRecord


def validate_common_publish_fields(record: ItemRecord) -> tuple[str, ...]:
    missing = []
    if not record.name_public or not record.name_public.strip():
        missing.append("name_public")
    if not record.description_public or not record.description_public.strip():
        missing.append("description_public")
    if record.event_time_exact is None:
        missing.append("event_time")
    if not record.location_public or not record.location_public.strip():
        missing.append("location_public")
    return tuple(missing)


def subtype_requirement(item_type: ItemType) -> str:
    if item_type is ItemType.IDENTITY_DOCUMENT:
        return "identity_document_secret"
    return "verification_set"
