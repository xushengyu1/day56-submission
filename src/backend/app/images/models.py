from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import DataClass, ImagePurpose, RedactionStatus


class ImageAsset(Base):
    __tablename__ = "image_assets"
    __table_args__ = (
        CheckConstraint(
            "purpose != 'PUBLIC_REDACTED' OR "
            "(data_class = 'PUBLIC' AND redaction_status = 'CONFIRMED')",
            name="public_redacted_confirmed",
        ),
        CheckConstraint(
            "purpose NOT IN ('FINDER_ORIGINAL', 'OWNER_SUPPORT') "
            "OR data_class = 'PRIVATE'",
            name="private_originals",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    record_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("item_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploader_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose: Mapped[ImagePurpose] = mapped_column(
        SqlEnum(ImagePurpose, name="image_purpose"), nullable=False
    )
    data_class: Mapped[DataClass] = mapped_column(
        SqlEnum(DataClass, name="data_class"), nullable=False
    )
    object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    redaction_status: Mapped[RedactionStatus] = mapped_column(
        SqlEnum(RedactionStatus, name="redaction_status"), nullable=False
    )
    delete_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
