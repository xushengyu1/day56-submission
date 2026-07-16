"""Create identity secrets and OTHER verification questions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | None = None
depends_on: str | None = None


item_type = postgresql.ENUM(name="item_type", create_type=False)
document_type = postgresql.ENUM(name="document_type", create_type=False)


def upgrade() -> None:
    op.create_table(
        "identity_document_secrets",
        sa.Column("found_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "item_type",
            item_type,
            server_default="IDENTITY_DOCUMENT",
            nullable=False,
        ),
        sa.Column("document_type", document_type, nullable=False),
        sa.Column("number_hmac", sa.LargeBinary(), nullable=False),
        sa.Column("number_masked", sa.String(length=18), nullable=False),
        sa.Column("key_version", sa.SmallInteger(), nullable=False),
        sa.Column("finder_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_type = 'IDENTITY_DOCUMENT'",
            name="ck_identity_document_secrets_identity_document_type",
        ),
        sa.ForeignKeyConstraint(
            ["found_record_id", "item_type"],
            ["item_records.id", "item_records.item_type"],
            ondelete="CASCADE",
            name="fk_identity_secret_record_type",
        ),
        sa.PrimaryKeyConstraint("found_record_id", name="pk_identity_document_secrets"),
    )
    op.create_index(
        "ix_identity_document_secrets_hmac",
        "identity_document_secrets",
        ["number_hmac"],
    )

    op.create_table(
        "verification_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("found_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", item_type, server_default="OTHER", nullable=False),
        sa.Column("hidden_description", sa.Text(), nullable=False),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_type = 'OTHER'", name="ck_verification_sets_other_item_type"
        ),
        sa.ForeignKeyConstraint(
            ["found_record_id", "item_type"],
            ["item_records.id", "item_records.item_type"],
            ondelete="CASCADE",
            name="fk_verification_set_record_type",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_verification_set_confirmer",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_verification_sets"),
        sa.UniqueConstraint("found_record_id", name="uq_verification_sets_record"),
    )

    op.create_table(
        "verification_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_key", sa.Text(), nullable=False),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("provider_model", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["verification_set_id"],
            ["verification_sets.id"],
            ondelete="CASCADE",
            name="fk_verification_question_set",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_verification_question_confirmer",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_verification_questions"),
    )
    op.create_index(
        "ix_verification_questions_verification_set_id",
        "verification_questions",
        ["verification_set_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verification_questions_verification_set_id",
        table_name="verification_questions",
    )
    op.drop_table("verification_questions")
    op.drop_table("verification_sets")
    op.drop_index(
        "ix_identity_document_secrets_hmac",
        table_name="identity_document_secrets",
    )
    op.drop_table("identity_document_secrets")
