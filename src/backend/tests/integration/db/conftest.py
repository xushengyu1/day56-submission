from collections.abc import AsyncIterator
from os import environ
from uuid import UUID, uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)


@pytest_asyncio.fixture
async def database_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def seeded_records(database_engine: AsyncEngine) -> dict[str, UUID]:
    ids = {
        "user": uuid4(),
        "lost": uuid4(),
        "identity_found": uuid4(),
        "other_found": uuid4(),
        "candidate": uuid4(),
        "claim": uuid4(),
    }

    async with database_engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE users, item_records, candidate_matches, "
                "claims, review_requests RESTART IDENTITY CASCADE"
            )
        )
        await connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, role) "
                "VALUES (:id, :email, :password_hash, 'USER')"
            ),
            {
                "id": ids["user"],
                "email": "database-test@example.test",
                "password_hash": "synthetic-password-hash",
            },
        )
        for record_id, kind, item_type, public_category, location_area in (
            (ids["lost"], "LOST", "OTHER", "OTHER_CATEGORY", "LIBRARY"),
            (
                ids["identity_found"],
                "FOUND",
                "IDENTITY_DOCUMENT",
                "IDENTITY_CARD",
                "LIBRARY",
            ),
            (
                ids["other_found"],
                "FOUND",
                "OTHER",
                "OTHER_CATEGORY",
                "LIBRARY",
            ),
        ):
            await connection.execute(
                text(
                    "INSERT INTO item_records "
                    "(id, owner_user_id, kind, item_type, public_category, "
                    "location_area, status, version) "
                    "VALUES (:id, :owner_user_id, :kind, :item_type, "
                    ":public_category, :location_area, 'DRAFT', 1)"
                ),
                {
                    "id": record_id,
                    "owner_user_id": ids["user"],
                    "kind": kind,
                    "item_type": item_type,
                    "public_category": public_category,
                    "location_area": location_area,
                },
            )
        await connection.execute(
            text(
                "INSERT INTO candidate_matches "
                "(id, lost_record_id, found_record_id, semantic_score, "
                "time_score, location_score, completeness_score, total_score, "
                "reason_codes, conflict_codes, rule_version, model_version) "
                "VALUES (:id, :lost, :found, 40, 10, 10, 5, 65, '[]', '[]', "
                "'rule-v1', 'model-v1')"
            ),
            {
                "id": ids["candidate"],
                "lost": ids["lost"],
                "found": ids["other_found"],
            },
        )
        await connection.execute(
            text(
                "INSERT INTO claims "
                "(id, candidate_id, requester_user_id, item_type, status) "
                "VALUES (:id, :candidate_id, :requester_user_id, 'OTHER', "
                "'SUBMITTED')"
            ),
            {
                "id": ids["claim"],
                "candidate_id": ids["candidate"],
                "requester_user_id": ids["user"],
            },
        )

    return ids
