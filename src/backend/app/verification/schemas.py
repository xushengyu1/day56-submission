from uuid import UUID

from pydantic import BaseModel

from app.db.enums import ClaimStatus


class IdentityClaimRequest(BaseModel):
    full_number: str


class ClaimOutcome(BaseModel):
    claim_id: UUID
    status: ClaimStatus
    result_code: str
    attempt_no: int
