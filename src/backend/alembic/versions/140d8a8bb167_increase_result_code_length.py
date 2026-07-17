"""increase_result_code_length"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '140d8a8bb167'
down_revision: Union[str, None] = '20260717_0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('audit_events', 'result_code',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=256),
               existing_nullable=False)
    op.alter_column('claim_attempts', 'result_code',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=256),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('claim_attempts', 'result_code',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False)
    op.alter_column('audit_events', 'result_code',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False)
