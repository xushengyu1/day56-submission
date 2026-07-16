from fastapi import FastAPI

from app.health import register_health_routes


def create_app() -> FastAPI:
    application = FastAPI(title="AI Lost and Found API")
    register_health_routes(application)
    return application


app = create_app()
