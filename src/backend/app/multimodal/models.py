from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ExtractionStatus, ItemType


class AIExtraction(Base):
    __tablename__ = "ai_extractions"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("item_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_result_redacted: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    suggested_item_type: Mapped[ItemType | None] = mapped_column(
        SqlEnum(ItemType, name="item_type")
    )
    draft_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    confidence: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    confirmed_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    status: Mapped[ExtractionStatus] = mapped_column(
        SqlEnum(ExtractionStatus, name="extraction_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
