"""Align the authentication response contract."""

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_0008"
down_revision: str | None = "20260717_0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.execute("UPDATE users SET username = split_part(email, '@', 1)")
    op.alter_column("users", "username", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "username")
