from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from os import environ
from uuid import UUID, uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.auth.security import create_access_token
from app.db.enums import (
    ClaimStatus,
    DataClass,
    DocumentType,
    ImagePurpose,
    ItemType,
    LocationArea,
    PublicCategory,
    RecordKind,
    RecordStatus,
    RedactionStatus,
    UserRole,
)
from app.images.models import ImageAsset
from app.items.models import ItemRecord
from app.matching.models import CandidateMatch
from app.reviews.models import Claim
from app.verification.models import IdentityDocumentSecret, VerificationSet


DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found",
)


@pytest_asyncio.fixture
async def auth_database_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def record_api_data(
    auth_database_engine: AsyncEngine,
) -> dict[str, object]:
    session_maker = async_sessionmaker(auth_database_engine, expire_on_commit=False)
    now = datetime.now(UTC).replace(microsecond=0)
    owner_id = uuid4()
    other_id = uuid4()
    records: dict[str, ItemRecord] = {
        "owner_lost": _record(
            owner_id,
            RecordKind.LOST,
            RecordStatus.PUBLISHED,
            PublicCategory.OTHER_CATEGORY,
            LocationArea.LIBRARY,
            now - timedelta(hours=6),
            "黑色雨伞",
        ),
        "owner_draft": _record(
            owner_id,
            RecordKind.FOUND,
            RecordStatus.DRAFT,
            PublicCategory.OTHER_CATEGORY,
            LocationArea.LIBRARY,
            now - timedelta(hours=5),
            "草稿水杯",
        ),
        "public_found": _record(
            other_id,
            RecordKind.FOUND,
            RecordStatus.PUBLISHED,
            PublicCategory.ELECTRONICS,
            LocationArea.LIBRARY,
            now - timedelta(hours=1),
            "银色耳机",
        ),
        "public_lost": _record(
            other_id,
            RecordKind.LOST,
            RecordStatus.PUBLISHED,
            PublicCategory.STATIONERY,
            LocationArea.TEACHING_BUILDING,
            now - timedelta(hours=4),
            "蓝色笔袋",
        ),
        "handoff_found": _record(
            owner_id,
            RecordKind.FOUND,
            RecordStatus.PENDING_HANDOFF,
            PublicCategory.CLOTHING,
            LocationArea.LIBRARY,
            now - timedelta(hours=3),
            "灰色围巾",
        ),
        "handoff_lost": _record(
            other_id,
            RecordKind.LOST,
            RecordStatus.PENDING_HANDOFF,
            PublicCategory.CLOTHING,
            LocationArea.LIBRARY,
            now - timedelta(hours=3),
            "灰色围巾",
        ),
        "identity_found": _record(
            other_id,
            RecordKind.FOUND,
            RecordStatus.PUBLISHED,
            PublicCategory.IDENTITY_CARD,
            LocationArea.LIBRARY,
            now - timedelta(hours=2),
            "居民身份证",
            item_type=ItemType.IDENTITY_DOCUMENT,
        ),
    }
    owner = User(
        id=owner_id,
        username="record-owner",
        email="record-owner@example.test",
        password_hash="unused",
        phone_encrypted=b"SECRET_PHONE_ENCRYPTED",
        role=UserRole.USER,
    )
    other = User(
        id=other_id,
        username="other-owner",
        email="other-owner@example.test",
        password_hash="unused",
        role=UserRole.USER,
    )
    async with session_maker() as session:
        session.add_all([owner, other, *records.values()])
        await session.flush()
        public_asset = ImageAsset(
            record_id=records["public_found"].id,
            uploader_user_id=other_id,
            purpose=ImagePurpose.PUBLIC_REDACTED,
            data_class=DataClass.PUBLIC,
            object_key="SECRET_OBJECT_KEY/public-found.jpg",
            sha256="a" * 64,
            mime_type="image/jpeg",
            size_bytes=123,
            redaction_status=RedactionStatus.CONFIRMED,
        )
        verification_set = VerificationSet(
            found_record_id=records["public_found"].id,
            item_type=ItemType.OTHER,
            hidden_description="SECRET_HIDDEN_DESCRIPTION",
            confirmed_by=other_id,
            confirmed_at=now,
        )
        identity_secret = IdentityDocumentSecret(
            found_record_id=records["identity_found"].id,
            item_type=ItemType.IDENTITY_DOCUMENT,
            document_type=DocumentType.CN_RESIDENT_ID,
            number_hmac=b"SECRET_NUMBER_HMAC",
            number_masked="1101********0010",
            key_version=1,
            finder_confirmed_at=now,
        )
        candidate = CandidateMatch(
            lost_record_id=records["handoff_lost"].id,
            found_record_id=records["handoff_found"].id,
            semantic_score=Decimal("90.00"),
            time_score=Decimal("90.00"),
            location_score=Decimal("90.00"),
            completeness_score=Decimal("90.00"),
            total_score=Decimal("90.00"),
            reason_codes=[],
            conflict_codes=[],
            rule_version="test",
            model_version="test",
        )
        session.add_all([public_asset, verification_set, identity_secret, candidate])
        await session.flush()
        claim = Claim(
            candidate_id=candidate.id,
            requester_user_id=other_id,
            item_type=ItemType.OTHER,
            status=ClaimStatus.PENDING_HANDOFF,
        )
        session.add(claim)
        await session.commit()

    return {
        "owner_headers": _headers(owner_id),
        "other_headers": _headers(other_id),
        "records": {name: record.id for name, record in records.items()},
        "public_asset_id": public_asset.id,
        "claim_id": claim.id,
    }


def _headers(user_id: UUID) -> dict[str, str]:
    token = create_access_token(user_id, UserRole.USER)
    return {"Authorization": f"Bearer {token}"}


def _record(
    owner_id: UUID,
    kind: RecordKind,
    status: RecordStatus,
    category: PublicCategory,
    location_area: LocationArea,
    created_at: datetime,
    name: str,
    *,
    item_type: ItemType = ItemType.OTHER,
) -> ItemRecord:
    return ItemRecord(
        owner_user_id=owner_id,
        kind=kind,
        item_type=item_type,
        public_category=category,
        location_area=location_area,
        status=status,
        name_public=name,
        description_public=f"{name}的公开描述",
        event_time_exact=created_at,
        event_time_public="2026-07-17 下午",
        location_public="图书馆三楼 302 室",
        location_normalized={"secret": "SECRET_NORMALIZED_LOCATION"},
        embedding=[0.1, 0.2, 0.3],
        embedding_model="SECRET_EMBEDDING_MODEL",
        embedding_dimensions=3,
        published_at=created_at if status is RecordStatus.PUBLISHED else None,
        created_at=created_at,
        updated_at=created_at,
    )
