from typing import Any

from app.main import create_app


REQUIRED_OPERATIONS = {
    ("post", "/api/auth/register"),
    ("post", "/api/auth/login"),
    ("post", "/api/auth/refresh"),
    ("get", "/api/auth/me"),
    ("get", "/api/records/recent"),
    ("get", "/api/records"),
    ("get", "/api/records/mine"),
    ("get", "/api/records/mine/summary"),
    ("get", "/api/records/{record_id}/timeline"),
    ("post", "/api/lost-records"),
    ("get", "/api/lost-records/{record_id}"),
    ("get", "/api/lost-records/{record_id}/candidates"),
    ("get", "/api/lost-records/{record_id}/match"),
    ("post", "/api/lost-records/{record_id}/review-requests"),
    ("post", "/api/found-records"),
    ("get", "/api/found-records/{record_id}"),
    ("post", "/api/found-records/{record_id}/extract"),
    ("put", "/api/found-records/{record_id}/confirmation"),
    ("post", "/api/found-records/{record_id}/identity-confirmation"),
    ("post", "/api/found-records/{record_id}/redaction"),
    ("post", "/api/found-records/{record_id}/questions"),
    ("post", "/api/found-records/{record_id}/publish"),
    ("get", "/api/candidates/{candidate_id}"),
    ("get", "/api/candidates/{candidate_id}/questions"),
    ("post", "/api/candidates/{candidate_id}/claims/identity"),
    ("post", "/api/candidates/{candidate_id}/claims/answers"),
    ("get", "/api/claims/{claim_id}"),
    ("post", "/api/claims/{claim_id}/review-requests"),
    ("get", "/api/claims/{claim_id}/contact"),
    ("post", "/api/claims/{claim_id}/handoff-complete"),
    ("get", "/api/admin/reviews"),
    ("get", "/api/admin/reviews/{review_id}"),
    ("post", "/api/admin/reviews/{review_id}/decision"),
    ("get", "/api/admin/audit-events"),
    ("post", "/api/uploads"),
    ("get", "/api/assets/{asset_id}"),
}


def _schemas(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return document["components"]["schemas"]


def test_openapi_contains_every_frontend_operation_and_exact_taxonomy() -> None:
    document = create_app().openapi()
    operations = {
        (method, path)
        for path, path_item in document["paths"].items()
        for method in path_item
        if method in {"get", "post", "put", "patch", "delete"}
    }

    assert REQUIRED_OPERATIONS <= operations
    schemas = _schemas(document)
    assert schemas["PublicCategory"]["enum"] == [
        "ELECTRONICS",
        "IDENTITY_CARD",
        "CLOTHING",
        "STATIONERY",
        "OTHER_CATEGORY",
    ]
    assert schemas["LocationArea"]["enum"] == [
        "DORMITORY",
        "CANTEEN",
        "TEACHING_BUILDING",
        "SCIENCE_BUILDING",
        "LIBRARY",
    ]


def test_openapi_locks_representative_frontend_response_fields() -> None:
    schemas = _schemas(create_app().openapi())
    expected_required = {
        "TokenResponse": {"user", "tokens"},
        "ItemRecordPublic": {
            "id", "owner_user_id", "kind", "item_type", "public_category",
            "location_area", "status", "name_public", "description_public",
            "event_time_public", "location_public", "version", "published_at",
            "created_at", "updated_at",
        },
        "CandidatePublic": {
            "id", "lost_record_id", "found_record_id", "total_score", "level",
            "reason_codes", "conflict_codes", "found_record", "created_at",
        },
        "FoundExtractionResponse": {
            "suggested_name", "suggested_description", "suggested_item_type",
            "confidence", "status",
        },
        "ClaimOutcome": {
            "claim_id", "status", "result_code", "attempt_no", "attempts_remaining",
        },
        "ClaimDetail": {
            "id", "candidate_id", "requester_user_id", "item_type", "status",
            "route_source", "result_code", "attempt_count", "attempts_remaining",
            "created_at", "updated_at", "timeline",
        },
        "ReviewQueueItem": {
            "id", "source", "item_type", "status", "created_at",
        },
        "ReviewDecisionResult": {
            "review_id", "status", "decision",
        },
    }
    for schema_name, required_fields in expected_required.items():
        assert required_fields <= set(schemas[schema_name]["required"]), schema_name

    item_properties = schemas["ItemRecordPublic"]["properties"]
    assert item_properties["public_category"]["$ref"].endswith("/PublicCategory")
    assert item_properties["location_area"]["$ref"].endswith("/LocationArea")
    assert schemas["CandidatePublic"]["properties"]["found_record"]["$ref"].endswith(
        "/ItemRecordPublic"
    )


def test_openapi_documents_the_runtime_canonical_validation_error() -> None:
    """OpenAPI must describe the same 422 body emitted by the registered handler."""
    document = create_app().openapi()
    schemas = _schemas(document)
    problems: list[str] = []
    error_schema = schemas.get("ErrorResponse")
    if error_schema is None:
        problems.append("components.schemas.ErrorResponse is missing")
    elif error_schema.get("required") != ["error_code", "message"]:
        problems.append("ErrorResponse must require error_code and message")
    for path, path_item in document["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            validation = operation.get("responses", {}).get("422")
            if validation is None:
                continue
            schema = validation["content"]["application/json"]["schema"]
            if schema != {"$ref": "#/components/schemas/ErrorResponse"}:
                problems.append(f"{method.upper()} {path} documents 422 as {schema}")

    assert not problems, "\n".join(problems)
