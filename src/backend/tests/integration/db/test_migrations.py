from pathlib import Path
import re

import pytest
from sqlalchemy import inspect, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.enums import (
    ActorType,
    AdminDecision,
    ClaimStatus,
    DataClass,
    DocumentType,
    ExtractionStatus,
    ImagePurpose,
    ItemType,
    QuestionResult,
    RecordKind,
    RecordStatus,
    RedactionStatus,
    ReviewRequestType,
    UserRole,
)
from app.db.models import Base
from app.items.models import ItemRecord


EXPECTED_TABLES = {
    "users",
    "refresh_tokens",
    "item_records",
    "image_assets",
    "ai_extractions",
    "identity_document_secrets",
    "verification_sets",
    "verification_questions",
    "candidate_matches",
    "claims",
    "claim_attempts",
    "review_requests",
    "admin_reviews",
    "audit_events",
    "idempotency_results",
}


def test_database_enum_values_are_stable() -> None:
    expected = {
        UserRole: ["USER", "ADMIN"],
        ItemType: ["IDENTITY_DOCUMENT", "OTHER"],
        RecordKind: ["LOST", "FOUND"],
        RecordStatus: [
            "DRAFT",
            "PROCESSING",
            "PUBLISHED",
            "MATCHING_FAILED",
            "PENDING_HANDOFF",
            "CLAIMED",
            "CLOSED",
            "CANCELLED",
        ],
        ClaimStatus: [
            "SUBMITTED",
            "VERIFYING",
            "PENDING_ADMIN_REVIEW",
            "PENDING_HANDOFF",
            "REJECTED",
            "CLAIMED",
            "LOCKED",
        ],
        DataClass: ["PUBLIC", "MATCH_ONLY", "VERIFICATION", "PRIVATE"],
        ActorType: ["OWNER", "FINDER", "ADMIN", "SYSTEM", "AI"],
        ImagePurpose: ["FINDER_ORIGINAL", "PUBLIC_REDACTED", "OWNER_SUPPORT"],
        RedactionStatus: ["NOT_REQUIRED", "PENDING", "CONFIRMED", "FAILED"],
        ExtractionStatus: ["SUCCEEDED", "INVALID", "TIMEOUT", "FALLBACK"],
        QuestionResult: ["MATCH", "PARTIAL_MATCH", "UNDETERMINED", "CONFLICT"],
        DocumentType: ["CN_RESIDENT_ID"],
        AdminDecision: ["APPROVE_TO_HANDOFF", "REJECT"],
        ReviewRequestType: ["UNMATCHED", "CLAIM_REVIEW"],
    }

    for enum_type, values in expected.items():
        assert [member.value for member in enum_type] == values


def test_model_metadata_contains_all_t01_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


@pytest.mark.asyncio
async def test_migrations_create_core_schema(database_engine: AsyncEngine) -> None:
    async with database_engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )
        extension = await connection.scalar(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        embedding_type = await connection.scalar(
            text(
                "SELECT udt_name FROM information_schema.columns "
                "WHERE table_name = 'item_records' AND column_name = 'embedding'"
            )
        )
        index_names = set(
            await connection.scalars(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = current_schema()"
                )
            )
        )

    assert EXPECTED_TABLES <= tables
    assert extension == "vector"
    assert embedding_type == "vector"
    assert {
        "ix_item_records_match_filter",
        "ix_candidate_matches_top5",
        "ix_identity_document_secrets_hmac",
        "ix_claim_attempts_lookup",
        "ix_audit_events_timeline",
        "uq_review_requests_active_unmatched",
        "uq_review_requests_active_claim",
    } <= index_names


def test_migrations_do_not_contain_identity_number_literals() -> None:
    migration_root = Path(__file__).parents[3] / "alembic" / "versions"
    migration_text = "\n".join(
        path.read_text(encoding="utf-8") for path in migration_root.glob("*.py")
    )

    assert re.search(r"\d{17}[\dXx]", migration_text) is None
    assert "full_identity_number" not in migration_text


@pytest.mark.asyncio
async def test_vector_type_round_trips_public_embedding(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    embedding = [0.25, -0.5, 0.75]
    async with database_engine.begin() as connection:
        await connection.execute(
            update(ItemRecord)
            .where(ItemRecord.id == seeded_records["lost"])
            .values(embedding=embedding)
        )
        stored = await connection.scalar(
            select(ItemRecord.embedding).where(
                ItemRecord.id == seeded_records["lost"]
            )
        )

    assert stored == embedding
