import sys
from pathlib import Path

# Allow running this file directly: add backend/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes.auth import router as auth_router
from app.api.routes.found_records import router as found_records_router
from app.api.routes.lost_records import router as lost_records_router
from app.api.routes.candidates import router as candidates_router
from app.api.routes.claims import claim_review_router, router as claims_router
from app.api.routes.handoffs import router as handoffs_router
from app.api.routes.records import router as records_router
from app.api.routes.admin import router as admin_router
from app.api.routes.assets import router as assets_router
from app.health import register_health_routes
from app.api.routes.uploads import router as uploads_router
from app.api.schemas import ErrorResponse


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI Lost and Found API",
        responses={
            422: {
                "model": ErrorResponse,
                "description": "Validation Error",
            }
        },
    )
    register_error_handlers(application)
    register_health_routes(application)
    application.include_router(auth_router)
    application.include_router(found_records_router)
    application.include_router(lost_records_router)
    application.include_router(candidates_router)
    application.include_router(claims_router)
    application.include_router(claim_review_router)
    application.include_router(handoffs_router)
    application.include_router(records_router)
    application.include_router(admin_router)
    application.include_router(uploads_router)
    application.include_router(assets_router)
    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
