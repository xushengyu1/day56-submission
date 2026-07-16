from fastapi.testclient import TestClient

from app import health
from app.main import create_app


def test_live_health_reports_ok() -> None:
    response = TestClient(create_app()).get("/api/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_reports_ok_when_database_check_succeeds(
    monkeypatch,
) -> None:
    async def database_is_available() -> None:
        return None

    monkeypatch.setattr(health, "check_database", database_is_available)

    response = TestClient(create_app()).get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_reports_unavailable_without_exception_details(
    monkeypatch,
) -> None:
    async def database_is_unavailable() -> None:
        raise RuntimeError("secret database hostname")

    monkeypatch.setattr(health, "check_database", database_is_unavailable)

    response = TestClient(create_app()).get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "secret database hostname" not in response.text
