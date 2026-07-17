from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.asyncio
async def test_identity_category_rejects_other_item_type(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO item_records "
                    "(id, owner_user_id, kind, item_type, public_category, "
                    "location_area, status, version) "
                    "VALUES (:id, :owner, 'LOST', 'OTHER', 'IDENTITY_CARD', "
                    "'LIBRARY', 'DRAFT', 1)"
                ),
                {"id": uuid4(), "owner": seeded_records["user"]},
            )


@pytest.mark.asyncio
async def test_identity_record_rejects_other_verification_set(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO verification_sets "
                    "(id, found_record_id, item_type, hidden_description) "
                    "VALUES (:id, :record_id, 'OTHER', :description)"
                ),
                {
                    "id": uuid4(),
                    "record_id": seeded_records["identity_found"],
                    "description": "synthetic private feature",
                },
            )


@pytest.mark.asyncio
async def test_other_record_rejects_identity_secret(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO identity_document_secrets "
                    "(found_record_id, item_type, document_type, number_hmac, "
                    "number_masked, key_version) "
                    "VALUES (:record_id, 'IDENTITY_DOCUMENT', "
                    "'CN_RESIDENT_ID', :hmac, :masked, 1)"
                ),
                {
                    "record_id": seeded_records["other_found"],
                    "hmac": b"synthetic-hmac",
                    "masked": "***synthetic****",
                },
            )


@pytest.mark.asyncio
async def test_public_redacted_asset_requires_confirmation(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO image_assets "
                    "(id, record_id, uploader_user_id, purpose, data_class, "
                    "object_key, sha256, mime_type, size_bytes, redaction_status) "
                    "VALUES (:id, :record_id, :user_id, 'PUBLIC_REDACTED', "
                    "'PUBLIC', :object_key, :sha256, 'image/png', 100, 'PENDING')"
                ),
                {
                    "id": uuid4(),
                    "record_id": seeded_records["identity_found"],
                    "user_id": seeded_records["user"],
                    "object_key": "public/synthetic.png",
                    "sha256": "0" * 64,
                },
            )


@pytest.mark.asyncio
async def test_unmatched_review_rejects_claim_target(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO review_requests "
                    "(id, requester_user_id, request_type, claim_id, reason, active) "
                    "VALUES (:id, :user_id, 'UNMATCHED', :claim_id, :reason, true)"
                ),
                {
                    "id": uuid4(),
                    "user_id": seeded_records["user"],
                    "claim_id": seeded_records["claim"],
                    "reason": "synthetic unmatched reason",
                },
            )


@pytest.mark.asyncio
async def test_duplicate_active_review_for_same_target_is_rejected(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    async with database_engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO review_requests "
                "(id, requester_user_id, request_type, lost_record_id, "
                "reason, active) "
                "VALUES (:id, :user_id, 'UNMATCHED', :lost_id, :reason, true)"
            ),
            {
                "id": uuid4(),
                "user_id": seeded_records["user"],
                "lost_id": seeded_records["lost"],
                "reason": "synthetic first request",
            },
        )

    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO review_requests "
                    "(id, requester_user_id, request_type, lost_record_id, "
                    "reason, active) "
                    "VALUES (:id, :user_id, 'UNMATCHED', :lost_id, :reason, true)"
                ),
                {
                    "id": uuid4(),
                    "user_id": seeded_records["user"],
                    "lost_id": seeded_records["lost"],
                    "reason": "synthetic duplicate request",
                },
            )


@pytest.mark.asyncio
async def test_duplicate_candidate_pair_is_rejected(
    database_engine: AsyncEngine,
    seeded_records: dict[str, object],
) -> None:
    with pytest.raises(IntegrityError):
        async with database_engine.begin() as connection:
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
                    "id": uuid4(),
                    "lost": seeded_records["lost"],
                    "found": seeded_records["other_found"],
                },
            )
