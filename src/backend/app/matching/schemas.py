from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ItemType, LocationArea, PublicCategory


class LostRecordCreate(BaseModel):
    public_category: PublicCategory
    location_area: LocationArea
    event_time: datetime
    name_public: str = Field(min_length=1, max_length=160)
    description_public: str = Field(min_length=1, max_length=2000)


class CandidatePublic(BaseModel):
    id: UUID
    found_record_id: UUID
    item_type: ItemType
    public_category: PublicCategory
    location_area: LocationArea
    name_public: str
    description_public: str
    event_time_public: str | None
    location_public: str
    total_score: float
    level: str
    reason_codes: tuple[str, ...]
    conflict_codes: tuple[str, ...]
