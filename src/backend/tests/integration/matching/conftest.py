from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from os import environ
from uuid import UUID

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.auth.models import User  # noqa: F401
from app.db.enums import ItemType, RecordKind, RecordStatus
from app.items.models import ItemRecord
from app.matching.embedding import embed_public_text
from app.settings import settings


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)
OWNER_ID = UUID("77777777-7777-7777-7777-777777777777")
FINDER_ID = UUID("88888888-8888-8888-8888-888888888888")


@pytest_asyncio.fixture
async def matching_database() -> AsyncIterator[tuple[AsyncEngine, UUID, UUID]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) VALUES "
                    "(:owner, 'lost-owner@example.test', 'hash', 'USER'), "
                    "(:finder, 'finder@example.test', 'hash', 'USER')"
                ),
                {"owner": OWNER_ID, "finder": FINDER_ID},
            )
        async with AsyncSession(engine) as session:
            now = datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc)
            for index in range(6):
                text_value = f"黑色折叠伞 外观完整 图书馆 {index}"
                session.add(
                    ItemRecord(
                        owner_user_id=FINDER_ID,
                        kind=RecordKind.FOUND,
                        item_type=ItemType.OTHER,
                        status=RecordStatus.PUBLISHED,
                        name_public="黑色折叠伞",
                        description_public=f"外观完整 {index}",
                        event_time_exact=now + timedelta(minutes=index * 10),
                        event_time_public="2026-07-16 上午",
                        location_public="图书馆",
                        embedding=embed_public_text(
                            [text_value], dimension=settings.embedding_dimension
                        )[0],
                        embedding_model="mock-hash-v1",
                        embedding_dimensions=settings.embedding_dimension,
                        published_at=now,
                    )
                )
            await session.commit()
        yield engine, OWNER_ID, FINDER_ID
    finally:
        await engine.dispose()
