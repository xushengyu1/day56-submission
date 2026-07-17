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
ACTOR_ID = UUID("22222222-2222-2222-2222-222222222222")
OTHER_ACTOR_ID = UUID("33333333-3333-3333-3333-333333333333")


@pytest_asyncio.fixture
async def audit_database() -> AsyncIterator[tuple[AsyncEngine, UUID, UUID]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, email, password_hash, role) VALUES "
                    "(:actor, 'audit-actor', 'audit-actor@example.test', "
                    "'hash', 'USER'), "
                    "(:other, 'audit-other', 'audit-other@example.test', "
                    "'hash', 'USER')"
                ),
                {"actor": ACTOR_ID, "other": OTHER_ACTOR_ID},
            )
        yield engine, ACTOR_ID, OTHER_ACTOR_ID
    finally:
        await engine.dispose()
