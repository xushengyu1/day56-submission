"""Create candidates, claims, attempts, and review requests."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0005"
down_revision: str | None = "20260716_0004"
branch_labels: str | None = None
depends_on: str | None = None


item_type = postgresql.ENUM(name="item_type", create_type=False)
claim_status = postgresql.ENUM(name="claim_status", create_type=False)
review_request_type = postgresql.ENUM(name="review_request_type", create_type=False)
admin_decision = postgresql.ENUM(name="admin_decision", create_type=False)
data_class = postgresql.ENUM(name="data_class", create_type=False)


def upgrade() -> None:
    op.create_table(
        "candidate_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lost_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("found_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semantic_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("time_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("location_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("completeness_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("total_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason_codes", postgresql.JSONB(), nullable=False),
        sa.Column("conflict_codes", postgresql.JSONB(), nullable=False),
        sa.Column("rule_version", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
        sa.Column("input_snapshot_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lost_record_id"],
            ["item_records.id"],
            ondelete="CASCADE",
            name="fk_candidate_lost",
        ),
        sa.ForeignKeyConstraint(
            ["found_record_id"],
            ["item_records.id"],
            ondelete="CASCADE",
            name="fk_candidate_found",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_candidate_matches"),
    )
    op.create_index(
        "ix_candidate_matches_top5",
        "candidate_matches",
        ["lost_record_id", sa.text("total_score DESC")],
    )

    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", item_type, nullable=False),
        sa.Column("status", claim_status, server_default="SUBMITTED", nullable=False),
        sa.Column("route_source", sa.String(length=64), nullable=True),
        sa.Column("final_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_matches.id"],
            ondelete="CASCADE",
            name="fk_claim_candidate",
        ),
        sa.ForeignKeyConstraint(
            ["requester_user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_claim_requester",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_claims"),
    )
    op.create_index("ix_claims_candidate_id", "claims", ["candidate_id"])
    op.create_index("ix_claims_requester_user_id", "claims", ["requester_user_id"])

    op.create_table(
        "claim_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("submitted_hmac", sa.LargeBinary(), nullable=True),
        sa.Column("result_code", sa.String(length=64), nullable=False),
        sa.Column("answer_summary", postgresql.JSONB(), nullable=True),
        sa.Column("risk_flag", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"], ["claims.id"], ondelete="CASCADE", name="fk_attempt_claim"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_attempt_user"),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_matches.id"], name="fk_attempt_candidate"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_claim_attempts"),
        sa.UniqueConstraint("claim_id", "attempt_no", name="uq_claim_attempt_number"),
    )
    op.create_index(
        "ix_claim_attempts_lookup",
        "claim_attempts",
        ["user_id", "candidate_id", "created_at"],
    )

    op.create_table(
        "review_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", review_request_type, nullable=False),
        sa.Column("lost_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("candidate_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(request_type = 'UNMATCHED' AND lost_record_id IS NOT NULL "
            "AND claim_id IS NULL) OR "
            "(request_type = 'CLAIM_REVIEW' AND lost_record_id IS NULL "
            "AND claim_id IS NOT NULL)",
            name="ck_review_requests_target_matches_type",
        ),
        sa.ForeignKeyConstraint(
            ["requester_user_id"], ["users.id"], name="fk_review_requester"
        ),
        sa.ForeignKeyConstraint(
            ["lost_record_id"], ["item_records.id"], name="fk_review_lost"
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], name="fk_review_claim"),
        sa.ForeignKeyConstraint(
            ["candidate_snapshot_id"],
            ["candidate_matches.id"],
            name="fk_review_candidate_snapshot",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_requests"),
    )
    op.create_index(
        "uq_review_requests_active_unmatched",
        "review_requests",
        ["requester_user_id", "lost_record_id"],
        unique=True,
        postgresql_where=sa.text("active AND request_type = 'UNMATCHED'"),
    )
    op.create_index(
        "uq_review_requests_active_claim",
        "review_requests",
        ["requester_user_id", "claim_id"],
        unique=True,
        postgresql_where=sa.text("active AND request_type = 'CLAIM_REVIEW'"),
    )

    op.create_table(
        "admin_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", admin_decision, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_data_class", data_class, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["review_request_id"], ["review_requests.id"], name="fk_admin_review_request"
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"], ["claims.id"], name="fk_admin_review_claim"
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_user_id"], ["users.id"], name="fk_admin_reviewer"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_reviews"),
    )


def downgrade() -> None:
    op.drop_table("admin_reviews")
    op.drop_index("uq_review_requests_active_claim", table_name="review_requests")
    op.drop_index("uq_review_requests_active_unmatched", table_name="review_requests")
    op.drop_table("review_requests")
    op.drop_index("ix_claim_attempts_lookup", table_name="claim_attempts")
    op.drop_table("claim_attempts")
    op.drop_index("ix_claims_requester_user_id", table_name="claims")
    op.drop_index("ix_claims_candidate_id", table_name="claims")
    op.drop_table("claims")
    op.drop_index("ix_candidate_matches_top5", table_name="candidate_matches")
    op.drop_table("candidate_matches")
