from collections.abc import AsyncIterator
import json
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.database import get_database_session
from app.db.enums import RecordKind, RecordStatus
from app.items.models import ItemRecord
from app.items.query_service import get_record_detail
from app.items.schemas import ItemRecordPublic
from app.items.service import DomainError
from app.matching.schemas import CandidatePublic, LostRecordCreate
from app.matching.service import create_lost_record, generate_candidates, list_candidates
from app.reviews.schemas import ReviewRequestCreate
from app.reviews.service import create_unmatched_review_request


router = APIRouter(prefix="/api/lost-records", tags=["lost-records"])


@router.get("/{record_id}", response_model=ItemRecordPublic)
async def lost_record_detail(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> ItemRecordPublic:
    return await get_record_detail(
        session,
        record_id=record_id,
        kind=RecordKind.LOST,
        actor_id=user.id,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lost(
    payload: LostRecordCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        record = await create_lost_record(
            session, owner_user_id=user.id, **payload.model_dump()
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {
        "id": str(record.id),
        "status": record.status.value,
    }


def sse_event(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


@router.get("/{record_id}/match")
async def match_lost_record(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> StreamingResponse:
    record = await session.get(ItemRecord, record_id)
    if record is None or record.kind is not RecordKind.LOST:
        raise DomainError("NOT_FOUND")
    if record.owner_user_id != user.id:
        raise DomainError("NOT_OWNER")

    async def stream() -> AsyncIterator[str]:
        for stage_name, progress in (
            ("searching", 15),
            ("filtering", 30),
            ("embedding", 50),
            ("matching", 70),
        ):
            yield sse_event(
                "progress", {"stage": stage_name, "progress": progress}
            )
        try:
            await generate_candidates(session, lost_record=record)
            await session.commit()
        except DomainError:
            await session.rollback()
            await session.execute(
                update(ItemRecord)
                .where(ItemRecord.id == record_id)
                .values(status=RecordStatus.MATCHING_FAILED)
            )
            await session.commit()
            yield sse_event(
                "error",
                {
                    "stage": "failed",
                    "progress": 100,
                    "error_code": "MATCHING_FAILED",
                },
            )
            return
        for stage_name, progress in (("scoring", 85), ("finalizing", 100)):
            yield sse_event(
                "progress", {"stage": stage_name, "progress": progress}
            )
        yield sse_event("done", {"stage": "done", "progress": 100})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/{record_id}/candidates", response_model=list[CandidatePublic])
async def candidate_list(
    record_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> list[CandidatePublic]:
    return await list_candidates(session, record_id, user.id)


@router.post("/{record_id}/review-requests", status_code=status.HTTP_201_CREATED)
async def unmatched_review_request(
    record_id: UUID,
    payload: ReviewRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    try:
        request = await create_unmatched_review_request(
            session,
            lost_record_id=record_id,
            requester_id=user.id,
            reason=payload.reason,
        )
        await session.commit()
    except DomainError:
        await session.rollback()
        raise
    return {"id": str(request.id), "status": request.status}
