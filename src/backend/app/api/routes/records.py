from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.audit.projection import get_record_timeline
from app.auth.models import User
from app.database import get_database_session
from app.db.enums import LocationArea, RecordKind
from app.items.query_service import (
    list_my_records,
    list_public_records,
    list_recent_records,
)
from app.items.schemas import ItemRecordPublic, RecordPage


router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("/recent", response_model=list[ItemRecordPublic])
async def recent_records(
    limit: int = Query(default=5, ge=1, le=20),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[ItemRecordPublic]:
    return await list_recent_records(session, actor_id=user.id, limit=limit)


@router.get("", response_model=RecordPage)
async def public_records(
    location_area: LocationArea | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> RecordPage:
    return await list_public_records(
        session,
        actor_id=user.id,
        location_area=location_area,
        page=page,
        page_size=page_size,
    )


@router.get("/mine", response_model=RecordPage)
async def my_records(
    kind: RecordKind | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> RecordPage:
    return await list_my_records(
        session,
        actor_id=user.id,
        kind=kind,
        page=page,
        page_size=page_size,
    )


@router.get("/{record_id}/timeline")
async def record_timeline(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[dict[str, object]]:
    return await get_record_timeline(
        session,
        record_id=record_id,
        actor_id=user.id,
        actor_role=user.role,
    )
