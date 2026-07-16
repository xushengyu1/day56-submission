"""Pure transition rules for lost/found records and claims."""

from __future__ import annotations

from collections.abc import Mapping

from app.db.enums import ClaimStatus, RecordStatus


_RECORD_TRANSITIONS: Mapping[RecordStatus, frozenset[RecordStatus]] = {
    RecordStatus.DRAFT: frozenset(
        {RecordStatus.PROCESSING, RecordStatus.PUBLISHED, RecordStatus.CANCELLED}
    ),
    RecordStatus.PROCESSING: frozenset(
        {RecordStatus.DRAFT}
    ),
    RecordStatus.PUBLISHED: frozenset(
        {
            RecordStatus.PENDING_HANDOFF,
            RecordStatus.MATCHING_FAILED,
            RecordStatus.CANCELLED,
        }
    ),
    RecordStatus.MATCHING_FAILED: frozenset(
        {RecordStatus.PROCESSING, RecordStatus.PUBLISHED}
    ),
    RecordStatus.PENDING_HANDOFF: frozenset({RecordStatus.CLAIMED}),
    RecordStatus.CLAIMED: frozenset({RecordStatus.CLOSED}),
    RecordStatus.CLOSED: frozenset(),
    RecordStatus.CANCELLED: frozenset(),
}

_CLAIM_TRANSITIONS: Mapping[ClaimStatus, frozenset[ClaimStatus]] = {
    ClaimStatus.SUBMITTED: frozenset(
        {ClaimStatus.VERIFYING}
    ),
    ClaimStatus.VERIFYING: frozenset(
        {
            ClaimStatus.PENDING_HANDOFF,
            ClaimStatus.PENDING_ADMIN_REVIEW,
            ClaimStatus.REJECTED,
            ClaimStatus.LOCKED,
        }
    ),
    ClaimStatus.PENDING_ADMIN_REVIEW: frozenset(
        {ClaimStatus.PENDING_HANDOFF, ClaimStatus.REJECTED}
    ),
    ClaimStatus.PENDING_HANDOFF: frozenset(
        {ClaimStatus.CLAIMED, ClaimStatus.REJECTED}
    ),
    ClaimStatus.REJECTED: frozenset(),
    ClaimStatus.CLAIMED: frozenset(),
    ClaimStatus.LOCKED: frozenset(),
}


def can_transition_record(current: RecordStatus, target: RecordStatus) -> bool:
    """Return whether a record may move from ``current`` to ``target``."""

    try:
        current_status = RecordStatus(current)
        target_status = RecordStatus(target)
    except (TypeError, ValueError):
        return False
    return target_status in _RECORD_TRANSITIONS[current_status]


def can_transition_claim(current: ClaimStatus, target: ClaimStatus) -> bool:
    """Return whether a claim may move from ``current`` to ``target``."""

    try:
        current_status = ClaimStatus(current)
        target_status = ClaimStatus(target)
    except (TypeError, ValueError):
        return False
    return target_status in _CLAIM_TRANSITIONS[current_status]
