from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import ExtractionStatus, ItemType, QuestionResult


class ExtractionDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_type: ItemType
    name_public: str = Field(min_length=1, max_length=160)
    description_public: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)
    provider: str
    model: str
    version: str
    status: ExtractionStatus
    raw_result_redacted: dict[str, object] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    result: QuestionResult
    confidence: float = Field(ge=0, le=1)
    reason_code: str
    provider: str
    model: str
    version: str
