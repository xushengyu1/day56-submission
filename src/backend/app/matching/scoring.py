from dataclasses import dataclass
from enum import Enum

from app.db.enums import ItemType, RecordKind


class LocationRelation(str, Enum):
    SAME_LOCATION = "SAME_LOCATION"
    SAME_BUILDING = "SAME_BUILDING"
    ADJACENT_FLOOR = "ADJACENT_FLOOR"
    NEARBY_CAMPUS = "NEARBY_CAMPUS"
    UNRELATED = "UNRELATED"
    UNKNOWN = "UNKNOWN"


class CandidateLevel(str, Enum):
    EXCLUDED = "EXCLUDED"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class CandidateFeatures:
    candidate_id: str
    left_kind: RecordKind
    right_kind: RecordKind
    left_item_type: ItemType
    right_item_type: ItemType
    left_category: str
    right_category: str
    semantic_similarity: float
    time_delta_minutes: float | None
    location_relation: LocationRelation
    complete_public_fields: int
    total_public_fields: int


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    eligible: bool
    total_score: float
    semantic_score: float
    time_score: float
    location_score: float
    completeness_score: float
    level: CandidateLevel
    conflicts: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()


def _excluded(candidate_id: str, conflict: str) -> CandidateScore:
    return CandidateScore(
        candidate_id=candidate_id,
        eligible=False,
        total_score=0,
        semantic_score=0,
        time_score=0,
        location_score=0,
        completeness_score=0,
        level=CandidateLevel.EXCLUDED,
        conflicts=(conflict,),
    )


def _time_score(minutes: float | None) -> tuple[float, str | None, str | None]:
    if minutes is None:
        return 0, None, "time"
    minutes = abs(minutes)
    if minutes <= 60:
        return 20, None, None
    if minutes <= 240:
        return 12, None, None
    if minutes <= 1440:
        return 6, None, None
    return 0, "TIME_CONFLICT", None


def _location_score(
    relation: LocationRelation,
) -> tuple[float, str | None, str | None]:
    scores = {
        LocationRelation.SAME_LOCATION: 20,
        LocationRelation.SAME_BUILDING: 14,
        LocationRelation.ADJACENT_FLOOR: 14,
        LocationRelation.NEARBY_CAMPUS: 8,
        LocationRelation.UNRELATED: 0,
        LocationRelation.UNKNOWN: 0,
    }
    conflicts = {
        LocationRelation.ADJACENT_FLOOR: "LOCATION_WEAK_CONFLICT",
        LocationRelation.NEARBY_CAMPUS: "LOCATION_WEAK_CONFLICT",
        LocationRelation.UNRELATED: "LOCATION_CONFLICT",
    }
    missing = "location" if relation is LocationRelation.UNKNOWN else None
    return scores[relation], conflicts.get(relation), missing


def _level(total_score: float) -> CandidateLevel:
    if total_score < 40:
        return CandidateLevel.EXCLUDED
    if total_score < 60:
        return CandidateLevel.LOW
    if total_score < 80:
        return CandidateLevel.MEDIUM
    return CandidateLevel.HIGH


def score_candidate(features: CandidateFeatures) -> CandidateScore:
    if features.left_kind is features.right_kind:
        return _excluded(features.candidate_id, "RECORD_KIND_MISMATCH")
    if features.left_item_type is not features.right_item_type:
        return _excluded(features.candidate_id, "ITEM_TYPE_MISMATCH")
    if features.left_category.strip().casefold() != features.right_category.strip().casefold():
        return _excluded(features.candidate_id, "CATEGORY_MISMATCH")
    if not 0 <= features.semantic_similarity <= 1:
        raise ValueError("semantic_similarity must be between zero and one")
    if features.total_public_fields <= 0:
        raise ValueError("total_public_fields must be positive")
    if not 0 <= features.complete_public_fields <= features.total_public_fields:
        raise ValueError("complete_public_fields must be between zero and total")

    semantic = round(features.semantic_similarity * 50, 2)
    time, time_conflict, time_missing = _time_score(features.time_delta_minutes)
    location, location_conflict, location_missing = _location_score(
        features.location_relation
    )
    completeness = round(
        features.complete_public_fields / features.total_public_fields * 10, 2
    )
    total = round(semantic + time + location + completeness, 2)
    conflicts = tuple(
        value for value in (time_conflict, location_conflict) if value is not None
    )
    missing = tuple(
        value
        for value in (time_missing, location_missing)
        if value is not None
    )
    if features.complete_public_fields < features.total_public_fields:
        missing += ("public_fields",)
    level = _level(total)
    return CandidateScore(
        candidate_id=features.candidate_id,
        eligible=level is not CandidateLevel.EXCLUDED,
        total_score=total,
        semantic_score=semantic,
        time_score=time,
        location_score=location,
        completeness_score=completeness,
        level=level,
        conflicts=conflicts,
        missing_fields=missing,
    )


def rank_top_candidates(
    candidates: list[CandidateScore],
    *,
    limit: int = 5,
) -> list[CandidateScore]:
    if limit <= 0:
        return []
    eligible = [candidate for candidate in candidates if candidate.eligible]
    return sorted(
        eligible,
        key=lambda candidate: (-candidate.total_score, candidate.candidate_id),
    )[:limit]
