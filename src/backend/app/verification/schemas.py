from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ClaimStatus


class IdentityClaimRequest(BaseModel):
    full_number: str


class ClaimOutcome(BaseModel):
    claim_id: UUID
    status: ClaimStatus
    result_code: str
    attempt_no: int
    attempts_remaining: int


class QuestionPublic(BaseModel):
    id: UUID
    question_text: str
    dimension: str


class OtherAnswer(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=2000)


class OtherClaimRequest(BaseModel):
    answers: list[OtherAnswer] = Field(min_length=1)
