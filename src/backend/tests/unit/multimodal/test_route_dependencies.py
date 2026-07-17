from fastapi.routing import APIRoute

from app.api.routes import claims, found_records
from app.multimodal.factory import get_multimodal_adapter


EXPECTED = (
    (found_records.router, "/api/found-records/extract-preview", "POST"),
    (found_records.router, "/api/found-records/{record_id}/extract", "POST"),
    (found_records.router, "/api/found-records/{record_id}/questions", "POST"),
    (claims.router, "/api/candidates/{candidate_id}/claims/answers", "POST"),
)


def test_multimodal_routes_use_configured_adapter_dependency() -> None:
    for router, path, method in EXPECTED:
        route = next(
            route
            for route in router.routes
            if isinstance(route, APIRoute)
            and route.path == path
            and method in route.methods
        )
        dependency_calls = {
            dependency.call for dependency in route.dependant.dependencies
        }

        assert get_multimodal_adapter in dependency_calls
