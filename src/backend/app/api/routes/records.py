from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.audit.projection import get_record_timeline
from app.auth.models import User
from app.database import get_database_session


router = APIRouter(prefix="/api/records", tags=["records"])


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
