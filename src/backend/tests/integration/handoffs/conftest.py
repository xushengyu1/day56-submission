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
OWNER_ID = UUID("24242424-2424-2424-2424-242424242424")
FINDER_ID = UUID("25252525-2525-2525-2525-252525252525")
OTHER_ID = UUID("26262626-2626-2626-2626-262626262626")
ADMIN_ID = UUID("27272727-2727-2727-2727-272727272727")
LOST_ID = UUID("28282828-2828-2828-2828-282828282828")
FOUND_ID = UUID("29292929-2929-2929-2929-292929292929")
CANDIDATE_ID = UUID("30303030-3030-3030-3030-303030303030")
CLAIM_ID = UUID("31313131-3131-3131-3131-313131313131")


@pytest_asyncio.fixture
async def handoff_database() -> AsyncIterator[tuple[AsyncEngine, dict[str, UUID]]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE audit_events"))
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) VALUES "
                    "(:owner, 'owner-contact@example.test', 'hash', 'USER'), "
                    "(:finder, 'finder-contact@example.test', 'hash', 'USER'), "
                    "(:other, 'other@example.test', 'hash', 'USER'), "
                    "(:admin, 'admin@example.test', 'hash', 'ADMIN')"
                ),
                {"owner": OWNER_ID, "finder": FINDER_ID, "other": OTHER_ID, "admin": ADMIN_ID},
            )
            for record_id, owner_id, kind in (
                (LOST_ID, OWNER_ID, "LOST"),
                (FOUND_ID, FINDER_ID, "FOUND"),
            ):
                await connection.execute(
                    text(
                        "INSERT INTO item_records "
                        "(id, owner_user_id, kind, item_type, status, name_public, description_public, version) "
                        "VALUES (:id, :owner, :kind, 'OTHER', 'PENDING_HANDOFF', '黑色折叠伞', '外观完整', 1)"
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
                    "INSERT INTO claims (id, candidate_id, requester_user_id, item_type, status, route_source) "
                    "VALUES (:id, :candidate, :owner, 'OTHER', 'PENDING_HANDOFF', 'OTHER_MODEL')"
                ),
                {"id": CLAIM_ID, "candidate": CANDIDATE_ID, "owner": OWNER_ID},
            )
            await connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(event_id, aggregate_type, aggregate_id, event_type, actor_type, actor_id, result_code, metadata_redacted) "
                    "VALUES (gen_random_uuid(), 'item_record', :record, 'FOUND_RECORD_PUBLISHED', 'FINDER', :finder, 'PUBLISHED', "
                    "'{\"safe\":\"ok\",\"admin_note\":\"internal\",\"private_path\":\"[REDACTED]\"}')"
                ),
                {"record": FOUND_ID, "finder": FINDER_ID},
            )
        yield engine, {
            "owner": OWNER_ID,
            "finder": FINDER_ID,
            "other": OTHER_ID,
            "admin": ADMIN_ID,
            "lost": LOST_ID,
            "found": FOUND_ID,
            "candidate": CANDIDATE_ID,
            "claim": CLAIM_ID,
        }
    finally:
        await engine.dispose()
