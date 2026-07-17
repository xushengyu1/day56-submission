import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.matching import service as matching_service


class StaticEmbeddingAdapter:
    model = "SECRET_EMBEDDING_MODEL"
    dimension = 3

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.mark.usefixtures("auth_database_engine")
def test_claim_detail_is_limited_to_claimant_finder_and_admin(
    record_api_data: dict[str, object],
) -> None:
    claim_id = record_api_data["claim_id"]
    with TestClient(app) as client:
        claimant = client.get(
            f"/api/claims/{claim_id}", headers=record_api_data["other_headers"]
        )
        finder = client.get(
            f"/api/claims/{claim_id}", headers=record_api_data["owner_headers"]
        )
        admin = client.get(
            f"/api/claims/{claim_id}", headers=record_api_data["admin_headers"]
        )
        unrelated = client.get(
            f"/api/claims/{claim_id}", headers=record_api_data["unrelated_headers"]
        )

    assert claimant.status_code == finder.status_code == admin.status_code == 200
    assert unrelated.status_code == 404
    assert claimant.json()["id"] == str(claim_id)
    assert claimant.json()["status"] == "PENDING_HANDOFF"
    serialized = json.dumps(claimant.json())
    for forbidden in ("submitted_hmac", "answer_key", "object_key", "phone_encrypted"):
        assert forbidden not in serialized


@pytest.mark.usefixtures("auth_database_engine")
def test_identity_failure_returns_real_claim_id_and_attempt_budget(
    record_api_data: dict[str, object], monkeypatch
) -> None:
    monkeypatch.setattr(
        matching_service, "build_embedding_adapter", StaticEmbeddingAdapter
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/lost-records",
            headers=record_api_data["owner_headers"],
            json={
                "public_category": "IDENTITY_CARD",
                "location_area": "LIBRARY",
                "event_time": "2026-07-17T08:00:00Z",
                "name_public": "居民身份证",
                "description_public": "图书馆附近遗失的身份证",
            },
        )
        lost_id = created.json()["id"]
        matched = client.get(
            f"/api/lost-records/{lost_id}/match",
            headers=record_api_data["owner_headers"],
        )
        assert matched.status_code == 200
        candidates = client.get(
            f"/api/lost-records/{lost_id}/candidates",
            headers=record_api_data["owner_headers"],
        )
        candidate_id = candidates.json()[0]["id"]
        failed = client.post(
            f"/api/candidates/{candidate_id}/claims/identity",
            headers=record_api_data["owner_headers"],
            json={"full_number": "110101200001010010"},
        )
        detail = client.get(
            f"/api/claims/{failed.json()['claim_id']}",
            headers=record_api_data["owner_headers"],
        )

    assert failed.status_code == 200
    assert set(failed.json()) == {
        "claim_id",
        "status",
        "result_code",
        "attempt_no",
        "attempts_remaining",
    }
    assert failed.json()["result_code"] == "IDENTITY_NOT_VERIFIED"
    assert failed.json()["attempt_no"] == 1
    assert failed.json()["attempts_remaining"] == 1
    assert detail.status_code == 200
    assert detail.json()["attempt_count"] == 1
    assert detail.json()["attempts_remaining"] == 1
    assert "mismatch" not in json.dumps(failed.json()).casefold()
