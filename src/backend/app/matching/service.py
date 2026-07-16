from __future__ import annotations

from datetime import datetime, timezone
import math
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User  # noqa: F401 - register FK target metadata
from app.core.idempotency import hash_request
from app.db.enums import ItemType, RecordKind, RecordStatus
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.matching.embedding import embed_public_text
from app.matching.models import CandidateMatch
from app.matching.schemas import CandidatePublic
from app.matching.scoring import (
    CandidateFeatures,
    CandidateLevel,
    LocationRelation,
    rank_top_candidates,
    score_candidate,
)
from app.settings import settings


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise DomainError("EMBEDDING_DIMENSION_MISMATCH")
    denominator = math.sqrt(sum(v * v for v in left)) * math.sqrt(
        sum(v * v for v in right)
    )
    if denominator == 0:
        return 0
    return max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right)) / denominator))


async def create_lost_record(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    item_type: ItemType,
    event_time: datetime,
    location_public: str,
    name_public: str,
    description_public: str,
) -> ItemRecord:
    if not all(value.strip() for value in (location_public, name_public, description_public)):
        raise DomainError("FIELD_INVALID")
    public_text = f"{name_public}\n{description_public}\n{location_public}"
    embedding = embed_public_text([public_text], dimension=settings.embedding_dimension)[0]
    record = ItemRecord(
        owner_user_id=owner_user_id,
        kind=RecordKind.LOST,
        item_type=item_type,
        status=RecordStatus.PUBLISHED,
        name_public=name_public.strip(),
        description_public=description_public.strip(),
        event_time_exact=event_time,
        event_time_public=event_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        location_public=location_public.strip(),
        embedding=embedding,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimension,
        published_at=datetime.now(timezone.utc),
    )
    session.add(record)
    return record


async def generate_candidates(
    session: AsyncSession, *, lost_record: ItemRecord
) -> list[CandidateMatch]:
    if lost_record.kind is not RecordKind.LOST or lost_record.embedding is None:
        raise DomainError("MATCH_INPUT_INVALID")
    found_records = (
        await session.scalars(
            select(ItemRecord).where(
                ItemRecord.kind == RecordKind.FOUND,
                ItemRecord.status == RecordStatus.PUBLISHED,
                ItemRecord.item_type == lost_record.item_type,
                ItemRecord.embedding.is_not(None),
            )
        )
    ).all()
    scores = []
    score_to_record: dict[str, ItemRecord] = {}
    for found in found_records:
        cosine = _cosine(lost_record.embedding, found.embedding or [])
        semantic_similarity = (cosine + 1) / 2
        time_delta = None
        if lost_record.event_time_exact and found.event_time_exact:
            time_delta = abs(
                (lost_record.event_time_exact - found.event_time_exact).total_seconds()
            ) / 60
        location = (
            LocationRelation.SAME_LOCATION
            if lost_record.location_public
            and found.location_public
            and lost_record.location_public.strip().casefold()
            == found.location_public.strip().casefold()
            else LocationRelation.UNKNOWN
        )
        complete = sum(
            value is not None and (not isinstance(value, str) or bool(value.strip()))
            for value in (
                found.name_public,
                found.description_public,
                found.event_time_public,
                found.location_public,
            )
        )
        score = score_candidate(
            CandidateFeatures(
                candidate_id=str(found.id),
                left_kind=lost_record.kind,
                right_kind=found.kind,
                left_item_type=lost_record.item_type,
                right_item_type=found.item_type,
                left_category=lost_record.item_type.value,
                right_category=found.item_type.value,
                semantic_similarity=semantic_similarity,
                time_delta_minutes=time_delta,
                location_relation=location,
                complete_public_fields=complete,
                total_public_fields=4,
            )
        )
        scores.append(score)
        score_to_record[score.candidate_id] = found

    ranked = rank_top_candidates(scores)
    await session.execute(
        delete(CandidateMatch).where(CandidateMatch.lost_record_id == lost_record.id)
    )
    models = []
    for score in ranked:
        found = score_to_record[score.candidate_id]
        model = CandidateMatch(
            lost_record_id=lost_record.id,
            found_record_id=found.id,
            semantic_score=score.semantic_score,
            time_score=score.time_score,
            location_score=score.location_score,
            completeness_score=score.completeness_score,
            total_score=score.total_score,
            reason_codes=["SEMANTIC_MATCH", "TYPE_MATCH"],
            conflict_codes=list(score.conflicts),
            rule_version="score-v1",
            model_version=lost_record.embedding_model or "unknown",
            input_snapshot_hash=hash_request(
                {"lost": str(lost_record.id), "found": str(found.id)}
            ),
        )
        session.add(model)
        models.append(model)
    return models


def _level(total: float) -> str:
    if total < 60:
        return CandidateLevel.LOW.value
    if total < 80:
        return CandidateLevel.MEDIUM.value
    return CandidateLevel.HIGH.value


async def list_candidates(
    session: AsyncSession, lost_record_id: UUID, actor_id: UUID
) -> list[CandidatePublic]:
    lost = await session.get(ItemRecord, lost_record_id)
    if lost is None:
        raise DomainError("NOT_FOUND")
    if lost.owner_user_id != actor_id:
        raise DomainError("NOT_OWNER")
    rows = (
        await session.execute(
            select(CandidateMatch, ItemRecord)
            .join(ItemRecord, ItemRecord.id == CandidateMatch.found_record_id)
            .where(CandidateMatch.lost_record_id == lost_record_id)
            .order_by(CandidateMatch.total_score.desc(), CandidateMatch.id)
            .limit(5)
        )
    ).all()
    return [
        CandidatePublic(
            id=candidate.id,
            found_record_id=found.id,
            item_type=found.item_type,
            name_public=found.name_public or "",
            description_public=found.description_public or "",
            event_time_public=found.event_time_public,
            location_public=found.location_public or "",
            total_score=float(candidate.total_score),
            level=_level(float(candidate.total_score)),
            reason_codes=tuple(candidate.reason_codes),
            conflict_codes=tuple(candidate.conflict_codes),
        )
        for candidate, found in rows
    ]


async def get_candidate(
    session: AsyncSession, candidate_id: UUID, actor_id: UUID
) -> CandidatePublic:
    candidate = await session.get(CandidateMatch, candidate_id)
    if candidate is None:
        raise DomainError("NOT_FOUND")
    candidates = await list_candidates(session, candidate.lost_record_id, actor_id)
    for item in candidates:
        if item.id == candidate_id:
            return item
    raise DomainError("NOT_FOUND")
