from collections.abc import AsyncIterator
from os import environ
from uuid import UUID

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.verification.identity import compute_id_hmac, mask_cn_id


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)
OWNER_ID = UUID("99999999-9999-9999-9999-999999999999")
FINDER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
LOST_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FOUND_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
CANDIDATE_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
VALID_ID = "110101200001010010"
WRONG_VALID_ID = "11010120000101007X"
HMAC_KEY = b"synthetic-test-key"


@pytest_asyncio.fixture
async def identity_claim_database() -> AsyncIterator[tuple[AsyncEngine, dict[str, object]]]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role) VALUES "
                    "(:owner, 'identity-owner@example.test', 'hash', 'USER'), "
                    "(:finder, 'identity-finder@example.test', 'hash', 'USER')"
                ),
                {"owner": OWNER_ID, "finder": FINDER_ID},
            )
            for record_id, owner_id, kind in (
                (LOST_ID, OWNER_ID, "LOST"),
                (FOUND_ID, FINDER_ID, "FOUND"),
            ):
                await connection.execute(
                    text(
                        "INSERT INTO item_records "
                        "(id, owner_user_id, kind, item_type, status, name_public, "
                        "description_public, location_public, version) "
                        "VALUES (:id, :owner, :kind, 'IDENTITY_DOCUMENT', 'PUBLISHED', "
                        "'居民身份证', '拾获证件', '图书馆', 1)"
                    ),
                    {"id": record_id, "owner": owner_id, "kind": kind},
                )
            await connection.execute(
                text(
                    "INSERT INTO identity_document_secrets "
                    "(found_record_id, item_type, document_type, number_hmac, number_masked, key_version, finder_confirmed_at) "
                    "VALUES (:found, 'IDENTITY_DOCUMENT', 'CN_RESIDENT_ID', :hmac, :masked, 1, now())"
                ),
                {
                    "found": FOUND_ID,
                    "hmac": compute_id_hmac(VALID_ID, HMAC_KEY).encode("ascii"),
                    "masked": mask_cn_id(VALID_ID),
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO candidate_matches "
                    "(id, lost_record_id, found_record_id, semantic_score, time_score, location_score, "
                    "completeness_score, total_score, reason_codes, conflict_codes, rule_version, model_version) "
                    "VALUES (:id, :lost, :found, 40, 20, 20, 10, 90, '[]', '[]', 'v1', 'mock')"
                ),
                {"id": CANDIDATE_ID, "lost": LOST_ID, "found": FOUND_ID},
            )
        yield engine, {
            "owner": OWNER_ID,
            "finder": FINDER_ID,
            "lost": LOST_ID,
            "found": FOUND_ID,
            "candidate": CANDIDATE_ID,
            "valid_id": VALID_ID,
            "wrong_id": WRONG_VALID_ID,
            "hmac_key": HMAC_KEY,
        }
    finally:
        await engine.dispose()
