from collections.abc import AsyncIterator
from os import environ
from uuid import UUID

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)
OWNER_ID = UUID("16161616-1616-1616-1616-161616161616")
FINDER_ID = UUID("17171717-1717-1717-1717-171717171717")
ADMIN_ID = UUID("18181818-1818-1818-1818-181818181818")
LOST_ID = UUID("19191919-1919-1919-1919-191919191919")
FOUND_ID = UUID("20202020-2020-2020-2020-202020202020")
CANDIDATE_ID = UUID("21212121-2121-2121-2121-212121212121")
CLAIM_ID = UUID("22222222-2323-2323-2323-232323232323")


@pytest_asyncio.fixture
async def review_database() -> AsyncIterator[tuple[AsyncEngine, dict[str, UUID]]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, email, password_hash, role) VALUES "
                    "(:owner, 'review-owner', 'review-owner@example.test', "
                    "'hash', 'USER'), "
                    "(:finder, 'review-finder', 'review-finder@example.test', "
                    "'hash', 'USER'), "
                    "(:admin, 'review-admin', 'review-admin@example.test', "
                    "'hash', 'ADMIN')"
                ),
                {"owner": OWNER_ID, "finder": FINDER_ID, "admin": ADMIN_ID},
            )
            for record_id, owner_id, kind in (
                (LOST_ID, OWNER_ID, "LOST"),
                (FOUND_ID, FINDER_ID, "FOUND"),
            ):
                await connection.execute(
                    text(
                        "INSERT INTO item_records "
                        "(id, owner_user_id, kind, item_type, public_category, "
                        "location_area, status, name_public, description_public, "
                        "location_public, version) "
                        "VALUES (:id, :owner, :kind, 'OTHER', 'OTHER_CATEGORY', "
                        "'LIBRARY', 'PUBLISHED', '黑色折叠伞', '外观完整', "
                        "'图书馆', 1)"
                    ),
                    {"id": record_id, "owner": owner_id, "kind": kind},
                )
            await connection.execute(
                text(
                    "INSERT INTO candidate_matches "
                    "(id, lost_record_id, found_record_id, semantic_score, time_score, location_score, completeness_score, total_score, reason_codes, conflict_codes, rule_version, model_version) "
                    "VALUES (:id, :lost, :found, 40, 20, 20, 10, 90, '[]', '[]', 'v1', 'mock')"
                ),
                {"id": CANDIDATE_ID, "lost": LOST_ID, "found": FOUND_ID},
            )
            await connection.execute(
                text(
                    "INSERT INTO claims (id, candidate_id, requester_user_id, item_type, status, route_source, final_reason) "
                    "VALUES (:id, :candidate, :owner, 'OTHER', 'PENDING_ADMIN_REVIEW', 'OTHER_MODEL', 'MODEL_UNAVAILABLE')"
                ),
                {"id": CLAIM_ID, "candidate": CANDIDATE_ID, "owner": OWNER_ID},
            )
        yield engine, {
            "owner": OWNER_ID,
            "finder": FINDER_ID,
            "admin": ADMIN_ID,
            "lost": LOST_ID,
            "found": FOUND_ID,
            "candidate": CANDIDATE_ID,
            "claim": CLAIM_ID,
        }
    finally:
        await engine.dispose()
