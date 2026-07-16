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


def register_health_routes(application: FastAPI) -> None:
    application.include_router(router)
