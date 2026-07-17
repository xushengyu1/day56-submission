from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.routes import found_records, uploads
from app.items import service as item_service
from app.main import app
from app.matching.embedding import EmbeddingPort
from app.multimodal.factory import get_multimodal_adapter
from app.multimodal.mock import MockMultimodalAdapter


class RecordingEmbeddingAdapter(EmbeddingPort):
    model = "test-embedding"
    dimension = 3

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class FailingExtractionAdapter(MockMultimodalAdapter):
    async def extract_found_item(self, image_data_url, context):
        raise RuntimeError("provider unavailable")


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


def _register(client: TestClient, suffix: str = "owner") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"found-{suffix}",
            "email": f"found-{suffix}@example.test",
            "password": "password-123",
        },
    )
    assert response.status_code == 201
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_and_upload(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    created = client.post(
        "/api/found-records",
        headers=headers,
        json={"event_time": "2026-07-17T08:00:00Z", "location_area": "LIBRARY"},
    )
    assert created.status_code == 201
    record_id = created.json()["id"]
    uploaded = client.post(
        "/api/uploads",
        headers=headers,
        data={"record_id": record_id, "purpose": "FINDER_ORIGINAL"},
        files={"file": ("item.png", _png(), "image/png")},
    )
    assert uploaded.status_code == 201
    assert set(uploaded.json()) == {"image_asset_id", "purpose"}
    return record_id, uploaded.json()["image_asset_id"]


@pytest.mark.usefixtures("auth_database_engine")
def test_preview_extraction_runs_before_a_draft_exists() -> None:
    app.dependency_overrides[get_multimodal_adapter] = MockMultimodalAdapter
    try:
        with TestClient(app) as client:
            headers = _register(client, "preview")
            extracted = client.post(
                "/api/found-records/extract-preview",
                headers=headers,
                files={"file": ("item.png", _png(), "image/png")},
            )
            records = client.get("/api/records/mine", headers=headers)
    finally:
        app.dependency_overrides.pop(get_multimodal_adapter, None)

    assert extracted.status_code == 200
    assert extracted.json()["suggested_description"]
    assert extracted.json()["status"] == "SUCCEEDED"
    assert records.status_code == 200
    assert records.json()["total"] == 0


@pytest.mark.usefixtures("auth_database_engine")
def test_other_found_flow_keeps_ai_suggestion_separate_and_publishes(
    tmp_path, monkeypatch
) -> None:
    storage = uploads.LocalStorage(tmp_path)
    monkeypatch.setattr(uploads, "_storage", storage)
    monkeypatch.setattr(found_records, "_storage", storage)
    embedding = RecordingEmbeddingAdapter()
    monkeypatch.setattr(item_service, "build_embedding_adapter", lambda: embedding)
    app.dependency_overrides[get_multimodal_adapter] = MockMultimodalAdapter
    try:
        with TestClient(app) as client:
            headers = _register(client)
            record_id, image_asset_id = _create_and_upload(client, headers)
            extracted = client.post(
                f"/api/found-records/{record_id}/extract",
                headers=headers,
                json={"image_asset_id": image_asset_id},
            )
            draft_after_ai = client.get(
                f"/api/found-records/{record_id}", headers=headers
            )
            confirmed = client.put(
                f"/api/found-records/{record_id}/confirmation",
                headers=headers,
                json={
                    "expected_version": 1,
                    "public_category": "OTHER_CATEGORY",
                    "name_public": "黑色折叠伞",
                    "description_public": "图书馆三楼 302 室，伞柄有公开划痕",
                    "event_time": "2026-07-17T08:00:00Z",
                    "location_area": "LIBRARY",
                },
            )
            questions = client.post(
                f"/api/found-records/{record_id}/questions",
                headers=headers,
                json={"hidden_description": "SECRET_INNER_MARK 字母A"},
            )
            published = client.post(
                f"/api/found-records/{record_id}/publish",
                headers=headers,
                json={"expected_version": 2},
            )
    finally:
        app.dependency_overrides.pop(get_multimodal_adapter, None)

    assert extracted.status_code == 200
    assert extracted.json() == {
        "suggested_name": "黑色折叠伞",
        "suggested_description": "一把黑色折叠伞，外观完整。",
        "suggested_item_type": "OTHER",
        "confidence": 0.93,
        "status": "SUCCEEDED",
    }
    assert draft_after_ai.json()["status"] == "DRAFT"
    assert draft_after_ai.json()["version"] == 1
    assert confirmed.json()["version"] == 2
    assert questions.status_code == 200
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    assert embedding.calls == [
        ["黑色折叠伞\n图书馆三楼 302 室，伞柄有公开划痕\n图书馆"]
    ]
    assert "SECRET_INNER_MARK" not in str(embedding.calls)


@pytest.mark.usefixtures("auth_database_engine")
def test_extraction_failure_leaves_draft_editable(tmp_path, monkeypatch) -> None:
    storage = uploads.LocalStorage(tmp_path)
    monkeypatch.setattr(uploads, "_storage", storage)
    monkeypatch.setattr(found_records, "_storage", storage)
    app.dependency_overrides[get_multimodal_adapter] = FailingExtractionAdapter
    try:
        with TestClient(app) as client:
            headers = _register(client, "failure")
            record_id, image_asset_id = _create_and_upload(client, headers)
            failed = client.post(
                f"/api/found-records/{record_id}/extract",
                headers=headers,
                json={"image_asset_id": image_asset_id},
            )
            detail = client.get(f"/api/found-records/{record_id}", headers=headers)
    finally:
        app.dependency_overrides.pop(get_multimodal_adapter, None)

    assert failed.status_code == 400
    assert failed.json()["error_code"] == "MODEL_UNAVAILABLE"
    assert detail.status_code == 200
    assert detail.json()["status"] == "DRAFT"
    assert detail.json()["version"] == 1
