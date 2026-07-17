from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.routes import assets, found_records, uploads
from app.auth.security import create_access_token
from app.db.enums import UserRole
from app.main import app

from .conftest import USER_ID


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


def _register(client: TestClient, name: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": name,
            "email": f"{name}@example.test",
            "password": "password-123",
        },
    )
    assert response.status_code == 201
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.usefixtures("image_database")
def test_asset_download_enforces_private_and_confirmed_public_access(
    tmp_path, monkeypatch
) -> None:
    storage = uploads.LocalStorage(tmp_path)
    monkeypatch.setattr(uploads, "_storage", storage)
    monkeypatch.setattr(found_records, "_storage", storage)
    monkeypatch.setattr(assets, "_storage", storage)
    with TestClient(app) as client:
        owner_headers = {
            "Authorization": f"Bearer {create_access_token(USER_ID, UserRole.USER)}"
        }
        viewer_headers = _register(client, "asset-viewer")
        created = client.post(
            "/api/found-records",
            headers=owner_headers,
            json={
                "event_time": "2026-07-17T08:00:00Z",
                "location_area": "LIBRARY",
            },
        )
        record_id = created.json()["id"]
        uploaded = client.post(
            "/api/uploads",
            headers=owner_headers,
            data={"record_id": record_id, "purpose": "FINDER_ORIGINAL"},
            files={"file": ("item.png", _png(), "image/png")},
        )
        private_asset_id = uploaded.json()["image_asset_id"]
        owner_private = client.get(
            f"/api/assets/{private_asset_id}", headers=owner_headers
        )
        viewer_private = client.get(
            f"/api/assets/{private_asset_id}", headers=viewer_headers
        )
        redacted = client.post(
            f"/api/found-records/{record_id}/redaction",
            headers=owner_headers,
            json={
                "original_asset_id": private_asset_id,
                "region": {"x": 0, "y": 0, "width": 2, "height": 2},
            },
        )
        public_asset_id = redacted.json()["asset_id"]
        viewer_public = client.get(
            f"/api/assets/{public_asset_id}", headers=viewer_headers
        )

    assert owner_private.status_code == 200
    assert owner_private.content == _png()
    assert owner_private.headers["content-type"] == "image/png"
    assert viewer_private.status_code == 404
    assert viewer_public.status_code == 200
    assert viewer_public.headers["content-type"] == "image/png"
    assert "object" not in str(viewer_public.headers).lower()
