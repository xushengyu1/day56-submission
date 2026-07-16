from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import DocumentType, ItemType


class IdentityDocumentSecret(Base):
    __tablename__ = "identity_document_secrets"
    __table_args__ = (
        CheckConstraint(
            "item_type = 'IDENTITY_DOCUMENT'", name="identity_document_type"
        ),
        Index("ix_identity_document_secrets_hmac", "number_hmac"),
        ForeignKeyConstraint(
            ["found_record_id", "item_type"],
            ["item_records.id", "item_records.item_type"],
            name="fk_identity_secret_record_type",
            ondelete="CASCADE",
        ),
    )

    found_record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True
    )
    item_type: Mapped[ItemType] = mapped_column(
        SqlEnum(ItemType, name="item_type"),
        default=ItemType.IDENTITY_DOCUMENT,
        server_default=ItemType.IDENTITY_DOCUMENT.value,
        nullable=False,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SqlEnum(DocumentType, name="document_type"), nullable=False
    )
    number_hmac: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    number_masked: Mapped[str] = mapped_column(String(18), nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    finder_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class VerificationSet(Base):
    __tablename__ = "verification_sets"
    __table_args__ = (
        UniqueConstraint("found_record_id", name="uq_verification_sets_record"),
        CheckConstraint("item_type = 'OTHER'", name="other_item_type"),
        ForeignKeyConstraint(
            ["found_record_id", "item_type"],
            ["item_records.id", "item_records.item_type"],
            name="fk_verification_set_record_type",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    found_record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False
    )
    item_type: Mapped[ItemType] = mapped_column(
        SqlEnum(ItemType, name="item_type"),
        default=ItemType.OTHER,
        server_default=ItemType.OTHER.value,
        nullable=False,
    )
    hidden_description: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_by: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class VerificationQuestion(Base):
    __tablename__ = "verification_questions"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    verification_set_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("verification_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_key: Mapped[str] = mapped_column(Text, nullable=False)
    dimension: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_model: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmed_by: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
