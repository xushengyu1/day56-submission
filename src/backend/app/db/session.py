from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.settings import settings


def create_database_engine(database_url: str) -> AsyncEngine:
    options: dict[str, object] = {"pool_pre_ping": True}
    if settings.app_env == "test":
        options["poolclass"] = NullPool
    return create_async_engine(database_url, **options)


engine = create_database_engine(settings.database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def check_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
