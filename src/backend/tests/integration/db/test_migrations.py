import asyncio
from enum import Enum
from pathlib import Path
import re
from typing import cast
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import inspect, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.db.enums import (
    ActorType,
    AdminDecision,
    ClaimStatus,
    DataClass,
    DocumentType,
    ExtractionStatus,
    ImagePurpose,
    ItemType,
    LocationArea,
    PublicCategory,
    QuestionResult,
    RecordKind,
    RecordStatus,
    RedactionStatus,
    ReviewRequestType,
    UserRole,
)
from app.db.models import Base
from app.items.models import ItemRecord
from app.settings import settings


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


def _alembic_config() -> Config:
    backend_root = Path(__file__).parents[3]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    return config


def test_database_enum_values_are_stable() -> None:
    expected = {
        UserRole: ["USER", "ADMIN"],
        ItemType: ["IDENTITY_DOCUMENT", "OTHER"],
        PublicCategory: [
            "ELECTRONICS",
            "IDENTITY_CARD",
            "CLOTHING",
            "STATIONERY",
            "OTHER_CATEGORY",
        ],
        LocationArea: [
            "DORMITORY",
            "CANTEEN",
            "TEACHING_BUILDING",
            "SCIENCE_BUILDING",
            "LIBRARY",
        ],
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
        assert [member.value for member in cast(type[Enum], enum_type)] == values


def test_model_metadata_contains_all_t01_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


@pytest.mark.asyncio
async def test_migrations_create_core_schema(database_engine: AsyncEngine) -> None:
    async with database_engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )
        item_columns = dict(
            (
                await connection.execute(
                    text(
                        "SELECT column_name, is_nullable "
                        "FROM information_schema.columns "
                        "WHERE table_schema = current_schema() "
                        "AND table_name = 'item_records'"
                    )
                )
            ).all()
        )
        user_columns = dict(
            (
                await connection.execute(
                    text(
                        "SELECT column_name, is_nullable "
                        "FROM information_schema.columns "
                        "WHERE table_schema = current_schema() "
                        "AND table_name = 'users'"
                    )
                )
            ).all()
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
    assert item_columns["public_category"] == "NO"
    assert item_columns["location_area"] == "NO"
    assert user_columns["username"] == "NO"
    assert {
        "ix_item_records_match_taxonomy",
        "ix_candidate_matches_top5",
        "ix_identity_document_secrets_hmac",
        "ix_claim_attempts_lookup",
        "ix_audit_events_timeline",
        "uq_review_requests_active_unmatched",
        "uq_review_requests_active_claim",
    } <= index_names
    assert "ix_item_records_match_filter" not in index_names


@pytest.mark.asyncio
async def test_matching_taxonomy_migration_backfills_existing_record() -> None:
    config = _alembic_config()
    await asyncio.to_thread(command.downgrade, config, "20260716_0006")

    user_id = uuid4()
    record_id = uuid4()
    old_engine = create_async_engine(settings.database_url)
    try:
        async with old_engine.begin() as connection:
            await connection.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) "
                    "VALUES (:id, :email, :password_hash, 'USER')"
                ),
                {
                    "id": user_id,
                    "email": "migration-backfill@example.test",
                    "password_hash": "synthetic-password-hash",
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO item_records "
                    "(id, owner_user_id, kind, item_type, status, "
                    "location_public, version) "
                    "VALUES (:id, :owner, 'FOUND', 'IDENTITY_DOCUMENT', "
                    "'DRAFT', '图书馆', 1)"
                ),
                {"id": record_id, "owner": user_id},
            )
    finally:
        await old_engine.dispose()

    await asyncio.to_thread(command.upgrade, config, "head")

    upgraded_engine = create_async_engine(settings.database_url)
    try:
        async with upgraded_engine.connect() as connection:
            migrated = (
                await connection.execute(
                    text(
                        "SELECT public_category::text, location_area::text "
                        "FROM item_records WHERE id = :id"
                    ),
                    {"id": record_id},
                )
            ).one()
    finally:
        await upgraded_engine.dispose()

    assert migrated == ("IDENTITY_CARD", "LIBRARY")


@pytest.mark.asyncio
async def test_matching_taxonomy_migration_rejects_unknown_location() -> None:
    config = _alembic_config()
    await asyncio.to_thread(command.downgrade, config, "20260716_0006")

    user_id = uuid4()
    record_id = uuid4()
    old_engine = create_async_engine(settings.database_url)
    try:
        async with old_engine.begin() as connection:
            await connection.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) "
                    "VALUES (:id, :email, :password_hash, 'USER')"
                ),
                {
                    "id": user_id,
                    "email": "migration-rejection@example.test",
                    "password_hash": "synthetic-password-hash",
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO item_records "
                    "(id, owner_user_id, kind, item_type, status, "
                    "location_public, version) "
                    "VALUES (:id, :owner, 'FOUND', 'OTHER', 'DRAFT', "
                    "'操场', 1)"
                ),
                {"id": record_id, "owner": user_id},
            )
    finally:
        await old_engine.dispose()

    try:
        with pytest.raises(DBAPIError, match="UNMAPPABLE_LOCATION_PUBLIC"):
            await asyncio.to_thread(command.upgrade, config, "head")
    finally:
        cleanup_engine = create_async_engine(settings.database_url)
        try:
            async with cleanup_engine.begin() as connection:
                await connection.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
        finally:
            await cleanup_engine.dispose()
        await asyncio.to_thread(command.upgrade, config, "head")


@pytest.mark.asyncio
async def test_auth_contract_migration_backfills_username_from_email() -> None:
    config = _alembic_config()
    await asyncio.to_thread(command.downgrade, config, "20260717_0007")

    user_id = uuid4()
    old_engine = create_async_engine(settings.database_url)
    try:
        async with old_engine.begin() as connection:
            await connection.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) "
                    "VALUES (:id, 'legacy.user@example.test', 'hash', 'USER')"
                ),
                {"id": user_id},
            )
    finally:
        await old_engine.dispose()

    await asyncio.to_thread(command.upgrade, config, "head")

    upgraded_engine = create_async_engine(settings.database_url)
    try:
        async with upgraded_engine.connect() as connection:
            username = await connection.scalar(
                text("SELECT username FROM users WHERE id = :id"), {"id": user_id}
            )
    finally:
        await upgraded_engine.dispose()

    assert username == "legacy.user"


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
