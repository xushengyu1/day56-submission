from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.db.enums import LocationArea, PublicCategory
from app.items.schemas import ItemRecordPublic


class LostRecordCreate(BaseModel):
    public_category: PublicCategory
    location_area: LocationArea
    event_time: AwareDatetime
    name_public: str = Field(min_length=1, max_length=160)
    description_public: str = Field(min_length=1, max_length=2000)


class CandidatePublic(BaseModel):
    id: UUID
    lost_record_id: UUID
    found_record_id: UUID
    total_score: float
    level: str
    reason_codes: tuple[str, ...]
    conflict_codes: tuple[str, ...]
    found_record: ItemRecordPublic
    created_at: datetime
