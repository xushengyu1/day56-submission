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
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
RECORD_ID = UUID("55555555-5555-5555-5555-555555555555")


def sample_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


@pytest_asyncio.fixture
async def image_database() -> AsyncIterator[tuple[AsyncEngine, UUID, UUID]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) VALUES "
                    "(:user, 'image-user@example.test', 'hash', 'USER')"
                ),
                {"user": USER_ID},
            )
            await connection.execute(
                text(
                    "INSERT INTO item_records (id, owner_user_id, kind, item_type, status, version) "
                    "VALUES (:record, :user, 'FOUND', 'OTHER', 'DRAFT', 1)"
                ),
                {"record": RECORD_ID, "user": USER_ID},
            )
        yield engine, USER_ID, RECORD_ID
    finally:
        await engine.dispose()
