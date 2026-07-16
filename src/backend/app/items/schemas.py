from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ClaimStatus, ItemType
from app.images.schemas import RedactionRegion


class FoundDraftCreate(BaseModel):
    event_time: datetime
    location_public: str = Field(min_length=1, max_length=255)


class FoundConfirmation(BaseModel):
    expected_version: int = Field(ge=1)
    item_type: ItemType
    name_public: str = Field(min_length=1, max_length=160)
    description_public: str = Field(min_length=1, max_length=2000)


class IdentityConfirmation(BaseModel):
    full_number: str
    digits_confirmed: bool


class OtherQuestionConfirmation(BaseModel):
    hidden_description: str = Field(min_length=1, max_length=4000)


class PublishRequest(BaseModel):
    expected_version: int = Field(ge=1)


class RedactionRequest(BaseModel):
    original_asset_id: UUID
    region: RedactionRegion


class HandoffCompleteRequest(BaseModel):
    confirmation: bool


class HandoffResult(BaseModel):
    claim_id: UUID
    status: ClaimStatus
