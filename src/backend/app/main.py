from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler
from typing import cast

from app.api.errors import APIError, api_error_handler
from app.api.routes.auth import router as auth_router
from app.api.routes.found_records import router as found_records_router
from app.api.routes.lost_records import router as lost_records_router
from app.api.routes.candidates import router as candidates_router
from app.api.routes.claims import claim_review_router, router as claims_router
from app.api.routes.handoffs import router as handoffs_router
from app.api.routes.records import router as records_router
from app.api.routes.admin import router as admin_router
from app.auth.rbac import AuthorizationError
from app.auth.security import AuthenticationError
from app.health import register_health_routes
from app.api.routes.uploads import router as uploads_router


def create_app() -> FastAPI:
    application = FastAPI(title="AI Lost and Found API")

    @application.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        _request: Request, error: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": error.code})

    @application.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _request: Request, error: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": error.code})

    application.add_exception_handler(
        APIError, cast(ExceptionHandler, api_error_handler)
    )
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
    return application


app = create_app()
