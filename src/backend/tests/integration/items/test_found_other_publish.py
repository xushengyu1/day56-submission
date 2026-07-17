from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LocationArea, PublicCategory, RecordStatus
from app.db.enums import ImagePurpose
from app.images.service import store_private_asset
from app.images.storage import LocalStorage
from app.items.service import (
    DomainError,
    confirm_found_draft,
    confirm_other_questions,
    create_found_draft,
    publish_found_record,
)
from app.matching.embedding import EmbeddingError
from app.multimodal.mock import MockMultimodalAdapter
from app.multimodal.ports import ModelAdapterError
from app.verification.models import VerificationQuestion

from .conftest import sample_png


class StaticEmbeddingAdapter:
    model = "qwen3.7-text-embedding"
    dimension = 1024

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.01] * self.dimension for _ in texts]


class FailingEmbeddingAdapter:
    model = "qwen3.7-text-embedding"
    dimension = 1024

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingError("EMBEDDING_UNAVAILABLE")


class FailingQuestionAdapter(MockMultimodalAdapter):
    def __init__(self, code: str) -> None:
        self.code = code

    async def generate_questions(self, hidden_description: str):
        raise ModelAdapterError(self.code)


async def _ready_other_record(
    session,
    owner_id,
    tmp_path,
    *,
    public_category=PublicCategory.OTHER_CATEGORY,
    include_original=True,
    include_verification=True,
):
    event_time = datetime.now(timezone.utc)
    record = await create_found_draft(
        session,
        owner_user_id=owner_id,
        event_time=event_time,
        location_area=LocationArea.TEACHING_BUILDING,
    )
    await session.flush()
    if include_original:
        await store_private_asset(
            session,
            LocalStorage(tmp_path),
            record_id=record.id,
            uploader_user_id=owner_id,
            data=sample_png(),
            declared_mime="image/png",
            purpose=ImagePurpose.FINDER_ORIGINAL,
        )
    await confirm_found_draft(
        session,
        record_id=record.id,
        actor_id=owner_id,
        expected_version=1,
        public_category=public_category,
        name_public="黑色折叠伞",
        description_public="教学楼 B 区 302 教室，伞柄有公开划痕",
        event_time=event_time,
        location_area=LocationArea.TEACHING_BUILDING,
    )
    if include_verification:
        await confirm_other_questions(
            session,
            record_id=record.id,
            actor_id=owner_id,
            hidden_description="伞套内侧字母A",
            adapter=MockMultimodalAdapter(),
        )
    return record


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "public_category",
    [
        PublicCategory.ELECTRONICS,
        PublicCategory.CLOTHING,
        PublicCategory.STATIONERY,
        PublicCategory.OTHER_CATEGORY,
    ],
)
async def test_other_categories_publish_without_original_image(
    item_database, tmp_path, public_category
) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await _ready_other_record(
            session,
            owner_id,
            tmp_path,
            public_category=public_category,
            include_original=False,
        )
        await publish_found_record(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=2,
            embedding_adapter=StaticEmbeddingAdapter(),
        )
        await session.commit()

    assert record.status is RecordStatus.PUBLISHED


@pytest.mark.asyncio
async def test_other_publish_without_image_still_requires_verification(
    item_database, tmp_path
) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await _ready_other_record(
            session,
            owner_id,
            tmp_path,
            include_original=False,
            include_verification=False,
        )

        with pytest.raises(DomainError, match="^PUBLISH_GUARD_FAILED$"):
            await publish_found_record(
                session,
                record_id=record.id,
                actor_id=owner_id,
                expected_version=2,
                embedding_adapter=StaticEmbeddingAdapter(),
            )

        assert record.status is RecordStatus.DRAFT


@pytest.mark.asyncio
async def test_other_publish_requires_confirmed_valid_questions(item_database, tmp_path) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await _ready_other_record(session, owner_id, tmp_path)
        embedding_adapter = StaticEmbeddingAdapter()
        await publish_found_record(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=2,
            embedding_adapter=embedding_adapter,
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        question_count = await session.scalar(select(func.count(VerificationQuestion.id)))
    assert question_count == 2
    assert record.status is RecordStatus.PUBLISHED
    assert record.embedding_model == "qwen3.7-text-embedding"
    assert record.embedding_dimensions == 1024
    assert embedding_adapter.calls == [
        ["黑色折叠伞\n教学楼 B 区 302 教室，伞柄有公开划痕\n教学楼"]
    ]
    assert "伞套内侧字母A" not in str(embedding_adapter.calls)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_error",
    ["MODEL_UNAVAILABLE", "MODEL_HTTP_ERROR", "MODEL_RESPONSE_INVALID"],
)
async def test_question_generation_maps_model_errors_to_domain_error(
    item_database, model_error: str
) -> None:
    engine, owner_id = item_database
    event_time = datetime.now(timezone.utc)
    async with AsyncSession(engine) as session:
        record = await create_found_draft(
            session,
            owner_user_id=owner_id,
            event_time=event_time,
            location_area=LocationArea.TEACHING_BUILDING,
        )
        await session.flush()
        await confirm_found_draft(
            session,
            record_id=record.id,
            actor_id=owner_id,
            expected_version=1,
            public_category=PublicCategory.OTHER_CATEGORY,
            name_public="黑色折叠伞",
            description_public="外观完整",
            event_time=event_time,
            location_area=LocationArea.TEACHING_BUILDING,
        )

        with pytest.raises(DomainError, match="^QUESTION_GENERATION_FAILED$"):
            await confirm_other_questions(
                session,
                record_id=record.id,
                actor_id=owner_id,
                hidden_description="伞柄底部有裂纹，伞套有字母标记",
                adapter=FailingQuestionAdapter(model_error),
            )

        question_count = await session.scalar(
            select(func.count(VerificationQuestion.id))
        )
        assert question_count == 0


@pytest.mark.asyncio
async def test_other_publish_stays_draft_when_embedding_fails(
    item_database, tmp_path
) -> None:
    engine, owner_id = item_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        record = await _ready_other_record(session, owner_id, tmp_path)

        with pytest.raises(DomainError, match="^EMBEDDING_UNAVAILABLE$"):
            await publish_found_record(
                session,
                record_id=record.id,
                actor_id=owner_id,
                expected_version=2,
                embedding_adapter=FailingEmbeddingAdapter(),
            )

        assert record.status is RecordStatus.DRAFT
        assert record.embedding is None
