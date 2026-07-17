from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LocationArea, RecordKind, RecordStatus
from app.items.models import ItemRecord
from app.items.projections import project_records
from app.items.schemas import ItemRecordPublic, RecordPage, RecordSummary
from app.items.service import DomainError


PUBLIC_DETAIL_STATUSES = {
    RecordStatus.PUBLISHED,
    RecordStatus.PENDING_HANDOFF,
    RecordStatus.CLAIMED,
    RecordStatus.CLOSED,
}


async def list_recent_records(
    session: AsyncSession,
    *,
    actor_id: UUID,
    limit: int,
) -> list[ItemRecordPublic]:
    records = list(
        await session.scalars(
            select(ItemRecord)
            .where(ItemRecord.status == RecordStatus.PUBLISHED)
            .order_by(ItemRecord.published_at.desc(), ItemRecord.id)
            .limit(limit)
        )
    )
    return await project_records(session, records, actor_id=actor_id)


async def list_public_records(
    session: AsyncSession,
    *,
    actor_id: UUID,
    location_area: LocationArea | None,
    page: int,
    page_size: int,
) -> RecordPage:
    filters = [ItemRecord.status == RecordStatus.PUBLISHED]
    if location_area is not None:
        filters.append(ItemRecord.location_area == location_area)
    total = await session.scalar(
        select(func.count()).select_from(ItemRecord).where(*filters)
    )
    records = list(
        await session.scalars(
            select(ItemRecord)
            .where(*filters)
            .order_by(ItemRecord.published_at.desc(), ItemRecord.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return RecordPage(
        items=await project_records(session, records, actor_id=actor_id),
        page=page,
        page_size=page_size,
        total=total or 0,
    )


async def list_my_records(
    session: AsyncSession,
    *,
    actor_id: UUID,
    kind: RecordKind | None,
    page: int,
    page_size: int,
) -> RecordPage:
    filters = [ItemRecord.owner_user_id == actor_id]
    if kind is not None:
        filters.append(ItemRecord.kind == kind)
    total = await session.scalar(
        select(func.count()).select_from(ItemRecord).where(*filters)
    )
    records = list(
        await session.scalars(
            select(ItemRecord)
            .where(*filters)
            .order_by(ItemRecord.updated_at.desc(), ItemRecord.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return RecordPage(
        items=await project_records(session, records, actor_id=actor_id),
        page=page,
        page_size=page_size,
        total=total or 0,
    )


async def get_my_record_summary(
    session: AsyncSession,
    *,
    actor_id: UUID,
) -> RecordSummary:
    lost_count, found_count, matched_count, total_count = (
        await session.execute(
            select(
                func.count().filter(ItemRecord.kind == RecordKind.LOST),
                func.count().filter(ItemRecord.kind == RecordKind.FOUND),
                func.count().filter(
                    ItemRecord.status.in_(
                        (
                            RecordStatus.PENDING_HANDOFF,
                            RecordStatus.CLAIMED,
                            RecordStatus.CLOSED,
                        )
                    )
                ),
                func.count(),
            ).where(ItemRecord.owner_user_id == actor_id)
        )
    ).one()
    return RecordSummary(
        lost_count=lost_count,
        found_count=found_count,
        matched_count=matched_count,
        total_count=total_count,
    )


async def get_record_detail(
    session: AsyncSession,
    *,
    record_id: UUID,
    kind: RecordKind,
    actor_id: UUID,
) -> ItemRecordPublic:
    record = await session.scalar(
        select(ItemRecord).where(ItemRecord.id == record_id, ItemRecord.kind == kind)
    )
    if record is None or (
        record.owner_user_id != actor_id and record.status not in PUBLIC_DETAIL_STATUSES
    ):
        raise DomainError("NOT_FOUND")
    return (await project_records(session, [record], actor_id=actor_id))[0]
