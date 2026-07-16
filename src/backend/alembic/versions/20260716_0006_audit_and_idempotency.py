"""Create append-only audit events and idempotency results."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0006"
down_revision: str | None = "20260716_0005"
branch_labels: str | None = None
depends_on: str | None = None


actor_type = postgresql.ENUM(name="actor_type", create_type=False)


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("actor_type", actor_type, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("rule_version", sa.String(length=64), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("input_snapshot_hash", sa.String(length=64), nullable=True),
        sa.Column("result_code", sa.String(length=64), nullable=False),
        sa.Column("metadata_redacted", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id", name="pk_audit_events"),
    )
    op.create_index(
        "ix_audit_events_timeline",
        "audit_events",
        ["aggregate_type", "aggregate_id", "created_at"],
    )

    op.create_table(
        "idempotency_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_idempotency_actor",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_results"),
        sa.UniqueConstraint(
            "actor_user_id",
            "idempotency_key",
            name="uq_idempotency_actor_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("idempotency_results")
    op.drop_index("ix_audit_events_timeline", table_name="audit_events")
    op.drop_table("audit_events")
