from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from app.database import check_database

router = APIRouter()


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
