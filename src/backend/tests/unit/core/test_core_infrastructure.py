from uuid import UUID, uuid4

import pytest

from app.api.errors import APIError
from app.core.clock import utc_now
from app.core.ids import new_request_id, validate_request_id
from app.core.idempotency import hash_request


def test_clock_is_utc_and_request_ids_are_uuid_strings() -> None:
    now = utc_now()
    request_id = new_request_id()

    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0
    assert isinstance(UUID(request_id), UUID)
    assert validate_request_id(request_id)


def test_request_hash_is_stable_for_mapping_order() -> None:
    assert hash_request({"b": 2, "a": 1}) == hash_request({"a": 1, "b": 2})
    assert hash_request({"a": 1}) != hash_request({"a": 2})


def test_api_error_has_stable_code_and_status() -> None:
    error = APIError("FIELD_INVALID", status_code=422)

    assert error.code == "FIELD_INVALID"
    assert error.status_code == 422
    assert "FIELD_INVALID" in str(error)


def test_invalid_request_id_is_rejected() -> None:
    assert not validate_request_id("not-a-uuid")
    with pytest.raises(ValueError):
        APIError("", status_code=400)
