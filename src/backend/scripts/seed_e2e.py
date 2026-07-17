from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid5

from alembic import command
from alembic.config import Config
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import User
from app.auth.security import hash_password
from app.db.enums import UserRole
from app.db.models import Base
from app.settings import settings


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parents[1]
DEFAULT_ASSET_DIR = REPOSITORY_ROOT / "frontend" / "e2e" / "assets"
MAINTENANCE_DATABASE = "lost_found"
E2E_NAMESPACE = UUID("f07eb7a0-7ea5-4de0-b8e2-a3b68cd7d28f")

E2E_ADMIN_EMAIL = "synthetic.admin@example.test"
E2E_ADMIN_PASSWORD = "SyntheticAdmin123!"
E2E_USER_EMAIL = "synthetic.user@example.test"
E2E_USER_PASSWORD = "SyntheticUser123!"


def validate_e2e_target(app_env: str, database_url: str) -> URL:
    target = make_url(database_url)
    if app_env != "e2e":
        raise RuntimeError("seed_e2e requires APP_ENV=e2e")
    if not target.database or not target.database.endswith("_e2e"):
        raise RuntimeError("seed_e2e database name must end with _e2e")
    return target


def maintenance_url(target: URL) -> URL:
    return target.set(database=MAINTENANCE_DATABASE)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


async def ensure_target_database(target: URL) -> None:
    engine = create_async_engine(
        maintenance_url(target),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database"),
                {"database": target.database},
            )
            if exists is None:
                await connection.exec_driver_sql(
                    f"CREATE DATABASE {_quote_identifier(target.database or '')}"
                )
    finally:
        await engine.dispose()


def upgrade_target_database(target: URL) -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", target.render_as_string(hide_password=False))
    command.upgrade(config, "head")


def application_table_names() -> tuple[str, ...]:
    return tuple(table.name for table in reversed(Base.metadata.sorted_tables))


async def reset_application_tables(target: URL) -> None:
    engine = create_async_engine(target, poolclass=NullPool)
    try:
        table_names = application_table_names()
        if not table_names:
            return
        statement = "TRUNCATE TABLE " + ", ".join(
            _quote_identifier(name) for name in table_names
        ) + " RESTART IDENTITY CASCADE"
        async with engine.begin() as connection:
            await connection.execute(text(statement))
    finally:
        await engine.dispose()


def synthetic_users() -> tuple[User, User]:
    admin = User(
        id=uuid5(E2E_NAMESPACE, "admin"),
        username="synthetic-admin",
        email=E2E_ADMIN_EMAIL,
        password_hash=hash_password(E2E_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
    )
    user = User(
        id=uuid5(E2E_NAMESPACE, "user"),
        username="synthetic-user",
        email=E2E_USER_EMAIL,
        password_hash=hash_password(E2E_USER_PASSWORD),
        role=UserRole.USER,
    )
    return admin, user


async def seed_users(target: URL) -> None:
    engine = create_async_engine(target, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            session.add_all(synthetic_users())
            await session.commit()
    finally:
        await engine.dispose()


def _synthetic_png(label: str, *, identity: bool) -> bytes:
    image = Image.new("RGB", (960, 600), "#eef3f8")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (80, 70, 880, 530),
        radius=36,
        fill="#cbd8e5" if identity else "#d9e8dc",
        outline="#425466",
        width=6,
    )
    if identity:
        draw.ellipse((140, 150, 340, 350), fill="#71869a")
        draw.rectangle((420, 165, 790, 215), fill="#71869a")
        draw.rectangle((420, 265, 790, 315), fill="#71869a")
        draw.rectangle((420, 365, 790, 415), fill="#283746")
    else:
        draw.polygon(
            ((220, 410), (360, 145), (500, 410)),
            fill="#6b9e7a",
            outline="#425466",
        )
        draw.ellipse((535, 155, 760, 380), fill="#6b8ba4", outline="#425466")
    font = ImageFont.load_default(size=36)
    draw.text((300, 470), label, fill="#111827", font=font)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_synthetic_assets(asset_dir: Path = DEFAULT_ASSET_DIR) -> tuple[Path, Path]:
    asset_dir.mkdir(parents=True, exist_ok=True)
    other_path = asset_dir / "synthetic-other.png"
    identity_path = asset_dir / "synthetic-id.png"
    other_path.write_bytes(_synthetic_png("SYNTHETIC OTHER", identity=False))
    identity_path.write_bytes(_synthetic_png("SYNTHETIC ID", identity=True))
    return other_path, identity_path


async def seed_e2e() -> None:
    target = validate_e2e_target(settings.app_env, settings.database_url)
    await ensure_target_database(target)
    await asyncio.to_thread(upgrade_target_database, target)
    await reset_application_tables(target)
    await seed_users(target)
    paths = generate_synthetic_assets()
    print(f"seeded E2E database={target.database} users=2")
    print(f"synthetic assets: {paths[0]} {paths[1]}")
    print(f"user login: {E2E_USER_EMAIL} / {E2E_USER_PASSWORD}")
    print(f"admin login: {E2E_ADMIN_EMAIL} / {E2E_ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed_e2e())
