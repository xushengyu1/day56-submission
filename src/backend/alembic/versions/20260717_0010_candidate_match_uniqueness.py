"""Make candidate generation idempotent."""

from alembic import op


revision: str = "20260717_0010"
down_revision: str | None = "20260717_0009"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TEMP TABLE duplicate_candidate_matches ON COMMIT DROP AS
        SELECT id AS duplicate_id,
               first_value(id) OVER (
                   PARTITION BY lost_record_id, found_record_id
                   ORDER BY created_at, id
               ) AS retained_id
        FROM candidate_matches
        """
    )
    op.execute(
        """
        UPDATE claims
        SET candidate_id = duplicates.retained_id
        FROM duplicate_candidate_matches AS duplicates
        WHERE claims.candidate_id = duplicates.duplicate_id
          AND duplicates.duplicate_id <> duplicates.retained_id
        """
    )
    op.execute(
        """
        UPDATE claim_attempts
        SET candidate_id = duplicates.retained_id
        FROM duplicate_candidate_matches AS duplicates
        WHERE claim_attempts.candidate_id = duplicates.duplicate_id
          AND duplicates.duplicate_id <> duplicates.retained_id
        """
    )
    op.execute(
        """
        UPDATE review_requests
        SET candidate_snapshot_id = duplicates.retained_id
        FROM duplicate_candidate_matches AS duplicates
        WHERE review_requests.candidate_snapshot_id = duplicates.duplicate_id
          AND duplicates.duplicate_id <> duplicates.retained_id
        """
    )
    op.execute(
        """
        DELETE FROM candidate_matches
        USING duplicate_candidate_matches AS duplicates
        WHERE candidate_matches.id = duplicates.duplicate_id
          AND duplicates.duplicate_id <> duplicates.retained_id
        """
    )
    op.create_unique_constraint(
        "uq_candidate_matches_lost_found",
        "candidate_matches",
        ["lost_record_id", "found_record_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_candidate_matches_lost_found",
        "candidate_matches",
        type_="unique",
    )
