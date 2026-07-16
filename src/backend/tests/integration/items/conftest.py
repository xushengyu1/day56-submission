from collections.abc import AsyncIterator
from io import BytesIO
from os import environ
from uuid import UUID

import pytest_asyncio
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)
OWNER_ID = UUID("66666666-6666-6666-6666-666666666666")


def sample_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


@pytest_asyncio.fixture
async def item_database() -> AsyncIterator[tuple[AsyncEngine, UUID]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) VALUES "
                    "(:owner, 'found-owner@example.test', 'hash', 'USER')"
                ),
                {"owner": OWNER_ID},
            )
        yield engine, OWNER_ID
    finally:
        await engine.dispose()
