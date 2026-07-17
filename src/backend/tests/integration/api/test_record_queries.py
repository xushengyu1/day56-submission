from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.usefixtures("auth_database_engine")
def test_recent_records_are_newest_first_and_limit_is_validated(
    record_api_data: dict[str, object],
) -> None:
    records = record_api_data["records"]
    assert isinstance(records, dict)
    with TestClient(app) as client:
        response = client.get(
            "/api/records/recent?limit=2",
            headers=record_api_data["owner_headers"],
        )
        invalid = client.get(
            "/api/records/recent?limit=21",
            headers=record_api_data["owner_headers"],
        )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        str(records["public_found"]),
        str(records["identity_found"]),
    ]
    assert invalid.status_code == 422


@pytest.mark.usefixtures("auth_database_engine")
def test_public_records_filter_by_location_enum_and_paginate(
    record_api_data: dict[str, object],
) -> None:
    with TestClient(app) as client:
        first = client.get(
            "/api/records?location_area=LIBRARY&page=1&page_size=2",
            headers=record_api_data["owner_headers"],
        )
        second = client.get(
            "/api/records?location_area=LIBRARY&page=2&page_size=2",
            headers=record_api_data["owner_headers"],
        )
        invalid = client.get(
            "/api/records?location_area=library",
            headers=record_api_data["owner_headers"],
        )

    assert first.status_code == 200
    assert first.json()["page"] == 1
    assert first.json()["page_size"] == 2
    assert first.json()["total"] == 3
    assert len(first.json()["items"]) == 2
    assert all(item["location_area"] == "LIBRARY" for item in first.json()["items"])
    assert len(second.json()["items"]) == 1
    assert invalid.status_code == 422


@pytest.mark.usefixtures("auth_database_engine")
def test_mine_is_owner_only_and_can_filter_record_kind(
    record_api_data: dict[str, object],
) -> None:
    records = record_api_data["records"]
    assert isinstance(records, dict)
    with TestClient(app) as client:
        response = client.get(
            "/api/records/mine?page=1&page_size=20",
            headers=record_api_data["owner_headers"],
        )
        found = client.get(
            "/api/records/mine?kind=FOUND&page=1&page_size=20",
            headers=record_api_data["owner_headers"],
        )

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {
        str(records["owner_lost"]),
        str(records["owner_draft"]),
        str(records["handoff_found"]),
    }
    assert {item["kind"] for item in found.json()["items"]} == {"FOUND"}
    handoff = next(
        item
        for item in found.json()["items"]
        if item["id"] == str(records["handoff_found"])
    )
    assert handoff["claim_id"] == str(record_api_data["claim_id"])


@pytest.mark.usefixtures("auth_database_engine")
def test_my_summary_counts_only_the_authenticated_owners_records(
    record_api_data: dict[str, object],
) -> None:
    with TestClient(app) as client:
        owner = client.get(
            "/api/records/mine/summary",
            headers=record_api_data["owner_headers"],
        )
        other = client.get(
            "/api/records/mine/summary",
            headers=record_api_data["other_headers"],
        )

    assert owner.status_code == other.status_code == 200
    assert owner.json() == {
        "lost_count": 1,
        "found_count": 2,
        "matched_count": 1,
        "total_count": 3,
    }
    assert other.json() == {
        "lost_count": 2,
        "found_count": 2,
        "matched_count": 1,
        "total_count": 4,
    }


@pytest.mark.usefixtures("auth_database_engine")
def test_published_detail_is_authenticated_and_draft_is_owner_only(
    record_api_data: dict[str, object],
) -> None:
    records = record_api_data["records"]
    assert isinstance(records, dict)
    published_id = records["public_found"]
    draft_id = records["owner_draft"]
    assert isinstance(published_id, UUID)
    assert isinstance(draft_id, UUID)
    with TestClient(app) as client:
        published = client.get(
            f"/api/found-records/{published_id}",
            headers=record_api_data["owner_headers"],
        )
        own_draft = client.get(
            f"/api/found-records/{draft_id}",
            headers=record_api_data["owner_headers"],
        )
        foreign_draft = client.get(
            f"/api/found-records/{draft_id}",
            headers=record_api_data["other_headers"],
        )
        wrong_kind = client.get(
            f"/api/lost-records/{published_id}",
            headers=record_api_data["owner_headers"],
        )

    assert published.status_code == 200
    assert published.json()["public_image_asset_id"] == str(
        record_api_data["public_asset_id"]
    )
    assert own_draft.status_code == 200
    assert foreign_draft.status_code == 404
    assert wrong_kind.status_code == 404
