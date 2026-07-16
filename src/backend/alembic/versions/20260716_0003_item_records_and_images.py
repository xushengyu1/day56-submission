"""Create item records, images, and AI extraction snapshots."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.db.types import VectorType


revision: str = "20260716_0003"
down_revision: str | None = "20260716_0002"
branch_labels: str | None = None
depends_on: str | None = None


item_type = postgresql.ENUM(name="item_type", create_type=False)
record_kind = postgresql.ENUM(name="record_kind", create_type=False)
record_status = postgresql.ENUM(name="record_status", create_type=False)
data_class = postgresql.ENUM(name="data_class", create_type=False)
image_purpose = postgresql.ENUM(name="image_purpose", create_type=False)
redaction_status = postgresql.ENUM(name="redaction_status", create_type=False)
extraction_status = postgresql.ENUM(name="extraction_status", create_type=False)


def upgrade() -> None:
    op.create_table(
        "item_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", record_kind, nullable=False),
        sa.Column("item_type", item_type, nullable=False),
        sa.Column("status", record_status, server_default="DRAFT", nullable=False),
        sa.Column("name_public", sa.String(length=160), nullable=True),
        sa.Column("description_public", sa.Text(), nullable=True),
        sa.Column("event_time_exact", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_time_public", sa.String(length=160), nullable=True),
        sa.Column("location_public", sa.String(length=255), nullable=True),
        sa.Column("location_normalized", postgresql.JSONB(), nullable=True),
        sa.Column("embedding", VectorType(), nullable=True),
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("ai_extraction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version >= 1", name="ck_item_records_version_positive"),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], ondelete="CASCADE", name="fk_item_owner"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_item_records"),
        sa.UniqueConstraint("id", "item_type", name="uq_item_records_id_item_type"),
    )
    op.create_index("ix_item_records_owner_user_id", "item_records", ["owner_user_id"])
    op.create_index(
        "ix_item_records_match_filter",
        "item_records",
        ["kind", "item_type", "status", "published_at"],
    )

    op.create_table(
        "image_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploader_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", image_purpose, nullable=False),
        sa.Column("data_class", data_class, nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("redaction_status", redaction_status, nullable=False),
        sa.Column("delete_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose != 'PUBLIC_REDACTED' OR "
            "(data_class = 'PUBLIC' AND redaction_status = 'CONFIRMED')",
            name="ck_image_assets_public_redacted_confirmed",
        ),
        sa.CheckConstraint(
            "purpose NOT IN ('FINDER_ORIGINAL', 'OWNER_SUPPORT') "
            "OR data_class = 'PRIVATE'",
            name="ck_image_assets_private_originals",
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["item_records.id"],
            ondelete="CASCADE",
            name="fk_image_record",
        ),
        sa.ForeignKeyConstraint(
            ["uploader_user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_image_uploader",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_assets"),
        sa.UniqueConstraint("object_key", name="uq_image_assets_object_key"),
    )
    op.create_index("ix_image_assets_record_id", "image_assets", ["record_id"])

    op.create_table(
        "ai_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("raw_result_redacted", postgresql.JSONB(), nullable=False),
        sa.Column("suggested_item_type", item_type, nullable=True),
        sa.Column("draft_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", postgresql.JSONB(), nullable=False),
        sa.Column("confirmed_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("status", extraction_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["item_records.id"],
            ondelete="CASCADE",
            name="fk_ai_extraction_record",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_extractions"),
    )
    op.create_index("ix_ai_extractions_record_id", "ai_extractions", ["record_id"])
    op.create_foreign_key(
        "fk_item_records_ai_extraction",
        "item_records",
        "ai_extractions",
        ["ai_extraction_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_item_records_ai_extraction", "item_records", type_="foreignkey"
    )
    op.drop_index("ix_ai_extractions_record_id", table_name="ai_extractions")
    op.drop_table("ai_extractions")
    op.drop_index("ix_image_assets_record_id", table_name="image_assets")
    op.drop_table("image_assets")
    op.drop_index("ix_item_records_match_filter", table_name="item_records")
    op.drop_index("ix_item_records_owner_user_id", table_name="item_records")
    op.drop_table("item_records")
