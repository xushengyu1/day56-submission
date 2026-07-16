"""Enable pgvector and create stable enum types."""

from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


ENUMS = (
    ("user_role", ("USER", "ADMIN")),
    ("item_type", ("IDENTITY_DOCUMENT", "OTHER")),
    ("record_kind", ("LOST", "FOUND")),
    (
        "record_status",
        (
            "DRAFT",
            "PROCESSING",
            "PUBLISHED",
            "MATCHING_FAILED",
            "PENDING_HANDOFF",
            "CLAIMED",
            "CLOSED",
            "CANCELLED",
        ),
    ),
    (
        "claim_status",
        (
            "SUBMITTED",
            "VERIFYING",
            "PENDING_ADMIN_REVIEW",
            "PENDING_HANDOFF",
            "REJECTED",
            "CLAIMED",
            "LOCKED",
        ),
    ),
    ("data_class", ("PUBLIC", "MATCH_ONLY", "VERIFICATION", "PRIVATE")),
    ("actor_type", ("OWNER", "FINDER", "ADMIN", "SYSTEM", "AI")),
    (
        "image_purpose",
        ("FINDER_ORIGINAL", "PUBLIC_REDACTED", "OWNER_SUPPORT"),
    ),
    (
        "redaction_status",
        ("NOT_REQUIRED", "PENDING", "CONFIRMED", "FAILED"),
    ),
    ("extraction_status", ("SUCCEEDED", "INVALID", "TIMEOUT", "FALLBACK")),
    (
        "question_result",
        ("MATCH", "PARTIAL_MATCH", "UNDETERMINED", "CONFLICT"),
    ),
    ("document_type", ("CN_RESIDENT_ID",)),
    ("admin_decision", ("APPROVE_TO_HANDOFF", "REJECT")),
    ("review_request_type", ("UNMATCHED", "CLAIM_REVIEW")),
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    for name, values in ENUMS:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name, _ in reversed(ENUMS):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
    op.execute("DROP EXTENSION IF EXISTS vector")
