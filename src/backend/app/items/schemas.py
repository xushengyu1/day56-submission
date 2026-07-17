from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import (
    ClaimStatus,
    ItemType,
    LocationArea,
    PublicCategory,
    RecordKind,
    RecordStatus,
)
from app.images.schemas import RedactionRegion


class FoundDraftCreate(BaseModel):
    event_time: datetime
    location_area: LocationArea


class FoundConfirmation(BaseModel):
    expected_version: int = Field(ge=1)
    public_category: PublicCategory
    name_public: str = Field(min_length=1, max_length=160)
    description_public: str = Field(min_length=1, max_length=2000)
    event_time: datetime
    location_area: LocationArea


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


class ItemRecordPublic(BaseModel):
    id: UUID
    owner_user_id: UUID
    kind: RecordKind
    item_type: ItemType
    public_category: PublicCategory
    location_area: LocationArea
    status: RecordStatus
    name_public: str | None
    description_public: str | None
    event_time_public: str | None
    location_public: str | None
    public_image_asset_id: UUID | None = None
    number_masked: str | None = None
    claim_id: UUID | None = None
    version: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RecordPage(BaseModel):
    items: list[ItemRecordPublic]
    page: int
    page_size: int
    total: int
