import json

import pytest
from fastapi.testclient import TestClient

from app.api.routes import lost_records
from app.items.service import DomainError
from app.main import app
from app.matching import service as matching_service


class StaticEmbeddingAdapter:
    model = "SECRET_EMBEDDING_MODEL"
    dimension = 3

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def _events(body: str) -> list[tuple[str, dict[str, object]]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
        data = next(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
        events.append((event, json.loads(data)))
    return events


def _create_lost(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/lost-records",
        headers=headers,
        json={
            "public_category": "ELECTRONICS",
            "location_area": "LIBRARY",
            "event_time": "2026-07-17T08:00:00Z",
            "name_public": "银色耳机",
            "description_public": "图书馆三楼 302 室附近遗失",
        },
    )
    assert response.status_code == 201
    assert set(response.json()) == {"id", "status"}
    return response.json()["id"]


@pytest.mark.usefixtures("auth_database_engine")
def test_matching_stream_is_authenticated_ordered_and_builds_nested_candidates(
    record_api_data: dict[str, object], monkeypatch
) -> None:
    monkeypatch.setattr(
        matching_service, "build_embedding_adapter", StaticEmbeddingAdapter
    )
    with TestClient(app) as client:
        lost_id = _create_lost(client, record_api_data["owner_headers"])
        unauthenticated = client.get(f"/api/lost-records/{lost_id}/match")
        foreign = client.get(
            f"/api/lost-records/{lost_id}/match",
            headers=record_api_data["other_headers"],
        )
        streamed = client.get(
            f"/api/lost-records/{lost_id}/match",
            headers=record_api_data["owner_headers"],
        )
        candidates = client.get(
            f"/api/lost-records/{lost_id}/candidates",
            headers=record_api_data["owner_headers"],
        )

    assert unauthenticated.status_code == 401
    assert foreign.status_code == 403
    assert streamed.status_code == 200
    assert streamed.headers["content-type"].startswith("text/event-stream")
    assert [
        (event, data["stage"], data["progress"])
        for event, data in _events(streamed.text)
    ] == [
        ("progress", "searching", 15),
        ("progress", "filtering", 30),
        ("progress", "embedding", 50),
        ("progress", "matching", 70),
        ("progress", "scoring", 85),
        ("progress", "finalizing", 100),
        ("done", "done", 100),
    ]
    assert candidates.status_code == 200
    candidate = candidates.json()[0]
    assert set(candidate) == {
        "id",
        "lost_record_id",
        "found_record_id",
        "total_score",
        "level",
        "reason_codes",
        "conflict_codes",
        "found_record",
        "created_at",
    }
    assert candidate["lost_record_id"] == lost_id
    assert candidate["found_record"]["id"] == candidate["found_record_id"]


@pytest.mark.usefixtures("auth_database_engine")
def test_matching_failure_emits_safe_error_and_marks_record_failed(
    record_api_data: dict[str, object], monkeypatch
) -> None:
    monkeypatch.setattr(
        matching_service, "build_embedding_adapter", StaticEmbeddingAdapter
    )

    async def fail_matching(*_args, **_kwargs):
        raise DomainError("EMBEDDING_UNAVAILABLE")

    with TestClient(app) as client:
        lost_id = _create_lost(client, record_api_data["owner_headers"])
        monkeypatch.setattr(lost_records, "generate_candidates", fail_matching)
        streamed = client.get(
            f"/api/lost-records/{lost_id}/match",
            headers=record_api_data["owner_headers"],
        )
        detail = client.get(
            f"/api/lost-records/{lost_id}",
            headers=record_api_data["owner_headers"],
        )

    event, data = _events(streamed.text)[-1]
    assert event == "error"
    assert data == {
        "stage": "failed",
        "progress": 100,
        "error_code": "MATCHING_FAILED",
    }
    assert detail.json()["status"] == "MATCHING_FAILED"
