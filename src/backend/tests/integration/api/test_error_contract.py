from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import claims as claim_routes
from app.db.enums import RecordStatus
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.main import app


def _register(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "contract-user",
            "email": "contract-user@example.test",
            "password": "password-123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    tokens = body.get("tokens", body)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.usefixtures("auth_database_engine")
def test_validation_and_missing_auth_use_canonical_error_shape() -> None:
    with TestClient(app) as client:
        validation = client.post(
            "/api/auth/login",
            json={"email": "invalid-email", "password": "password-123"},
        )
        unauthenticated = client.get(f"/api/candidates/{uuid4()}")

    assert validation.status_code == 422
    assert validation.json()["error_code"] == "VALIDATION_ERROR"
    assert validation.json()["message"] == "请求参数不正确"
    assert "email" in validation.json()["field_errors"]
    assert "detail" not in validation.json()
    assert unauthenticated.status_code == 401
    assert unauthenticated.json() == {
        "error_code": "UNAUTHENTICATED",
        "message": "请先登录",
    }


@pytest.mark.usefixtures("auth_database_engine")
def test_naive_business_event_times_use_canonical_validation_errors() -> None:
    with TestClient(app) as client:
        headers = _register(client)
        lost = client.post(
            "/api/lost-records",
            headers=headers,
            json={
                "public_category": "ELECTRONICS",
                "location_area": "LIBRARY",
                "event_time": "2026-07-17T10:30:00",
                "name_public": "黑色耳机",
                "description_public": "图书馆二楼遗失",
            },
        )
        found = client.post(
            "/api/found-records",
            headers=headers,
            json={
                "event_time": "2026-07-17T10:30:00",
                "location_area": "LIBRARY",
            },
        )
        valid_draft = client.post(
            "/api/found-records",
            headers=headers,
            json={
                "event_time": "2026-07-17T10:30:00+08:00",
                "location_area": "LIBRARY",
            },
        )
        assert valid_draft.status_code == 201
        confirmation = client.put(
            f"/api/found-records/{valid_draft.json()['id']}/confirmation",
            headers=headers,
            json={
                "expected_version": 1,
                "public_category": "ELECTRONICS",
                "name_public": "黑色耳机",
                "description_public": "图书馆二楼拾得",
                "event_time": "2026-07-17T10:30:00",
                "location_area": "LIBRARY",
            },
        )

    for response in (lost, found, confirmation):
        assert response.status_code == 422
        assert response.json()["error_code"] == "VALIDATION_ERROR"
        assert response.json()["message"] == "请求参数不正确"
        assert "event_time" in response.json()["field_errors"]
        assert "detail" not in response.json()


@pytest.mark.usefixtures("auth_database_engine")
def test_authorization_and_not_found_use_canonical_error_shape() -> None:
    with TestClient(app) as client:
        headers = _register(client)
        forbidden = client.get("/api/admin/reviews", headers=headers)
        missing = client.get(f"/api/candidates/{uuid4()}", headers=headers)

    assert forbidden.status_code == 403
    assert forbidden.json() == {
        "error_code": "FORBIDDEN",
        "message": "无权执行此操作",
    }
    assert missing.status_code == 404
    assert missing.json() == {
        "error_code": "NOT_FOUND",
        "message": "资源不存在",
    }


@pytest.mark.usefixtures("auth_database_engine")
def test_version_conflict_uses_canonical_error_shape() -> None:
    with TestClient(app) as client:
        headers = _register(client)
        created = client.post(
            "/api/found-records",
            headers=headers,
            json={
                "event_time": "2026-07-16T10:00:00Z",
                "location_area": "LIBRARY",
            },
        )
        assert created.status_code == 201
        record_id = created.json()["id"]
        confirmation = {
            "expected_version": 1,
            "public_category": "OTHER_CATEGORY",
            "name_public": "黑色折叠伞",
            "description_public": "图书馆三楼 302 室，伞柄有公开划痕",
            "event_time": "2026-07-16T10:00:00Z",
            "location_area": "LIBRARY",
        }
        first = client.put(
            f"/api/found-records/{record_id}/confirmation",
            headers=headers,
            json=confirmation,
        )
        assert first.status_code == 200
        conflict = client.put(
            f"/api/found-records/{record_id}/confirmation",
            headers=headers,
            json=confirmation,
        )

    assert conflict.status_code == 409
    assert conflict.json() == {
        "error_code": "VERSION_CONFLICT",
        "message": "记录已被更新，请重新加载",
    }


@pytest.mark.usefixtures("auth_database_engine")
def test_locked_claim_uses_canonical_error_shape(monkeypatch) -> None:
    async def raise_locked(*_args, **_kwargs):
        raise DomainError("ATTEMPT_LOCKED")

    monkeypatch.setattr(claim_routes, "submit_identity_claim", raise_locked)
    with TestClient(app) as client:
        headers = _register(client)
        response = client.post(
            f"/api/candidates/{uuid4()}/claims/identity",
            headers=headers,
            json={"full_number": "110101200001010010"},
        )

    assert response.status_code == 423
    assert response.json() == {
        "error_code": "ATTEMPT_LOCKED",
        "message": "尝试次数已用尽，请联系管理员",
    }


@pytest.mark.asyncio
async def test_unmatched_review_api_accepts_only_owned_published_lost_records(
    auth_database_engine,
    record_api_data: dict[str, object],
) -> None:
    records = record_api_data["records"]
    assert isinstance(records, dict)
    owner_lost_id = records["owner_lost"]
    public_found_id = records["public_found"]
    assert isinstance(owner_lost_id, UUID)
    assert isinstance(public_found_id, UUID)

    with TestClient(app) as client:
        legal = client.post(
            f"/api/lost-records/{owner_lost_id}/review-requests",
            headers=record_api_data["owner_headers"],
            json={"reason": "当前候选中没有合适物品"},
        )
        found = client.post(
            f"/api/lost-records/{public_found_id}/review-requests",
            headers=record_api_data["other_headers"],
            json={"reason": "FOUND 记录不能提交未匹配复核"},
        )

        async with AsyncSession(auth_database_engine) as session:
            draft_lost = await session.get(ItemRecord, owner_lost_id)
            assert draft_lost is not None
            draft_lost.status = RecordStatus.DRAFT
            await session.commit()

        draft = client.post(
            f"/api/lost-records/{owner_lost_id}/review-requests",
            headers=record_api_data["owner_headers"],
            json={"reason": "DRAFT 记录不能提交未匹配复核"},
        )

    assert legal.status_code == 201
    assert legal.json()["status"] == "OPEN"
    for response in (found, draft):
        assert response.status_code == 404
        assert response.json() == {
            "error_code": "NOT_FOUND",
            "message": "资源不存在",
        }
