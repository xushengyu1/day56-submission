from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import (
    ItemType,
    LocationArea,
    PublicCategory,
    RecordKind,
    RecordStatus,
)
from app.items.models import ItemRecord
from app.matching.reembed import reembed_published_records


class CountingEmbeddingAdapter:
    model = "qwen3.7-text-embedding"
    dimension = 1024

    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.batch_sizes.append(len(texts))
        return [[0.01] * self.dimension for _ in texts]


@pytest.mark.asyncio
async def test_reembed_updates_published_records_in_batches_and_is_idempotent(
    matching_database,
) -> None:
    engine, _, finder_id = matching_database
    old_vector = [0.1] * 8
    async with AsyncSession(engine, expire_on_commit=False) as session:
        published = (
            await session.scalars(
                select(ItemRecord).where(ItemRecord.status == RecordStatus.PUBLISHED)
            )
        ).all()
        for record in published:
            record.embedding = old_vector
            record.embedding_model = "mock-hash-v1"
            record.embedding_dimensions = 8
        for index in range(15):
            session.add(
                ItemRecord(
                    owner_user_id=finder_id,
                    kind=RecordKind.FOUND,
                    item_type=ItemType.OTHER,
                    public_category=PublicCategory.OTHER_CATEGORY,
                    location_area=LocationArea.TEACHING_BUILDING,
                    status=RecordStatus.PUBLISHED,
                    name_public=f"旧记录 {index}",
                    description_public="等待重算",
                    event_time_exact=datetime.now(timezone.utc),
                    event_time_public="2026-07-17",
                    location_public="教学楼",
                    embedding=old_vector,
                    embedding_model="mock-hash-v1",
                    embedding_dimensions=8,
                    published_at=datetime.now(timezone.utc),
                )
            )
        draft = ItemRecord(
            owner_user_id=finder_id,
            kind=RecordKind.FOUND,
            item_type=ItemType.OTHER,
            public_category=PublicCategory.OTHER_CATEGORY,
            location_area=LocationArea.TEACHING_BUILDING,
            status=RecordStatus.DRAFT,
            name_public="草稿",
            description_public="不重算",
            location_public="教学楼",
            embedding=old_vector,
            embedding_model="mock-hash-v1",
            embedding_dimensions=8,
        )
        claimed = ItemRecord(
            owner_user_id=finder_id,
            kind=RecordKind.FOUND,
            item_type=ItemType.OTHER,
            public_category=PublicCategory.OTHER_CATEGORY,
            location_area=LocationArea.TEACHING_BUILDING,
            status=RecordStatus.CLAIMED,
            name_public="已领取",
            description_public="不重算",
            location_public="教学楼",
            embedding=old_vector,
            embedding_model="mock-hash-v1",
            embedding_dimensions=8,
        )
        session.add_all([draft, claimed])
        await session.commit()

        adapter = CountingEmbeddingAdapter()
        updated = await reembed_published_records(session, adapter)
        await session.commit()
        second = await reembed_published_records(session, adapter)

        refreshed = (
            await session.scalars(
                select(ItemRecord).where(ItemRecord.status == RecordStatus.PUBLISHED)
            )
        ).all()
        await session.refresh(draft)
        await session.refresh(claimed)

    assert updated == 21
    assert second == 0
    assert adapter.batch_sizes == [20, 1]
    assert all(record.embedding_model == adapter.model for record in refreshed)
    assert all(record.embedding_dimensions == adapter.dimension for record in refreshed)
    assert all(len(record.embedding or []) == adapter.dimension for record in refreshed)
    assert draft.embedding_dimensions == 8
    assert claimed.embedding_dimensions == 8


@pytest.mark.parametrize("batch_size", [0, 21])
@pytest.mark.asyncio
async def test_reembed_rejects_invalid_batch_size(
    matching_database, batch_size: int
) -> None:
    engine, _, _ = matching_database
    async with AsyncSession(engine) as session:
        with pytest.raises(ValueError, match="batch_size must be between 1 and 20"):
            await reembed_published_records(
                session,
                CountingEmbeddingAdapter(),
                batch_size=batch_size,
            )
