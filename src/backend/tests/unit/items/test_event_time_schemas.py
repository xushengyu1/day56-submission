import pytest
from pydantic import ValidationError

from app.items.schemas import FoundConfirmation, FoundDraftCreate
from app.matching.schemas import LostRecordCreate


def _payloads(event_time: str):
    return (
        (
            LostRecordCreate,
            {
                "public_category": "ELECTRONICS",
                "location_area": "LIBRARY",
                "event_time": event_time,
                "name_public": "黑色耳机",
                "description_public": "图书馆二楼遗失",
            },
        ),
        (
            FoundDraftCreate,
            {"event_time": event_time, "location_area": "LIBRARY"},
        ),
        (
            FoundConfirmation,
            {
                "expected_version": 1,
                "public_category": "ELECTRONICS",
                "name_public": "黑色耳机",
                "description_public": "图书馆二楼拾得",
                "event_time": event_time,
                "location_area": "LIBRARY",
            },
        ),
    )


@pytest.mark.parametrize(
    "event_time", ("2026-07-17T10:30:00Z", "2026-07-17T10:30:00+08:00")
)
def test_business_event_times_accept_explicit_timezones(event_time: str) -> None:
    for schema, values in _payloads(event_time):
        payload = schema.model_validate(values)
        assert payload.event_time.utcoffset() is not None


def test_business_event_times_reject_naive_datetimes() -> None:
    for schema, values in _payloads("2026-07-17T10:30:00"):
        with pytest.raises(ValidationError):
            schema.model_validate(values)
