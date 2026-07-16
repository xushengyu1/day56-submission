import pytest

from app.db.enums import ClaimStatus, RecordStatus
from app.items.state_machine import can_transition_claim, can_transition_record


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RecordStatus.DRAFT, RecordStatus.PROCESSING),
        (RecordStatus.DRAFT, RecordStatus.PUBLISHED),
        (RecordStatus.PROCESSING, RecordStatus.DRAFT),
        (RecordStatus.PUBLISHED, RecordStatus.PENDING_HANDOFF),
        (RecordStatus.PUBLISHED, RecordStatus.MATCHING_FAILED),
        (RecordStatus.MATCHING_FAILED, RecordStatus.PROCESSING),
        (RecordStatus.MATCHING_FAILED, RecordStatus.PUBLISHED),
        (RecordStatus.PENDING_HANDOFF, RecordStatus.CLAIMED),
        (RecordStatus.CLAIMED, RecordStatus.CLOSED),
    ],
)
def test_allowed_record_transitions(current: RecordStatus, target: RecordStatus) -> None:
    assert can_transition_record(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RecordStatus.DRAFT, RecordStatus.CLAIMED),
        (RecordStatus.PROCESSING, RecordStatus.PUBLISHED),
        (RecordStatus.PENDING_HANDOFF, RecordStatus.PUBLISHED),
        (RecordStatus.PENDING_HANDOFF, RecordStatus.CLOSED),
        (RecordStatus.CLOSED, RecordStatus.DRAFT),
        (RecordStatus.CANCELLED, RecordStatus.PUBLISHED),
    ],
)
def test_forbidden_record_transitions(current: RecordStatus, target: RecordStatus) -> None:
    assert can_transition_record(current, target) is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ClaimStatus.SUBMITTED, ClaimStatus.VERIFYING),
        (ClaimStatus.VERIFYING, ClaimStatus.PENDING_HANDOFF),
        (ClaimStatus.VERIFYING, ClaimStatus.PENDING_ADMIN_REVIEW),
        (ClaimStatus.PENDING_ADMIN_REVIEW, ClaimStatus.PENDING_HANDOFF),
        (ClaimStatus.PENDING_HANDOFF, ClaimStatus.CLAIMED),
    ],
)
def test_allowed_claim_transitions(current: ClaimStatus, target: ClaimStatus) -> None:
    assert can_transition_claim(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ClaimStatus.SUBMITTED, ClaimStatus.CLAIMED),
        (ClaimStatus.SUBMITTED, ClaimStatus.PENDING_ADMIN_REVIEW),
        (ClaimStatus.PENDING_ADMIN_REVIEW, ClaimStatus.CLAIMED),
        (ClaimStatus.REJECTED, ClaimStatus.PENDING_HANDOFF),
        (ClaimStatus.LOCKED, ClaimStatus.VERIFYING),
    ],
)
def test_forbidden_claim_transitions(current: ClaimStatus, target: ClaimStatus) -> None:
    assert can_transition_claim(current, target) is False


def test_invalid_status_values_are_rejected_without_internal_errors() -> None:
    assert can_transition_record("UNKNOWN", RecordStatus.DRAFT) is False  # type: ignore[arg-type]
    assert can_transition_claim(ClaimStatus.SUBMITTED, "UNKNOWN") is False  # type: ignore[arg-type]
