# T00 Backend Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest `src/backend` FastAPI scaffold with live and database-readiness health endpoints, verified by unit and functional tests.

**Architecture:** `app.main` creates the FastAPI application and registers the health router. `app.health` owns stable health responses and a replaceable async database check; `app.settings` provides only T00 configuration. Tests replace the check function so T00 does not require PostgreSQL.

**Tech Stack:** Python 3.11+, FastAPI 0.116.1, Pydantic Settings 2.10.1, SQLAlchemy 2.0.41 async, asyncpg 0.30.0, pytest 8.4.1, httpx 0.28.1.

## Global Constraints

- Work only on the backend scope from `task-backend.md` T00.
- Do not restore business code from `codex/t001-health-scaffold` wholesale.
- No production code before a test has failed for the intended missing behavior.
- `/api/health/ready` is canonical; `/ready` is a compatibility alias using the same handler.
- Readiness failures return `503` with `{"status":"unavailable"}` and never expose exception text.
- Do not require a live PostgreSQL instance for the T00 unit or functional checks.

### Task 1: Add failing health tests

**Files:**
- Create: `src/backend/tests/unit/test_health.py`

**Interfaces:**
- Consumes: `app.main.create_app`, `app.health.check_database` (the desired API, not yet implemented).
- Produces: Three executable behavior checks for the live endpoint, ready success, and ready failure.

- [x] **Step 1: Write the failing test**

```python
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
```

- [x] **Step 2: Run the test to verify it fails for the missing feature**

Run from the repository root:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/test_health.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'app'` because the T00 application package does not exist yet.

### Task 2: Add the minimal implementation

**Files:**
- Create: `.gitignore`
- Create: `src/backend/.env.example`
- Create: `src/backend/pyproject.toml`
- Create: `src/backend/app/__init__.py`
- Create: `src/backend/app/settings.py`
- Create: `src/backend/app/health.py`
- Create: `src/backend/app/main.py`

**Interfaces:**
- Consumes: The three tests from Task 1.
- Produces: `create_app()`, `check_database()`, `/api/health/live`, `/api/health/ready`, and `/ready`.

- [x] **Step 1: Add the dependency manifest and settings**

```toml
[project]
name = "lost-found-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "asyncpg==0.30.0",
  "fastapi==0.116.1",
  "pydantic-settings==2.10.1",
  "sqlalchemy[asyncio]==2.0.41",
]

[project.optional-dependencies]
dev = ["httpx==0.28.1", "pytest==8.4.1", "pytest-asyncio==1.1.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "test"
    database_url: str = "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

The repository-level `.gitignore` excludes virtual environments, Python caches, test caches, and local environment files. `src/backend/.env.example` contains only non-secret local defaults.

- [x] **Step 2: Implement the health router and app factory**

```python
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import settings

router = APIRouter()


async def check_database() -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


async def readiness_response() -> JSONResponse:
    try:
        await check_database()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/api/health/live")
async def live_response() -> dict[str, str]:
    return {"status": "ok"}


router.add_api_route("/api/health/ready", readiness_response, methods=["GET"])
router.add_api_route("/ready", readiness_response, methods=["GET"])


def create_app() -> FastAPI:
    application = FastAPI(title="AI Lost and Found API")
    application.include_router(router)
    return application
```

- [x] **Step 3: Run the focused tests to verify Green**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/test_health.py -q
```

Expected: `3 passed`.

### Task 3: Functional verification and evidence

**Files:**
- Create: `evidence/development-records/T00.md`

- [x] **Step 1: Run the focused and full backend test commands**

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/test_health.py -q
../../.venv/bin/pytest -q
```

Expected: both commands exit `0`; the full run contains only the T00 tests.

- [x] **Step 2: Run an application-level functional check**

```bash
cd src/backend
../../.venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app import health
from app.main import create_app

async def available() -> None:
    return None

health.check_database = available
client = TestClient(create_app())
assert client.get('/api/health/live').json() == {'status': 'ok'}
assert client.get('/api/health/ready').json() == {'status': 'ok'}
assert client.get('/ready').json() == {'status': 'ok'}
print('T00 functional check passed')
PY
```

- [x] **Step 3: Record the actual outputs and scope limits**

Write the executed commands, exit codes, test counts, Python/runtime versions, and the fact that no real PostgreSQL was required to `evidence/development-records/T00.md`. Do not mark T01 as started in this record.

- [ ] **Step 4: Commit the completed T00 module**

```bash
git add src/backend/pyproject.toml src/backend/app src/backend/tests/unit/test_health.py evidence/development-records/T00.md
git -c user.name='songziyi' -c user.email='2893663522@qq.com' commit -m "feat(backend): add T00 health scaffold"
```

## Self-review checklist

- T00 requirements map to Tasks 1–3; no authentication, database schema, frontend, or AI requirement is hidden in this plan.
- Every code-changing step includes concrete paths, interfaces, commands, and expected results.
- The test imports and monkeypatch target match the planned module names exactly.
