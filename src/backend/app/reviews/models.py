from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import (
    AdminDecision,
    ClaimStatus,
    DataClass,
    ItemType,
    ReviewRequestType,
)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("candidate_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[ItemType] = mapped_column(
        SqlEnum(ItemType, name="item_type"), nullable=False
    )
    status: Mapped[ClaimStatus] = mapped_column(
        SqlEnum(ClaimStatus, name="claim_status"),
        default=ClaimStatus.SUBMITTED,
        server_default=ClaimStatus.SUBMITTED.value,
        nullable=False,
    )
    route_source: Mapped[str | None] = mapped_column(String(64))
    final_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ClaimAttempt(Base):
    __tablename__ = "claim_attempts"
    __table_args__ = (
        UniqueConstraint("claim_id", "attempt_no", name="uq_claim_attempt_number"),
        Index("ix_claim_attempts_lookup", "user_id", "candidate_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    claim_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("candidate_matches.id"), nullable=False
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_hmac: Mapped[bytes | None] = mapped_column(LargeBinary)
    result_code: Mapped[str] = mapped_column(String(256), nullable=False)
    answer_summary: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    risk_flag: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReviewRequest(Base):
    __tablename__ = "review_requests"
    __table_args__ = (
        CheckConstraint(
            "(request_type = 'UNMATCHED' AND lost_record_id IS NOT NULL "
            "AND claim_id IS NULL) OR "
            "(request_type = 'CLAIM_REVIEW' AND lost_record_id IS NULL "
            "AND claim_id IS NOT NULL)",
            name="target_matches_type",
        ),
        Index(
            "uq_review_requests_active_unmatched",
            "requester_user_id",
            "lost_record_id",
            unique=True,
            postgresql_where=text("active AND request_type = 'UNMATCHED'"),
        ),
        Index(
            "uq_review_requests_active_claim",
            "requester_user_id",
            "claim_id",
            unique=True,
            postgresql_where=text("active AND request_type = 'CLAIM_REVIEW'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    requester_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    request_type: Mapped[ReviewRequestType] = mapped_column(
        SqlEnum(ReviewRequestType, name="review_request_type"), nullable=False
    )
    lost_record_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("item_records.id")
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("claims.id")
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", server_default="OPEN", nullable=False
    )
    candidate_snapshot_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("candidate_matches.id")
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminReview(Base):
    __tablename__ = "admin_reviews"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    review_request_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("review_requests.id")
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("claims.id")
    )
    reviewer_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    decision: Mapped[AdminDecision] = mapped_column(
        SqlEnum(AdminDecision, name="admin_decision"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_data_class: Mapped[DataClass] = mapped_column(
        SqlEnum(DataClass, name="data_class"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
