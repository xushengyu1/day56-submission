from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import AdminDecision, ClaimStatus, ItemType


class ReviewRequestCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class AdminDecisionRequest(BaseModel):
    decision: AdminDecision
    reason: str = Field(min_length=1, max_length=2000)


class ReviewQueueItem(BaseModel):
    id: UUID
    source: str
    item_type: ItemType | None
    status: str
    route_source: str | None = None
    result_code: str | None = None
    created_at: datetime


class ReviewDecisionResult(BaseModel):
    claim_id: UUID
    status: ClaimStatus
    decision: AdminDecision
