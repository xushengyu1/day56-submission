from __future__ import annotations

from datetime import datetime, timezone
import math
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User  # noqa: F401 - register FK target metadata
from app.core.idempotency import hash_request
from app.db.enums import LocationArea, PublicCategory, RecordKind, RecordStatus
from app.items.catalog import (
    build_public_embedding_text,
    item_type_for,
    location_public_for,
)
from app.items.models import ItemRecord
from app.items.projections import project_records
from app.items.service import DomainError
from app.matching.embedding import EmbeddingError, EmbeddingPort
from app.matching.embedding_factory import build_embedding_adapter
from app.matching.models import CandidateMatch
from app.matching.schemas import CandidatePublic
from app.matching.scoring import (
    CandidateFeatures,
    CandidateLevel,
    LocationRelation,
    rank_top_candidates,
    score_candidate,
)
from app.reviews.models import Claim


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
    public_category: PublicCategory,
    location_area: LocationArea,
    event_time: datetime,
    name_public: str,
    description_public: str,
    embedding_adapter: EmbeddingPort | None = None,
) -> ItemRecord:
    if not all(value.strip() for value in (name_public, description_public)):
        raise DomainError("FIELD_INVALID")
    location_public = location_public_for(location_area)
    public_text = build_public_embedding_text(
        name_public=name_public,
        description_public=description_public,
        location_public=location_public,
    )
    try:
        adapter = embedding_adapter or build_embedding_adapter()
        embedding = (await adapter.embed([public_text]))[0]
    except EmbeddingError:
        raise DomainError("EMBEDDING_UNAVAILABLE") from None
    record = ItemRecord(
        owner_user_id=owner_user_id,
        kind=RecordKind.LOST,
        item_type=item_type_for(public_category),
        public_category=public_category,
        location_area=location_area,
        status=RecordStatus.PUBLISHED,
        name_public=name_public.strip(),
        description_public=description_public.strip(),
        event_time_exact=event_time,
        event_time_public=event_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        location_public=location_public.strip(),
        embedding=embedding,
        embedding_model=adapter.model,
        embedding_dimensions=adapter.dimension,
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
                ItemRecord.public_category == lost_record.public_category,
                ItemRecord.location_area == lost_record.location_area,
                ItemRecord.item_type == lost_record.item_type,
                ItemRecord.embedding.is_not(None),
                ItemRecord.embedding_model == lost_record.embedding_model,
                ItemRecord.embedding_dimensions == lost_record.embedding_dimensions,
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
        location = LocationRelation.SAME_LOCATION
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
                left_category=lost_record.public_category.value,
                right_category=found.public_category.value,
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
        delete(CandidateMatch).where(
            CandidateMatch.lost_record_id == lost_record.id,
            CandidateMatch.id.not_in(select(Claim.candidate_id)),
        )
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
    found_records = [found for _, found in rows]
    found_projections = await project_records(
        session, found_records, actor_id=actor_id
    )
    return [
        CandidatePublic(
            id=candidate.id,
            lost_record_id=candidate.lost_record_id,
            found_record_id=found.id,
            total_score=float(candidate.total_score),
            level=_level(float(candidate.total_score)),
            reason_codes=tuple(candidate.reason_codes),
            conflict_codes=tuple(candidate.conflict_codes),
            found_record=found_projection,
            created_at=candidate.created_at,
        )
        for (candidate, found), found_projection in zip(rows, found_projections)
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
