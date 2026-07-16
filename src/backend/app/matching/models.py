from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"
    __table_args__ = (
        Index(
            "ix_candidate_matches_top5",
            "lost_record_id",
            text("total_score DESC"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    lost_record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("item_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    found_record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("item_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    semantic_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    time_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    location_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    completeness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    conflict_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)
    input_snapshot_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
