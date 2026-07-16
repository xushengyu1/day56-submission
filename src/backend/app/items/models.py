from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ItemType, RecordKind, RecordStatus
from app.db.types import VectorType


class ItemRecord(Base):
    __tablename__ = "item_records"
    __table_args__ = (
        UniqueConstraint("id", "item_type", name="uq_item_records_id_item_type"),
        CheckConstraint("version >= 1", name="version_positive"),
        Index(
            "ix_item_records_match_filter",
            "kind",
            "item_type",
            "status",
            "published_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[RecordKind] = mapped_column(
        SqlEnum(RecordKind, name="record_kind"), nullable=False
    )
    item_type: Mapped[ItemType] = mapped_column(
        SqlEnum(ItemType, name="item_type"), nullable=False
    )
    status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus, name="record_status"),
        default=RecordStatus.DRAFT,
        server_default=RecordStatus.DRAFT.value,
        nullable=False,
    )
    name_public: Mapped[str | None] = mapped_column(String(160))
    description_public: Mapped[str | None] = mapped_column(Text)
    event_time_exact: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    event_time_public: Mapped[str | None] = mapped_column(String(160))
    location_public: Mapped[str | None] = mapped_column(String(255))
    location_normalized: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(VectorType())
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    ai_extraction_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            "ai_extractions.id",
            name="fk_item_records_ai_extraction",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
