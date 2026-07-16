import pytest

from app.db.enums import ItemType, RecordKind
from app.matching.scoring import (
    CandidateFeatures,
    CandidateLevel,
    LocationRelation,
    rank_top_candidates,
    score_candidate,
)


def _features(candidate_id: str = "found-a", **overrides: object) -> CandidateFeatures:
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "left_kind": RecordKind.LOST,
        "right_kind": RecordKind.FOUND,
        "left_item_type": ItemType.OTHER,
        "right_item_type": ItemType.OTHER,
        "left_category": " 雨伞 ",
        "right_category": "雨伞",
        "semantic_similarity": 1.0,
        "time_delta_minutes": 30,
        "location_relation": LocationRelation.SAME_LOCATION,
        "complete_public_fields": 4,
        "total_public_fields": 4,
    }
    values.update(overrides)
    return CandidateFeatures(**values)


def test_score_uses_50_20_20_10_weights_and_high_level() -> None:
    result = score_candidate(_features())

    assert result.eligible
    assert result.semantic_score == 50
    assert result.time_score == 20
    assert result.location_score == 20
    assert result.completeness_score == 10
    assert result.total_score == 100
    assert result.level is CandidateLevel.HIGH


@pytest.mark.parametrize(
    "override",
    [
        {"left_kind": RecordKind.LOST, "right_kind": RecordKind.LOST},
        {"left_item_type": ItemType.OTHER, "right_item_type": ItemType.IDENTITY_DOCUMENT},
        {"right_category": "耳机"},
    ],
)
def test_direction_type_and_category_are_hard_gates(override: dict[str, object]) -> None:
    result = score_candidate(_features(**override))

    assert result.eligible is False
    assert result.total_score == 0
    assert result.level is CandidateLevel.EXCLUDED


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [(60, 20), (61, 12), (240, 12), (241, 6), (None, 0)],
)
def test_time_boundaries(minutes: int | None, expected: int) -> None:
    result = score_candidate(_features(time_delta_minutes=minutes))

    assert result.time_score == expected


def test_location_and_completeness_boundaries() -> None:
    result = score_candidate(
        _features(
            location_relation=LocationRelation.NEARBY_CAMPUS,
            complete_public_fields=3,
            total_public_fields=4,
        )
    )

    assert result.location_score == 8
    assert result.completeness_score == 7.5


def test_invalid_score_inputs_raise_stable_errors() -> None:
    with pytest.raises(ValueError, match="semantic_similarity"):
        score_candidate(_features(semantic_similarity=1.1))
    with pytest.raises(ValueError, match="total_public_fields"):
        score_candidate(_features(complete_public_fields=1, total_public_fields=0))


def test_top_five_uses_candidate_id_as_deterministic_tie_break() -> None:
    candidates = [
        score_candidate(_features(candidate_id=f"found-{letter}", semantic_similarity=0.8))
        for letter in "fedcba"
    ]

    ranked = rank_top_candidates(candidates)

    assert [candidate.candidate_id for candidate in ranked] == [
        "found-a",
        "found-b",
        "found-c",
        "found-d",
        "found-e",
    ]
