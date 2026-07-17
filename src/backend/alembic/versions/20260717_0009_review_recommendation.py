"""Add candidate recommendation review decision."""

from alembic import op


revision: str = "20260717_0009"
down_revision: str | None = "20260717_0008"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE admin_decision ADD VALUE IF NOT EXISTS 'RECOMMEND_CANDIDATE'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE admin_reviews SET decision = 'REJECT' "
        "WHERE decision = 'RECOMMEND_CANDIDATE'"
    )
    op.execute("ALTER TYPE admin_decision RENAME TO admin_decision_old")
    op.execute("CREATE TYPE admin_decision AS ENUM ('APPROVE_TO_HANDOFF', 'REJECT')")
    op.execute(
        "ALTER TABLE admin_reviews ALTER COLUMN decision TYPE admin_decision "
        "USING decision::text::admin_decision"
    )
    op.execute("DROP TYPE admin_decision_old")
