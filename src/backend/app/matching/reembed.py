from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import RecordStatus
from app.items.catalog import build_public_embedding_text
from app.items.models import ItemRecord
from app.matching.embedding import EmbeddingError, EmbeddingPort


def _public_text(record: ItemRecord) -> str:
    return build_public_embedding_text(
        name_public=record.name_public or "",
        description_public=record.description_public or "",
        location_public=record.location_public or "",
    )


async def reembed_published_records(
    session: AsyncSession,
    adapter: EmbeddingPort,
    batch_size: int = 20,
) -> int:
    if not 1 <= batch_size <= 20:
        raise ValueError("batch_size must be between 1 and 20")
    records = (
        await session.scalars(
            select(ItemRecord)
            .where(
                ItemRecord.status == RecordStatus.PUBLISHED,
                or_(
                    ItemRecord.embedding.is_(None),
                    ItemRecord.embedding_model.is_(None),
                    ItemRecord.embedding_model != adapter.model,
                    ItemRecord.embedding_dimensions.is_(None),
                    ItemRecord.embedding_dimensions != adapter.dimension,
                ),
            )
            .order_by(ItemRecord.id)
        )
    ).all()
    for offset in range(0, len(records), batch_size):
        batch = records[offset : offset + batch_size]
        vectors = await adapter.embed([_public_text(record) for record in batch])
        if len(vectors) != len(batch):
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")
        for record, vector in zip(batch, vectors):
            if len(vector) != adapter.dimension:
                raise EmbeddingError("EMBEDDING_UNAVAILABLE")
            record.embedding = vector
            record.embedding_model = adapter.model
            record.embedding_dimensions = adapter.dimension
    return len(records)
