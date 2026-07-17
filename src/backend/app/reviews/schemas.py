from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import AdminDecision, ClaimStatus, ItemType
from app.items.schemas import ItemRecordPublic


class ReviewRequestCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class AdminDecisionRequest(BaseModel):
    decision: AdminDecision
    reason: str = Field(min_length=1, max_length=2000)
    candidate_id: UUID | None = None


class ReviewQueueItem(BaseModel):
    id: UUID
    source: str
    item_type: ItemType | None
    status: str
    route_source: str | None = None
    result_code: str | None = None
    created_at: datetime
    item_name: str | None = None
    requester_user_name: str | None = None


class ReviewDecisionResult(BaseModel):
    review_id: UUID
    claim_id: UUID | None = None
    candidate_id: UUID | None = None
    status: str
    decision: AdminDecision


class ClaimTimelineEvent(BaseModel):
    event_type: str
    result_code: str
    created_at: datetime


class ClaimDetail(BaseModel):
    id: UUID
    candidate_id: UUID
    requester_user_id: UUID
    item_type: ItemType
    status: ClaimStatus
    route_source: str | None
    result_code: str | None
    attempt_count: int
    attempts_remaining: int
    created_at: datetime
    updated_at: datetime
    timeline: list[ClaimTimelineEvent]


class ReviewEvidence(BaseModel):
    attempt_no: int
    result_code: str
    answer_summary: dict[str, object] | None
    risk_flag: str | None
    created_at: datetime


class ReviewCandidatePublic(BaseModel):
    id: UUID
    lost_record_id: UUID
    found_record_id: UUID
    total_score: float
    reason_codes: tuple[str, ...]
    conflict_codes: tuple[str, ...]
    found_record: ItemRecordPublic
    created_at: datetime


class ReviewDetail(BaseModel):
    id: UUID
    source: str
    item_type: ItemType | None
    status: str
    route_source: str | None
    result_code: str | None
    requester_user_id: UUID
    requester_user_name: str
    reason: str | None
    created_at: datetime
    lost_record: ItemRecordPublic | None
    candidate: ReviewCandidatePublic | None
    candidates: list[ReviewCandidatePublic] = Field(default_factory=list)
    evidence: list[ReviewEvidence]
