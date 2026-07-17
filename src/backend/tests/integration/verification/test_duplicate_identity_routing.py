from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus
from app.verification.service import submit_identity_claim


@pytest.mark.asyncio
async def test_duplicate_published_identity_routes_to_admin(identity_claim_database) -> None:
    engine, ids = identity_claim_database
    duplicate_id = uuid4()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO item_records "
                "(id, owner_user_id, kind, item_type, public_category, "
                "location_area, status, version) "
                "VALUES (:id, :finder, 'FOUND', 'IDENTITY_DOCUMENT', "
                "'IDENTITY_CARD', 'LIBRARY', 'PUBLISHED', 1)"
            ),
            {"id": duplicate_id, "finder": ids["finder"]},
        )
        await connection.execute(
            text(
                "INSERT INTO identity_document_secrets "
                "(found_record_id, item_type, document_type, number_hmac, number_masked, key_version, finder_confirmed_at) "
                "SELECT :duplicate, item_type, document_type, number_hmac, number_masked, key_version, now() "
                "FROM identity_document_secrets WHERE found_record_id = :found"
            ),
            {"duplicate": duplicate_id, "found": ids["found"]},
        )

    async with AsyncSession(engine) as session:
        result = await submit_identity_claim(
            session,
            candidate_id=ids["candidate"],
            requester_id=ids["owner"],
            full_number=ids["valid_id"],
            hmac_key=ids["hmac_key"],
        )
        await session.commit()

    assert result.status is ClaimStatus.PENDING_ADMIN_REVIEW
    assert result.result_code == "DUPLICATE_IDENTITY_REVIEW"
