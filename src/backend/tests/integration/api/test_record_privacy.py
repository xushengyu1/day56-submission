import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.usefixtures("auth_database_engine")
def test_record_responses_only_contain_safe_public_projection(
    record_api_data: dict[str, object],
) -> None:
    records = record_api_data["records"]
    assert isinstance(records, dict)
    with TestClient(app) as client:
        responses = [
            client.get(
                "/api/records/recent?limit=5",
                headers=record_api_data["owner_headers"],
            ),
            client.get(
                "/api/records/mine?page=1&page_size=20",
                headers=record_api_data["owner_headers"],
            ),
            client.get(
                f"/api/found-records/{records['public_found']}",
                headers=record_api_data["owner_headers"],
            ),
        ]
        identity = client.get(
            f"/api/found-records/{records['identity_found']}",
            headers=record_api_data["owner_headers"],
        )

    assert all(response.status_code == 200 for response in [*responses, identity])
    serialized = json.dumps(
        [response.json() for response in [*responses, identity]],
        ensure_ascii=False,
    )
    for forbidden in [
        "embedding",
        "object_key",
        "SECRET_OBJECT_KEY",
        "hidden_description",
        "SECRET_HIDDEN_DESCRIPTION",
        "number_hmac",
        "SECRET_NUMBER_HMAC",
        "phone_encrypted",
        "SECRET_PHONE_ENCRYPTED",
        "location_normalized",
        "SECRET_NORMALIZED_LOCATION",
    ]:
        assert forbidden not in serialized
    assert identity.json()["number_masked"] == "1101********0010"
