# Frontend Backend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing React frontend to the FastAPI/PostgreSQL backend, align the five public categories and five location areas, complete every required user journey, and prove it with unit, contract, integration, and browser E2E tests.

**Architecture:** Make the shared domain and HTTP contract authoritative first, then adapt backend routes and frontend feature pages to that contract. Keep all business access behind focused API modules, use PostgreSQL/pgvector as the state authority, and use deterministic AI/embedding adapters for repeatable tests.

**Tech Stack:** Python 3.12, FastAPI 0.116.1, SQLAlchemy 2.0.41, Alembic 1.16.4, PostgreSQL/pgvector, React 18.3, TypeScript 5.8, Vite 6, Axios 1.7, TanStack Query 5.83, Vitest 3.2, Testing Library 16.3, Playwright Chromium.

## Global Constraints

- Implement against `docs/superpowers/specs/2026-07-17-frontend-backend-integration-design.md`.
- Treat `frontend/` as the UI authority; do not read, modify, stage, or commit `frontend_副本/`.
- Public categories are exactly `ELECTRONICS`, `IDENTITY_CARD`, `CLOTHING`, `STATIONERY`, and `OTHER_CATEGORY`.
- Location areas are exactly `DORMITORY`, `CANTEEN`, `TEACHING_BUILDING`, `SCIENCE_BUILDING`, and `LIBRARY`.
- `public_category` and `location_area` are hard filters; detailed building/classroom text is public description content and participates in embedding.
- `IDENTITY_CARD` maps to `IDENTITY_DOCUMENT`; every other public category maps to `OTHER`.
- Hidden descriptions, verification answers, complete identity numbers, HMAC values, tokens, and private object paths never enter public DTOs, embedding input, normal logs, or URLs.
- Frontend runtime defaults to real API. Mock mode is enabled only by `VITE_USE_MOCK=true` and must display a visible banner.
- Access and refresh tokens stay in memory. A browser page reload requires login again.
- Found publishing uses the approved two-stage flow: local preview, draft/upload/extract, human confirmation, verification setup, explicit publish.
- Automatic tests use deterministic AI and hash embeddings. Real MiMo/DashScope checks are optional smoke tests only when valid keys exist.
- Before changing a known or newly discovered bug, report its root-cause group with reproduction, current file/line evidence, classification, at least two options, recommendation, and modification boundary; wait for explicit user confirmation.
- Use Red → Green → related regression for every behavior change. Do not rewrite passing tests only to hide a regression.
- Touch only files required by this plan. Preserve unrelated user changes.
- Every commit must include only the files listed by its task and must be preceded by the task verification command.

---

## File Responsibility Map

### Backend

- `src/backend/app/db/enums.py`: stable persisted enums.
- `src/backend/app/items/catalog.py`: category-to-verification mapping, Chinese area labels, and canonical public embedding text.
- `src/backend/app/items/models.py`: persisted record taxonomy and indexes.
- `src/backend/app/items/schemas.py`: found-record requests, public record DTOs, and upload/redaction request types.
- `src/backend/app/items/projections.py`: privacy-safe record projection.
- `src/backend/app/items/query_service.py`: recent, location, mine, and detail queries.
- `src/backend/app/matching/schemas.py`: lost create and nested candidate DTOs.
- `src/backend/app/matching/service.py`: lost publishing, hard-filtered candidate generation, and candidate projections.
- `src/backend/app/api/schemas.py`: common API error and pagination structures.
- `src/backend/app/api/errors.py`: one error-code/status/message mapping and exception handlers.
- `src/backend/app/api/routes/*.py`: thin authenticated HTTP adapters only.
- `src/backend/app/reviews/schemas.py` and `service.py`: review summary/detail and source-specific decisions.
- `src/backend/alembic/versions/20260717_0007_matching_taxonomy.py`: public category and location area migration.
- `src/backend/alembic/versions/20260717_0008_auth_contract.py`: username migration.
- `src/backend/alembic/versions/20260717_0009_review_recommendation.py`: unmatched-review recommendation decision support.

### Frontend

- `frontend/src/api/types.ts`: exact frontend representation of backend DTOs.
- `frontend/src/api/catalog.ts`: Chinese labels and stable enum conversion.
- `frontend/src/api/client.ts`: in-memory authentication, one refresh, and request transport.
- `frontend/src/api/errors.ts`: `ApiError` parsing and field-error helpers.
- `frontend/src/api/auth.ts`, `records.ts`, `lostRecords.ts`, `foundRecords.ts`, `claims.ts`, `admin.ts`: focused domain calls.
- `frontend/src/api/sse.ts`: authenticated fetch-based SSE parser.
- `frontend/src/api/mock.ts`: explicit offline adapter only.
- `frontend/src/components/MockModeBanner.tsx`: visible offline-mode indicator.
- `frontend/src/features/**`: page state and rendering; no direct transport or mock imports.
- `frontend/playwright.config.ts` and `frontend/e2e/**`: full-stack test orchestration and synthetic journeys.
- `src/backend/scripts/seed_e2e.py`: reset only the configured E2E database, seed admin, and generate synthetic upload images.

## Spec Coverage Index

| Approved Spec section | Implementing tasks |
|---|---|
| 6. Domain data contract and migration | Tasks 1–3 |
| 7. Hard filters, scoring, Top 5, and failure behavior | Tasks 3 and 8 |
| 8. Auth, record, candidate, claim, review, upload, SSE, and error contracts | Tasks 4–9 and 16 |
| 9. Real frontend API boundary, mock visibility, request state, and authenticated SSE | Tasks 10–14 |
| 10.1 Approved found scheme 2 | Tasks 7 and 13 |
| 10.2 Lost publishing and matching | Tasks 3, 8, and 12 |
| 10.3 Claims, review, and handoff | Tasks 9 and 14 |
| 11. Unit, integration, contract, and Playwright strategy | Tasks 1–18 |
| 12. Root-cause defect confirmation gates | Tasks 1, 4, 10, 15, and Task 18 Step 4 |
| 13. Phased checkpoints | Tasks 1–19 in order |
| 14. Completion evidence | Task 19 |

## Verification Command Conventions

Backend commands run from the repository root:

```bash
cd src/backend
../../.venv/bin/pytest path/to/test.py -q
```

Frontend commands run from `frontend/`:

```bash
npm run test -- tests/file.test.tsx
npm run typecheck
npm run build
```

Database services run from the repository root:

```bash
docker compose up -d postgres
docker compose exec -T postgres pg_isready -U app -d lost_found
```

---

### Task 1: Approve and Implement the Shared Taxonomy

**Files:**
- Modify: `src/backend/app/db/enums.py`
- Create: `src/backend/app/items/catalog.py`
- Create: `src/backend/tests/unit/items/test_catalog.py`
- Modify: `src/backend/tests/integration/db/test_migrations.py`

**Interfaces:**
- Produces: `PublicCategory`, `LocationArea`, `item_type_for(category) -> ItemType`, `location_public_for(area) -> str`, and `build_public_embedding_text(name_public, description_public, location_public) -> str`.
- Consumes: existing `ItemType`.

- [ ] **Step 1: Present defect group A and wait for confirmation**

Run:

```bash
rg -n "class ItemType|left_category=lost_record.item_type|location_public.*casefold|ItemRecord.item_type ==" src/backend/app/db/enums.py src/backend/app/matching/service.py
```

Report that the current backend has only two verification types, compares category using `item_type`, and does not hard-filter the five locations. Offer: (1) add independent persisted taxonomy fields, recommended; (2) encode all categories into `item_type`, rejected because it couples matching to verification. Do not continue until the user confirms group A.

- [ ] **Step 2: Write failing taxonomy unit tests**

Create `test_catalog.py` with exact assertions:

```python
import pytest

from app.db.enums import ItemType, LocationArea, PublicCategory
from app.items.catalog import (
    build_public_embedding_text,
    item_type_for,
    location_public_for,
)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (PublicCategory.ELECTRONICS, ItemType.OTHER),
        (PublicCategory.IDENTITY_CARD, ItemType.IDENTITY_DOCUMENT),
        (PublicCategory.CLOTHING, ItemType.OTHER),
        (PublicCategory.STATIONERY, ItemType.OTHER),
        (PublicCategory.OTHER_CATEGORY, ItemType.OTHER),
    ],
)
def test_public_category_maps_to_verification_type(category, expected):
    assert item_type_for(category) is expected


@pytest.mark.parametrize(
    ("area", "label"),
    [
        (LocationArea.DORMITORY, "宿舍区"),
        (LocationArea.CANTEEN, "食堂"),
        (LocationArea.TEACHING_BUILDING, "教学楼"),
        (LocationArea.SCIENCE_BUILDING, "科教楼"),
        (LocationArea.LIBRARY, "图书馆"),
    ],
)
def test_location_area_has_one_public_label(area, label):
    assert location_public_for(area) == label


def test_embedding_text_contains_public_detail_only():
    text = build_public_embedding_text(
        name_public="黑色折叠伞",
        description_public="教学楼 B 区 302 教室，伞柄有公开划痕",
        location_public="教学楼",
    )
    assert text == "黑色折叠伞\n教学楼 B 区 302 教室，伞柄有公开划痕\n教学楼"
    assert "字母A" not in text
```

Extend `test_database_enum_values_are_stable` with the exact five enum values.

- [ ] **Step 3: Run the tests and verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/items/test_catalog.py tests/integration/db/test_migrations.py::test_database_enum_values_are_stable -q
```

Expected: collection fails because `PublicCategory`, `LocationArea`, and `app.items.catalog` do not exist.

- [ ] **Step 4: Add the minimal enums and catalog functions**

Add:

```python
class PublicCategory(str, Enum):
    ELECTRONICS = "ELECTRONICS"
    IDENTITY_CARD = "IDENTITY_CARD"
    CLOTHING = "CLOTHING"
    STATIONERY = "STATIONERY"
    OTHER_CATEGORY = "OTHER_CATEGORY"


class LocationArea(str, Enum):
    DORMITORY = "DORMITORY"
    CANTEEN = "CANTEEN"
    TEACHING_BUILDING = "TEACHING_BUILDING"
    SCIENCE_BUILDING = "SCIENCE_BUILDING"
    LIBRARY = "LIBRARY"
```

Implement `catalog.py`:

```python
from app.db.enums import ItemType, LocationArea, PublicCategory


_LOCATION_LABELS = {
    LocationArea.DORMITORY: "宿舍区",
    LocationArea.CANTEEN: "食堂",
    LocationArea.TEACHING_BUILDING: "教学楼",
    LocationArea.SCIENCE_BUILDING: "科教楼",
    LocationArea.LIBRARY: "图书馆",
}


def item_type_for(category: PublicCategory) -> ItemType:
    if category is PublicCategory.IDENTITY_CARD:
        return ItemType.IDENTITY_DOCUMENT
    return ItemType.OTHER


def location_public_for(area: LocationArea) -> str:
    return _LOCATION_LABELS[area]


def build_public_embedding_text(
    *, name_public: str, description_public: str, location_public: str
) -> str:
    return "\n".join(
        (name_public.strip(), description_public.strip(), location_public.strip())
    )
```

- [ ] **Step 5: Verify Green and commit**

Run the Step 3 command. Expected: all selected tests pass.

Commit:

```bash
git add src/backend/app/db/enums.py src/backend/app/items/catalog.py src/backend/tests/unit/items/test_catalog.py src/backend/tests/integration/db/test_migrations.py
git commit -m "feat(domain): add public category and location taxonomy"
```

---

### Task 2: Persist and Migrate the Matching Taxonomy

**Files:**
- Create: `src/backend/alembic/versions/20260717_0007_matching_taxonomy.py`
- Modify: `src/backend/app/items/models.py`
- Modify: `src/backend/tests/integration/db/conftest.py`
- Modify: `src/backend/tests/integration/db/test_migrations.py`
- Modify: `src/backend/tests/integration/db/test_model_constraints.py`
- Modify: matching/items integration fixtures that construct `ItemRecord`.

**Interfaces:**
- Consumes: `PublicCategory`, `LocationArea`, `item_type_for`.
- Produces: non-null `ItemRecord.public_category` and `ItemRecord.location_area`, plus `ix_item_records_match_taxonomy`.

- [ ] **Step 1: Write failing model and migration tests**

Add assertions that `item_records` has non-null `public_category` and `location_area`, the new index exists, and inconsistent category/type inserts fail. The constraint test must execute:

```python
with pytest.raises(IntegrityError):
    async with database_engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO item_records "
                "(id, owner_user_id, kind, item_type, public_category, "
                "location_area, status, version) "
                "VALUES (:id, :owner, 'LOST', 'OTHER', 'IDENTITY_CARD', "
                "'LIBRARY', 'DRAFT', 1)"
            ),
            {"id": uuid4(), "owner": seeded_records["user"]},
        )
```

Add a migration-data test that inserts an old `IDENTITY_DOCUMENT / 图书馆` row at revision 0006, upgrades to head, and asserts `IDENTITY_CARD / LIBRARY`.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/db/test_migrations.py tests/integration/db/test_model_constraints.py -q
```

Expected: failures report missing columns, enums, index, and consistency constraint.

- [ ] **Step 3: Add model fields and migration**

Model fields:

```python
public_category: Mapped[PublicCategory] = mapped_column(
    SqlEnum(PublicCategory, name="public_category"), nullable=False
)
location_area: Mapped[LocationArea] = mapped_column(
    SqlEnum(LocationArea, name="location_area"), nullable=False
)
```

The migration must:

1. create both PostgreSQL enum types;
2. add nullable columns;
3. reject a non-null `location_public` outside the five exact Chinese labels with this preflight block:

```python
op.execute(
    """
    DO $$
    DECLARE invalid_values text;
    BEGIN
      SELECT string_agg(DISTINCT location_public, ', ')
      INTO invalid_values
      FROM item_records
      WHERE location_public IS NOT NULL
        AND location_public NOT IN ('宿舍区', '食堂', '教学楼', '科教楼', '图书馆');
      IF invalid_values IS NOT NULL THEN
        RAISE EXCEPTION 'UNMAPPABLE_LOCATION_PUBLIC: %', invalid_values;
      END IF;
    END $$;
    """
)
```
4. backfill `IDENTITY_DOCUMENT` to `IDENTITY_CARD` and every old `OTHER` to `OTHER_CATEGORY`;
5. map the five Chinese labels to the five area enum values;
6. make both columns non-null;
7. replace `ix_item_records_match_filter` with `ix_item_records_match_taxonomy` on `kind, public_category, location_area, status, embedding_model, embedding_dimensions`;
8. add `ck_item_records_category_item_type` enforcing the mapping.

The downgrade must restore the old index, remove the constraint/columns, and drop only the two new enum types.

- [ ] **Step 4: Update every test fixture explicitly**

Every `ItemRecord` constructor must set both fields. Do not infer locations inside fixtures. Example:

```python
ItemRecord(
    owner_user_id=FINDER_ID,
    kind=RecordKind.FOUND,
    item_type=ItemType.OTHER,
    public_category=PublicCategory.OTHER_CATEGORY,
    location_area=LocationArea.LIBRARY,
    status=RecordStatus.PUBLISHED,
)
```

- [ ] **Step 5: Verify migration and regression**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/db tests/integration/items tests/integration/matching -q
```

Expected: all selected tests pass against PostgreSQL.

- [ ] **Step 6: Commit**

```bash
git add src/backend/alembic/versions/20260717_0007_matching_taxonomy.py src/backend/app/items/models.py src/backend/tests
git commit -m "feat(db): persist matching category and location area"
```

---

### Task 3: Enforce Hard Filters and Public-Only Embeddings

**Files:**
- Modify: `src/backend/app/matching/schemas.py`
- Modify: `src/backend/app/matching/scoring.py`
- Modify: `src/backend/app/matching/service.py`
- Modify: `src/backend/app/items/service.py`
- Modify: `src/backend/tests/unit/matching/test_scoring.py`
- Modify: `src/backend/tests/integration/matching/test_candidate_query.py`
- Modify: `src/backend/tests/integration/matching/test_candidate_scoring.py`
- Create: `src/backend/tests/integration/matching/test_taxonomy_filters.py`
- Create: `src/backend/tests/unit/matching/test_embedding_privacy.py`

**Interfaces:**
- Consumes: `build_public_embedding_text` and persisted taxonomy.
- Produces: `create_lost_record(session: AsyncSession, *, owner_user_id: UUID, public_category: PublicCategory, location_area: LocationArea, event_time: datetime, name_public: str, description_public: str, embedding_adapter: EmbeddingPort | None = None) -> ItemRecord` and hard-filtered `generate_candidates(session: AsyncSession, *, lost_record: ItemRecord) -> list[CandidateMatch]`.

- [ ] **Step 1: Write Red tests for both hard filters**

Seed six found records: same category/area, wrong category, wrong area, wrong kind, draft status, and incompatible embedding metadata. Assert only the exact category/area published record becomes a candidate.

Retain the existing Top 5 regression cases and add explicit assertions that equal scores use candidate ID as the stable tie-break and that rerunning matching does not delete a candidate already referenced by a claim.

Use `CaptureEmbeddingAdapter` in `test_embedding_privacy.py` and assert its only input is:

```python
[
    "黑色折叠伞\n教学楼 B 区 302 教室，伞柄有公开划痕\n教学楼"
]
```

The hidden string `伞套内侧字母A` must not appear in adapter calls or candidate snapshots.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/matching/test_embedding_privacy.py tests/integration/matching/test_taxonomy_filters.py -q
```

Expected: tests fail because the service does not accept taxonomy fields and the query lacks the two predicates.

- [ ] **Step 3: Change lost creation and candidate query**

`LostRecordCreate` accepts `public_category` and `location_area`, not caller-supplied `item_type`. `create_lost_record` derives `item_type` and `location_public` and uses `build_public_embedding_text`.

The candidate SQL predicate must include:

```python
ItemRecord.public_category == lost_record.public_category,
ItemRecord.location_area == lost_record.location_area,
ItemRecord.item_type == lost_record.item_type,
```

Pass `public_category.value` to scoring category fields. Since area is already a hard gate, pass `LocationRelation.SAME_LOCATION` for the 20-point structured area score; detailed location remains in semantic similarity.

- [ ] **Step 4: Reuse the canonical embedding builder for found publish**

Replace the local f-string in `publish_found_record` with `build_public_embedding_text`. Keep `hidden_description` confined to verification models and question generation.

- [ ] **Step 5: Verify Green and regression**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/matching tests/integration/matching tests/integration/items -q
```

Expected: all selected tests pass; wrong-category and wrong-area records produce zero candidate rows.

- [ ] **Step 6: Commit**

```bash
git add src/backend/app/matching src/backend/app/items/service.py src/backend/tests/unit/matching src/backend/tests/integration/matching src/backend/tests/integration/items
git commit -m "feat(matching): hard filter category and location area"
```

---

### Task 4: Approve and Standardize the HTTP Error Contract

**Files:**
- Create: `src/backend/app/api/schemas.py`
- Modify: `src/backend/app/api/errors.py`
- Modify: `src/backend/app/main.py`
- Modify: `src/backend/app/api/routes/auth.py`
- Modify: every business route currently raising `HTTPException`.
- Create: `src/backend/tests/unit/api/test_errors.py`
- Create: `src/backend/tests/integration/api/test_error_contract.py`

**Interfaces:**
- Produces: `APIError(error_code, status_code, message, field_errors)` and JSON shape `{error_code,message,field_errors?}`.
- Consumes: `DomainError.code`, `AuthenticationError.code`, `AuthorizationError.code`, and FastAPI request validation errors.

- [ ] **Step 1: Present defect group B and wait for confirmation**

Run:

```bash
rg -n 'content=\{"detail"|HTTPException\(' src/backend/app/api src/backend/app/main.py
rg -n 'interface LoginResponse|interface MatchCandidate|interface ReviewRecord|interface UploadResponse' frontend/src/api/types.ts
```

Report that backend errors use `detail`, auth is flat while frontend expects nested tokens, candidate/admin/upload DTOs differ, and required GET/SSE endpoints are absent. Offer: (1) one canonical contract and missing routes, recommended; (2) page-specific frontend shims, rejected because drift remains. Wait for explicit confirmation.

- [ ] **Step 2: Write failing error contract tests**

Test authentication, authorization, not found, version conflict, validation, and lock errors. Exact assertions:

```python
assert response.json() == {
    "error_code": "VERSION_CONFLICT",
    "message": "记录已被更新，请重新加载",
}
assert validation_response.status_code == 422
assert validation_response.json()["error_code"] == "VALIDATION_ERROR"
assert "email" in validation_response.json()["field_errors"]
```

- [ ] **Step 3: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/api/test_errors.py tests/integration/api/test_error_contract.py -q
```

Expected: current responses contain `detail` and do not expose `error_code`.

- [ ] **Step 4: Implement one mapping**

Define a closed mapping for the codes used by current routes, including `UNAUTHENTICATED=401`, `FORBIDDEN=403`, `NOT_OWNER=403`, `NOT_FOUND=404`, `VERSION_CONFLICT=409`, `ATTEMPT_LOCKED=423`, `VALIDATION_ERROR=422`, and default domain errors at 400. Register handlers for `APIError`, authentication, authorization, request validation, and uncaught `DomainError`.

Route handlers must raise `APIError` or let a mapped domain exception propagate. They must not construct `{"detail": code}`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/api tests/integration/api -q
```

Expected: all API/error tests pass and sensitive values are absent.

Commit:

```bash
git add src/backend/app/api src/backend/app/main.py src/backend/tests/unit/api src/backend/tests/integration/api
git commit -m "feat(api): standardize error responses"
```

---

### Task 5: Align Authentication and Add `/auth/me`

**Files:**
- Create: `src/backend/alembic/versions/20260717_0008_auth_contract.py`
- Modify: `src/backend/app/auth/models.py`
- Modify: `src/backend/app/auth/schemas.py`
- Modify: `src/backend/app/auth/service.py`
- Modify: `src/backend/app/api/routes/auth.py`
- Modify: auth/database fixtures inserting users.
- Modify: `src/backend/tests/unit/auth/test_schemas.py`
- Modify: `src/backend/tests/integration/api/test_auth.py`

**Interfaces:**
- Produces: `UserPublic{id,username,email,role,created_at}` and `TokenResponse{user,tokens}`.
- Produces route: `GET /api/auth/me`.
- Consumes: existing password/JWT/session services.

- [ ] **Step 1: Write failing schema and API tests**

`RegisterRequest` requires a 2–64 character trimmed username. Login/register/refresh must return:

```python
assert set(body) == {"user", "tokens"}
assert body["user"]["username"] == "zhangsan"
assert set(body["tokens"]) == {"access_token", "refresh_token", "token_type"}
```

`GET /api/auth/me` must return the same user projection with a valid access token and 401 without one.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/auth/test_schemas.py tests/integration/api/test_auth.py -q
```

Expected: username is rejected as an extra/missing contract field, response is flat, and `/me` returns 404.

- [ ] **Step 3: Add username migration and model**

The migration adds nullable `username VARCHAR(64)`, backfills `split_part(email, '@', 1)`, makes it non-null, and does not add uniqueness because login identity remains email. Update raw fixture inserts with deterministic synthetic usernames.

- [ ] **Step 4: Nest the token response**

Define:

```python
class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    user: UserPublic
    tokens: AuthTokens
```

Update register/login/refresh service results and add:

```python
@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(user)
```

- [ ] **Step 5: Verify migration/auth regression and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/auth tests/integration/api/test_auth.py tests/integration/api/test_rbac.py tests/integration/db -q
```

Expected: all selected tests pass.

Commit:

```bash
git add src/backend/alembic/versions/20260717_0008_auth_contract.py src/backend/app/auth src/backend/app/api/routes/auth.py src/backend/tests
git commit -m "feat(auth): align frontend session contract"
```

---

### Task 6: Add Public Record Projections, Lists, and Details

**Files:**
- Modify: `src/backend/app/items/schemas.py`
- Create: `src/backend/app/items/projections.py`
- Create: `src/backend/app/items/query_service.py`
- Modify: `src/backend/app/api/routes/records.py`
- Modify: `src/backend/app/api/routes/lost_records.py`
- Modify: `src/backend/app/api/routes/found_records.py`
- Create: `src/backend/tests/integration/api/test_record_queries.py`
- Create: `src/backend/tests/integration/api/test_record_privacy.py`

**Interfaces:**
- Produces: `ItemRecordPublic` and `RecordPage`.
- Produces routes: `GET /api/records/recent`, `GET /api/records`, `GET /api/records/mine`, `GET /api/lost-records/{id}`, `GET /api/found-records/{id}`.
- Consumes: authenticated user and `ItemRecord`.

- [ ] **Step 1: Write failing endpoint and privacy tests**

Seed published, draft, other-user, and both-kind records. Assert:

- recent is newest-first and limit is capped at 20;
- location list uses `location_area` enum and pagination;
- mine is owner-only and optional `kind` filter works;
- published details are readable to authenticated users;
- drafts are owner-only;
- DTO JSON contains no `embedding`, `object_key`, `hidden_description`, `number_hmac`, or `phone_encrypted`;
- a pending-handoff found record in mine includes its related `claim_id` for the finder.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_record_queries.py tests/integration/api/test_record_privacy.py -q
```

Expected: route 404s and projection fields are unavailable.

- [ ] **Step 3: Define focused DTOs and projection**

`ItemRecordPublic` includes real IDs, taxonomy, verification type, status, public fields, `public_image_asset_id`, masked number, optional `claim_id`, version, and timestamps. `project_item_record` may query public redacted asset and related claim, but must return IDs rather than storage paths.

- [ ] **Step 4: Implement query service and thin routes**

Use one query service for ordering, ownership, pagination, and projection. Validate page ≥ 1, page_size 1–50, recent limit 1–20. Keep timeline route unchanged except for common error handling.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_record_queries.py tests/integration/api/test_record_privacy.py tests/integration/handoffs -q
```

Expected: all selected tests pass.

Commit:

```bash
git add src/backend/app/items src/backend/app/api/routes/records.py src/backend/app/api/routes/lost_records.py src/backend/app/api/routes/found_records.py src/backend/tests/integration/api src/backend/tests/integration/handoffs
git commit -m "feat(records): add safe list and detail APIs"
```

---

### Task 7: Complete the Found Draft, Upload, Confirmation, and Publish Contract

**Files:**
- Modify: `src/backend/app/items/schemas.py`
- Modify: `src/backend/app/items/service.py`
- Modify: `src/backend/app/api/routes/found_records.py`
- Modify: `src/backend/app/api/routes/uploads.py`
- Create: `src/backend/app/api/routes/assets.py`
- Modify: `src/backend/app/main.py`
- Modify: `src/backend/tests/integration/items/test_found_draft.py`
- Modify: `src/backend/tests/integration/items/test_found_identity_publish.py`
- Modify: `src/backend/tests/integration/items/test_found_other_publish.py`
- Create: `src/backend/tests/integration/api/test_found_flow_contract.py`
- Create: `src/backend/tests/integration/images/test_asset_download.py`

**Interfaces:**
- Consumes: taxonomy functions, common error contract, image service, multimodal adapter.
- Produces: found draft/AI/confirmation/publish DTOs and `GET /api/assets/{asset_id}` for confirmed public assets or authorized owners.
- Upload response is `{image_asset_id,purpose}`.

- [ ] **Step 1: Write failing two-stage API tests**

Test this exact sequence with deterministic adapters:

1. create draft using `event_time` and `location_area`;
2. upload multipart `FINDER_ORIGINAL` with returned record ID;
3. call extract with JSON `{"image_asset_id": id}`;
4. assert extraction returns suggestions but record remains `DRAFT`;
5. confirm final `public_category`, area, time, name, description, expected version;
6. for OTHER create questions from hidden description; for identity confirm number and redaction;
7. publish with the new version;
8. assert `PUBLISHED` and embedding input contains public detail but no hidden text.

Also assert AI failure leaves the draft editable and returns `MODEL_UNAVAILABLE`.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_found_flow_contract.py tests/integration/images/test_asset_download.py -q
```

Expected: payloads/response names differ, taxonomy fields are missing, and asset download route is absent.

- [ ] **Step 3: Update request schemas and service signatures**

`FoundDraftCreate` receives `event_time` and `location_area`. `FoundConfirmation` receives `expected_version, public_category, name_public, description_public, event_time, location_area`. Derive `item_type` and `location_public` on the server. Extraction request is a Pydantic JSON body containing `image_asset_id`.

Return the extraction draft as `suggested_name`, `suggested_description`, `suggested_item_type`, `confidence`, and `status`. Do not infer an exact non-identity public category from `OTHER`.

- [ ] **Step 4: Align upload and public asset access**

Rename the upload response key to `image_asset_id`. Asset download rules:

- `PUBLIC_REDACTED + PUBLIC + CONFIRMED` is readable by authenticated users;
- private assets are readable only by uploader/record owner during the authorized flow;
- response streams bytes with stored MIME;
- object keys never appear in JSON or headers.

- [ ] **Step 5: Verify found/image regression and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/items tests/integration/images tests/integration/api/test_found_flow_contract.py -q
```

Expected: both OTHER and identity publishing flows pass; privacy checks pass.

Commit:

```bash
git add src/backend/app/items src/backend/app/api/routes src/backend/app/main.py src/backend/tests/integration/items src/backend/tests/integration/images src/backend/tests/integration/api/test_found_flow_contract.py
git commit -m "feat(found): expose confirmed two-stage publishing API"
```

---

### Task 8: Add Authenticated Matching SSE and Nested Candidate DTOs

**Files:**
- Modify: `src/backend/app/matching/schemas.py`
- Modify: `src/backend/app/matching/service.py`
- Modify: `src/backend/app/api/routes/lost_records.py`
- Modify: `src/backend/app/api/routes/candidates.py`
- Create: `src/backend/tests/integration/api/test_matching_sse.py`
- Modify: `src/backend/tests/integration/matching/test_candidate_dto_privacy.py`
- Modify: `src/backend/tests/integration/matching/test_candidate_snapshot.py`

**Interfaces:**
- Produces: nested `CandidatePublic` with `found_record` public projection.
- Produces: authenticated `GET /api/lost-records/{id}/match` SSE.
- Changes: `POST /api/lost-records` creates/publishes a record and returns its ID; matching runs through SSE or an explicit service call.

- [ ] **Step 1: Write failing SSE and DTO tests**

Assert the event order is exactly:

```python
[
    ("progress", "searching", 15),
    ("progress", "filtering", 30),
    ("progress", "embedding", 50),
    ("progress", "matching", 70),
    ("progress", "scoring", 85),
    ("progress", "finalizing", 100),
    ("done", "done", 100),
]
```

Assert 401 without bearer token, 403 for non-owner, and an `error` event with `MATCHING_FAILED` on adapter failure. Candidate detail/list must contain `lost_record_id`, `found_record_id`, `reason_codes`, `conflict_codes`, `found_record`, and `created_at` with no private fields.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_matching_sse.py tests/integration/matching/test_candidate_dto_privacy.py -q
```

Expected: SSE route 404s and candidate DTO is flat.

- [ ] **Step 3: Implement SSE generator and nested projection**

Use `StreamingResponse(media_type="text/event-stream")` and a serializer:

```python
def sse_event(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"
```

Authenticate before constructing the stream. Commit successful matching once; rollback and emit a safe error event on `DomainError`. Do not put tokens in the URL.

- [ ] **Step 4: Verify and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_matching_sse.py tests/integration/matching -q
```

Expected: all selected tests pass and event order is stable.

Commit:

```bash
git add src/backend/app/matching src/backend/app/api/routes/lost_records.py src/backend/app/api/routes/candidates.py src/backend/tests/integration/api/test_matching_sse.py src/backend/tests/integration/matching
git commit -m "feat(matching): stream authenticated candidate progress"
```

---

### Task 9: Complete Claim, Review, Admin, and Handoff DTOs

**Files:**
- Create: `src/backend/alembic/versions/20260717_0009_review_recommendation.py`
- Modify: `src/backend/app/db/enums.py`
- Modify: `src/backend/app/verification/schemas.py`
- Modify: `src/backend/app/verification/service.py`
- Modify: `src/backend/app/reviews/schemas.py`
- Modify: `src/backend/app/reviews/service.py`
- Modify: `src/backend/app/api/routes/claims.py`
- Modify: `src/backend/app/api/routes/admin.py`
- Modify: `src/backend/app/api/routes/handoffs.py`
- Modify: `src/backend/app/api/routes/records.py`
- Modify: `src/backend/tests/integration/verification/**`
- Modify: `src/backend/tests/integration/reviews/**`
- Modify: `src/backend/tests/integration/handoffs/**`
- Create: `src/backend/tests/integration/api/test_claim_detail.py`

**Interfaces:**
- Produces: `GET /api/claims/{claim_id}` with claimant/finder/admin-safe projection.
- Produces: review summary/detail DTOs and source-specific decision.
- Adds `AdminDecision.RECOMMEND_CANDIDATE` for UNMATCHED review only.
- Keeps `APPROVE_TO_HANDOFF` for claim review only and `REJECT` for both.
- Produces real `claim_id` in all verification responses.

- [ ] **Step 1: Write failing claim/review contract tests**

Test:

- claimant, related finder, and admin may read claim detail; unrelated user gets 404;
- identity failure response includes `claim_id`, status, result code, attempt number, and attempts remaining without revealing number mismatch position;
- review queue covers claim and request sources;
- review detail contains safe item/requester/evidence projections;
- UNMATCHED can recommend an existing candidate or reject, but cannot approve directly to handoff;
- CLAIM_REVIEW can approve to handoff or reject, but cannot recommend;
- idempotency produces one decision/audit event;
- mine records expose `claim_id` only to the related party.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/api/test_claim_detail.py tests/integration/reviews tests/integration/handoffs -q
```

Expected: claim detail 404s, review detail is a queue summary, and unmatched decision is unsupported.

- [ ] **Step 3: Add recommendation migration and service rules**

Add PostgreSQL enum value `RECOMMEND_CANDIDATE` and Python enum member. Reuse `ReviewRequest.candidate_snapshot_id` to store the administrator's recommendation. Validate the candidate belongs to the reviewed lost record. Resolving an unmatched request never changes a claim or record to `PENDING_HANDOFF`.

- [ ] **Step 4: Build safe claim/review projections**

Claim projection includes status, attempt count/remaining, result code, created/updated timestamps, and safe timeline. Review detail includes target record/candidate public data and redacted attempt evidence, never submitted HMAC or answer keys.

- [ ] **Step 5: Verify all workflow tests and commit**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/integration/verification tests/integration/reviews tests/integration/handoffs tests/integration/api/test_claim_detail.py -q
```

Expected: all selected tests pass.

Commit:

```bash
git add src/backend/alembic/versions/20260717_0009_review_recommendation.py src/backend/app/db/enums.py src/backend/app/verification src/backend/app/reviews src/backend/app/api/routes src/backend/tests/integration
git commit -m "feat(workflow): complete claim review and handoff contracts"
```

---

### Task 10: Approve and Build the Frontend API Boundary

**Files:**
- Modify: `frontend/src/api/types.ts`
- Create: `frontend/src/api/catalog.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/errors.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/records.ts`
- Create: `frontend/src/api/lostRecords.ts`
- Create: `frontend/src/api/foundRecords.ts`
- Create: `frontend/src/api/claims.ts`
- Create: `frontend/src/api/admin.ts`
- Modify: `frontend/src/api/sse.ts`
- Modify: `frontend/src/api/mock.ts`
- Create: `frontend/src/components/MockModeBanner.tsx`
- Modify: `frontend/src/app/providers.tsx` or `frontend/src/app/App.tsx`
- Create: `frontend/tests/catalog.test.ts`
- Create: `frontend/tests/api-client.test.ts`
- Create: `frontend/tests/sse.test.ts`

**Interfaces:**
- Produces: typed domain functions matching Tasks 5–9.
- Produces: `isMockMode = import.meta.env.VITE_USE_MOCK === "true"`.
- Produces: `streamMatch(lostId, handlers, signal)` using bearer-authenticated fetch.

- [ ] **Step 1: Present defect group C and wait for confirmation**

Run:

```bash
rg -n "const USE_MOCK = true|from '@/api/mock'|lr-001|cl-001|cl-002|MOCK_AI_RESULTS|Math.random" frontend/src
```

Report that runtime is forced to mock, business pages call mock directly, forms navigate with static IDs, and found image selection generates random fake AI output. Offer: (1) typed real API modules with explicit mock adapter, recommended; (2) retain page-level switches, rejected because network failures can silently diverge. Wait for explicit confirmation.

- [ ] **Step 2: Write failing catalog/client/SSE tests**

Catalog assertions must cover all five bidirectional label mappings. Client tests must assert:

- default mode is real;
- tokens are not written to local/session storage;
- one 401 refresh retries once;
- refresh failure clears memory and redirects to login;
- 403/409/422/423 parse to `ApiError`;
- SSE sends Authorization header, parses progress/done/error, and aborts cleanly.

- [ ] **Step 3: Verify Red**

Run:

```bash
cd frontend
npm run test -- tests/catalog.test.ts tests/api-client.test.ts tests/sse.test.ts
```

Expected: missing modules/functions and native `EventSource` cannot satisfy the authorization-header assertion.

- [ ] **Step 4: Define exact frontend DTOs and catalog**

`PublicCategory`, `LocationArea`, auth, item, candidate, claim, review, audit, page, upload, extraction, and error types must match backend JSON field names. Centralize Chinese labels in `catalog.ts`; pages may not define duplicate category/location arrays.

- [ ] **Step 5: Implement the real client and domain modules**

Keep access/refresh tokens in module variables. Domain modules choose real or mock adapter only from `isMockMode`; a rejected real request remains rejected. Implement SSE with `fetch`, `ReadableStreamDefaultReader`, and `AbortSignal`, never native `EventSource` or query-string token.

- [ ] **Step 6: Add visible mock banner**

Render `MockModeBanner` only when `VITE_USE_MOCK=true`. The exact visible text is `Mock 演示模式：当前数据不会写入后端`.

- [ ] **Step 7: Verify and commit**

Run:

```bash
cd frontend
npm run test -- tests/catalog.test.ts tests/api-client.test.ts tests/sse.test.ts
npm run typecheck
```

Expected: selected tests pass. If typecheck still fails only at the pre-existing duplicate `border`, record that output for defect group D rather than modifying it here.

Commit:

```bash
git add frontend/src/api frontend/src/components/MockModeBanner.tsx frontend/src/app frontend/tests/catalog.test.ts frontend/tests/api-client.test.ts frontend/tests/sse.test.ts
git commit -m "feat(frontend): add real typed API boundary"
```

---

### Task 11: Connect Authentication, Home, Location, Details, and My Records

**Files:**
- Modify: `frontend/src/features/auth/api.ts`
- Modify: `frontend/src/features/auth/hooks.ts`
- Modify: `frontend/src/features/auth/LoginPage.tsx`
- Modify: `frontend/src/features/auth/RegisterPage.tsx`
- Modify: `frontend/src/features/home/HomePage.tsx`
- Modify: `frontend/src/features/home/LocationItemsPage.tsx`
- Modify: `frontend/src/features/lost-items/LostItemDetailPage.tsx`
- Modify: `frontend/src/features/found-items/FoundItemDetailPage.tsx`
- Modify: `frontend/src/features/records/MyRecordsPage.tsx`
- Modify: `frontend/tests/auth-routing.test.tsx`
- Modify: `frontend/tests/home.test.tsx`
- Modify: `frontend/tests/owner-flow.test.tsx`
- Create: `frontend/tests/record-pages.test.tsx`

**Interfaces:**
- Consumes: `authApi` and `recordsApi` from Task 10.
- Produces: page queries keyed by real filters/IDs and handoff mutation using returned `claim_id`.

- [ ] **Step 1: Write/adjust tests to assert network-backed behavior**

Use MSW-free Axios/fetch spies or injected domain adapters. Assert login consumes nested tokens, registration submits username, home calls recent and mine, location path maps Chinese label to enum, details load route ID, pagination uses API page values, and finder handoff calls the real claim ID.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd frontend
npm run test -- tests/auth-routing.test.tsx tests/home.test.tsx tests/owner-flow.test.tsx tests/record-pages.test.tsx
```

Expected: current pages call `mockApi` and owner handoff passes an item ID.

- [ ] **Step 3: Replace direct mock calls with domain functions**

Keep current layout/copy unless a test proves it stale. Add loading, empty, and `ErrorState` rendering. Query keys include `locationArea, page, pageSize` or `kind, page`. Invalidate only `records.mine` and related detail after handoff.

- [ ] **Step 4: Verify and commit**

Run the Step 2 command. Expected: all selected tests pass.

Commit:

```bash
git add frontend/src/features/auth frontend/src/features/home frontend/src/features/lost-items/LostItemDetailPage.tsx frontend/src/features/found-items/FoundItemDetailPage.tsx frontend/src/features/records frontend/tests
git commit -m "feat(frontend): connect auth and record browsing"
```

---

### Task 12: Connect Lost Publishing, Matching Progress, and Candidates

**Files:**
- Modify: `frontend/src/features/lost-items/LostCreatePage.tsx`
- Modify: `frontend/src/features/candidates/CandidateListPage.tsx`
- Modify: `frontend/src/features/candidates/CandidateDetailPage.tsx`
- Modify: `frontend/src/features/claims/UnmatchedReviewPage.tsx`
- Create: `frontend/tests/lost-flow.test.tsx`
- Modify: `frontend/tests/owner-flow.test.tsx`

**Interfaces:**
- Consumes: `lostRecordsApi.create`, `upload`, `streamMatch`, `listCandidates`, `getCandidate`, and `createUnmatchedReview`.
- Produces: navigation with backend IDs and category/area mapped payloads.

- [ ] **Step 1: Write failing lost-flow tests**

Assert:

- Chinese category/location submit exact enum values;
- detailed text remains in `description_public`;
- response ID controls navigation;
- optional image uploads with returned record ID;
- SSE progress labels update from actual events;
- abort occurs on unmount;
- stream error renders retry;
- candidate type determines identity vs other claim route;
- unmatched review submits real lost ID and reason.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd frontend
npm run test -- tests/lost-flow.test.tsx tests/owner-flow.test.tsx
```

Expected: static `/lost/lr-001/candidates` and direct mock calls violate assertions.

- [ ] **Step 3: Implement form mutation and authenticated stream**

Validate all required fields before mutation. Create record, upload optional file, navigate with `encodeURIComponent(response.id)`, then let candidate page open `streamMatch`. Candidate list consumes nested `found_record` and maps reason/conflict codes to Chinese in one constant table.

- [ ] **Step 4: Verify and commit**

Run the Step 2 command. Expected: all selected tests pass.

Commit:

```bash
git add frontend/src/features/lost-items/LostCreatePage.tsx frontend/src/features/candidates frontend/src/features/claims/UnmatchedReviewPage.tsx frontend/tests/lost-flow.test.tsx frontend/tests/owner-flow.test.tsx
git commit -m "feat(frontend): connect lost matching journey"
```

---

### Task 13: Implement the Approved Two-Stage Found Wizard

**Files:**
- Modify: `frontend/src/features/found-items/FoundWizardPage.tsx`
- Create: `frontend/src/features/found-items/RedactionRegionPicker.tsx`
- Modify: `frontend/tests/found-wizard.test.tsx`
- Create: `frontend/tests/found-identity-flow.test.tsx`

**Interfaces:**
- Consumes: found draft, upload, extract, confirm, identity confirmation, redaction, question confirmation, and publish API functions.
- Produces: `FoundWizardState = "editing" | "extracting" | "confirming" | "publishing" | "published"`.

- [ ] **Step 1: Write failing two-stage tests**

Assert:

- file selection creates only a local preview and performs zero API calls;
- first submit creates draft, uploads, and extracts in order;
- user-entered non-empty fields are not overwritten by AI suggestions;
- confirmation form remains editable;
- OTHER sends hidden description before publish;
- IDENTITY_CARD sends full number only to identity confirmation, requires explicit digit confirmation, sends a user-selected redaction rectangle, and never displays/persists the full number after success;
- publish occurs only after a second explicit click;
- AI failure stays in editable draft and has retry/manual options.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd frontend
npm run test -- tests/found-wizard.test.tsx tests/found-identity-flow.test.tsx
```

Expected: current image selection starts a timer/random result and submit only navigates home.

- [ ] **Step 3: Implement an explicit state machine in the component**

Use a discriminated state variable and disable buttons during mutations. Merge AI suggestions only into empty public fields. Keep the user's selected `public_category` because an `OTHER` extraction cannot distinguish four public categories.

`RedactionRegionPicker` converts pointer drag coordinates into natural-image integer `{x,y,width,height}` and requires positive width/height before identity publish.

- [ ] **Step 4: Publish and navigate with the real found ID**

After publish success navigate to `/found/{id}`. Clear the full identity number state immediately after identity confirmation and revoke local preview URL on replacement/unmount.

- [ ] **Step 5: Verify and commit**

Run the Step 2 command. Expected: all selected tests pass.

Commit:

```bash
git add frontend/src/features/found-items frontend/tests/found-wizard.test.tsx frontend/tests/found-identity-flow.test.tsx
git commit -m "feat(frontend): implement confirmed found publishing"
```

---

### Task 14: Connect Claims, Review, Admin, Audit, and Progress Pages

**Files:**
- Modify: `frontend/src/features/claims/IdentityClaimForm.tsx`
- Modify: `frontend/src/features/claims/OtherClaimForm.tsx`
- Modify: `frontend/src/features/claims/ClaimProgressPage.tsx`
- Modify: `frontend/src/features/admin/AdminQueuePage.tsx`
- Modify: `frontend/src/features/admin/AdminReviewPage.tsx`
- Modify: `frontend/src/features/admin/AdminAuditPage.tsx`
- Modify: `frontend/tests/claim-errors.test.tsx`
- Modify: `frontend/tests/admin-console.test.tsx`
- Create: `frontend/tests/claim-flow.test.tsx`

**Interfaces:**
- Consumes: claims/admin APIs from Task 10.
- Produces: real claim navigation, safe attempts display, source-specific admin decision UI, and real audit list.

- [ ] **Step 1: Write failing tests for real resources**

Assert candidate/claim IDs come from route/API, OTHER questions come from backend, all required questions are submitted by ID, identity errors show remaining attempts without mismatch details, progress polls claim detail, admin queue/detail use real DTOs, and UNMATCHED shows “推荐候选/驳回” while CLAIM shows “进入交接/驳回”.

- [ ] **Step 2: Verify Red**

Run:

```bash
cd frontend
npm run test -- tests/claim-errors.test.tsx tests/admin-console.test.tsx tests/claim-flow.test.tsx
```

Expected: static question/item data, fixed claim IDs, and static audit content violate assertions.

- [ ] **Step 3: Replace static data and wire mutations**

Load candidate before identity/OTHER rendering. Navigate to `/claims/{response.claim_id}/progress`. Poll claim detail only while status is `VERIFYING` or `PENDING_ADMIN_REVIEW`. Generate a UUID idempotency key once per admin decision and handoff submit, retaining it for retry of the same intent.

- [ ] **Step 4: Verify and commit**

Run the Step 2 command. Expected: all selected tests pass.

Commit:

```bash
git add frontend/src/features/claims frontend/src/features/admin frontend/tests/claim-errors.test.tsx frontend/tests/admin-console.test.tsx frontend/tests/claim-flow.test.tsx
git commit -m "feat(frontend): connect claim and admin workflows"
```

---

### Task 15: Approve and Resolve Baseline Frontend Test/Compiler Defects

**Files:**
- Modify only the exact frontend page/test/setup files proven by this task's failure output.
- Known candidates: `frontend/src/features/candidates/CandidateListPage.tsx`, `frontend/tests/setup.ts`, and the five existing failing test files.

**Interfaces:**
- Produces: clean typecheck and frontend unit suite without weakening assertions.

- [ ] **Step 1: Present defect group D and wait for confirmation**

Run fresh:

```bash
cd frontend
npm run typecheck
npm run test
```

Report exact current failures and lines. Separate defects that remain after Tasks 10–14 from assertions already legitimately updated by those tasks. Offer: (1) remove duplicate style key, install a standards-compatible AbortController setup, and update only obsolete expectations, recommended; (2) suppress compiler/test errors, rejected because it hides regressions. Wait for explicit confirmation.

- [ ] **Step 2: Add a regression assertion before each remaining fix**

For duplicate style keys, typecheck is the regression verifier. For AbortSignal, add a setup test that verifies `new Request("/", {signal: new AbortController().signal})` accepts the signal used by the client. For copy assertions, query semantic roles and the approved current text rather than internal markup.

- [ ] **Step 3: Verify Red**

Run the smallest failing file/command and record the exact failure. A test that already passes is not evidence for a new fix; do not modify it.

- [ ] **Step 4: Apply minimal fixes**

Remove only the duplicate `border` property selected by the intended final style. Use one compatible AbortController implementation in test setup. Update stale expectations only where current approved UI copy or real DTO behavior proves the old assertion incorrect.

- [ ] **Step 5: Verify full frontend suite and commit**

Run:

```bash
cd frontend
npm run typecheck
npm run test
npm run lint
npm run build
```

Expected: all commands exit 0 with zero failed tests and zero TypeScript/ESLint errors.

Commit only actual files:

```bash
git add frontend/src frontend/tests
git commit -m "fix(frontend): resolve verified compiler and test defects"
```

---

### Task 16: Lock the Cross-Language API Contract

**Files:**
- Create: `src/backend/tests/contract/test_frontend_api_contract.py`
- Create: `frontend/tests/api-contract.test.ts`
- Create: `frontend/tests/fixtures/api-contract.ts`
- Modify: response models/routes only if a new mismatch is proven and confirmed under defect group B.

**Interfaces:**
- Consumes: FastAPI OpenAPI document and TypeScript fixtures.
- Produces: executable checks for all required paths, enums, response fields, and standard errors.

- [ ] **Step 1: Write backend OpenAPI contract test**

Assert the path set includes every endpoint listed in Spec section 8.3, including `/api/auth/me`, list/detail routes, matching SSE, claim detail, admin, upload, asset, handoff, and timeline. Assert request/response schemas reference the exact taxonomy enum values.

- [ ] **Step 2: Write frontend fixture contract test**

For each representative JSON fixture, parse with small Zod schemas colocated in `api-contract.test.ts`. Cover auth, item page, candidate, extraction, claim, review detail, audit, upload, SSE data, and all error statuses.

- [ ] **Step 3: Verify tests**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/contract/test_frontend_api_contract.py -q
cd ../../frontend
npm run test -- tests/api-contract.test.ts
```

Expected: both commands pass. Any mismatch is a new integration bug and must be reported before changing the contract.

- [ ] **Step 4: Commit**

```bash
git add src/backend/tests/contract/test_frontend_api_contract.py frontend/tests/api-contract.test.ts frontend/tests/fixtures/api-contract.ts
git commit -m "test(contract): lock frontend backend API"
```

---

### Task 17: Add Deterministic Full-Stack E2E Infrastructure

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/global-setup.ts`
- Create: `frontend/e2e/helpers.ts`
- Create: `src/backend/scripts/seed_e2e.py`
- Modify: `.gitignore`
- Create: `frontend/e2e/auth-home.spec.ts`

**Interfaces:**
- Produces: `npm run test:e2e`, synthetic admin/user setup, synthetic PNGs, and two Playwright web servers.
- Consumes: local PostgreSQL at 55432, backend at 8000, Vite at 5173.

- [ ] **Step 1: Install and configure Playwright**

Run:

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

Add scripts `test:e2e` and `test:e2e:report`. Configure backend web server with `AI_MODE=mock EMBEDDING_MODE=mock` and frontend with `VITE_USE_MOCK=false`.

- [ ] **Step 2: Write the failing auth/home E2E**

Write a failing auth/home E2E before the reset/seed implementation. The spec registers a normal user, logs out/in, verifies protected routing, confirms browser storage contains no token keys, and asserts network calls target `/api` rather than mock data.

- [ ] **Step 3: Verify the E2E harness is Red**

Run:

```bash
docker compose up -d postgres
cd frontend
APP_ENV=e2e DATABASE_URL=postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e npm run test:e2e -- e2e/auth-home.spec.ts
```

Expected: setup exits non-zero with `database "lost_found_e2e" does not exist` because the guarded database creation/seed step is not implemented yet.

- [ ] **Step 4: Create the safe reset/seed implementation and verify Green**

`seed_e2e.py` must refuse to run unless `APP_ENV=e2e` and the target database name ends with `_e2e`. It connects first to the `lost_found` maintenance database, creates `lost_found_e2e` when absent outside a transaction, runs Alembic to head against that target URL, truncates application tables, inserts a synthetic admin through the real password service, and generates two synthetic PNG files containing only geometric shapes and labels `SYNTHETIC OTHER` / `SYNTHETIC ID`.

Run the Step 3 command again. Expected: one Chromium auth/home spec passes.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/playwright.config.ts frontend/e2e src/backend/scripts/seed_e2e.py .gitignore
git commit -m "test(e2e): add deterministic full stack harness"
```

---

### Task 18: Prove All Required User Journeys in Playwright

**Files:**
- Create: `frontend/e2e/matching-other.spec.ts`
- Create: `frontend/e2e/identity-admin.spec.ts`
- Create: `frontend/e2e/security-failures.spec.ts`
- Modify: `frontend/e2e/helpers.ts`
- Modify backend/frontend code only after reporting and confirming any newly reproduced bug.

**Interfaces:**
- Consumes: complete real HTTP frontend/backend and deterministic E2E harness.
- Produces: browser evidence for the Spec 11.4 journeys.

- [ ] **Step 1: Write failing OTHER/matching journey**

Drive the browser through found scheme 2, publish an OTHER item in 教学楼 with `B 区 302 教室` in public description, publish matching and nonmatching lost records, and assert:

- same category/area appears;
- wrong category and wrong area never appear;
- closer detailed text ranks above a different classroom;
- questions load from API;
- correct synthetic answers yield real claim ID and `PENDING_HANDOFF`;
- finder confirms handoff and both records become `CLAIMED`.

- [ ] **Step 2: Write failing identity/admin journey**

Publish a synthetic identity card with explicit number confirmation/redaction, verify one successful claim, then cover two failures leading to lock and a claim-review request. Cover an unmatched request where admin recommends a candidate without directly entering handoff. Verify admin audit entries and role guards.

- [ ] **Step 3: Write failing security/error journey**

Assert unauthorized cross-user details/contact/admin access fail visibly; AI extraction failure stays draft; matching failure shows retry and no mock candidates; 409 and 422 render actionable messages; browser URL/storage/network payloads contain none of the seeded full identity number or tokens.

- [ ] **Step 4: Run Red and report new defects**

Run each spec separately. For any new root cause, stop, show trace/screenshot/network evidence and options, get user confirmation, write the smallest regression test, then fix.

- [ ] **Step 5: Run full E2E Green**

Run:

```bash
cd frontend
APP_ENV=e2e DATABASE_URL=postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e npm run test:e2e
```

Expected: all four Chromium specs pass with zero retries required. Preserve Playwright HTML report path and failed trace only if a defect remains under investigation.

- [ ] **Step 6: Commit**

```bash
git add frontend/e2e
git commit -m "test(e2e): prove integrated lost and found workflows"
```

---

### Task 19: Run Full Regression and Requirement-by-Requirement Audit

**Files:**
- Create: `docs/validation/frontend-backend-integration-results.md`
- Modify: `README.md` only if current startup/test instructions are missing or inaccurate.
- Do not modify business code unless a new defect is reported and confirmed first.

**Interfaces:**
- Produces: reproducible evidence mapping each Spec completion criterion to a current command/output/file/runtime observation.

- [ ] **Step 1: Verify repository boundaries**

Run:

```bash
git status --short
git diff --name-only 600c751f..HEAD
git ls-files frontend_副本
```

Expected: `frontend_副本` remains untracked/unmodified and `git ls-files` returns nothing for it.

- [ ] **Step 2: Verify migrations and backend**

Run:

```bash
docker compose up -d postgres
cd src/backend
../../.venv/bin/alembic upgrade head
../../.venv/bin/pytest -q
../../.venv/bin/ruff check app tests
../../.venv/bin/mypy app
```

Expected: migration exits 0; all backend tests pass; Ruff and mypy exit 0.

- [ ] **Step 3: Verify frontend**

Run:

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

Expected: every command exits 0 and Vitest reports zero failed tests.

- [ ] **Step 4: Verify full-stack E2E**

Run:

```bash
cd frontend
APP_ENV=e2e DATABASE_URL=postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e npm run test:e2e
```

Expected: all required Chromium journeys pass against real FastAPI/PostgreSQL with deterministic adapters.

- [ ] **Step 5: Run static requirement scans**

Run:

```bash
rg -n "from '@/api/mock'|lr-001|cl-001|cl-002|MOCK_AI_RESULTS|Math.random" frontend/src --glob '!api/mock.ts'
rg -n "localStorage|sessionStorage" frontend/src
rg -n "full_number|hidden_description|answer_key|number_hmac|object_key" src/backend/app/api src/backend/app/items/projections.py
```

Expected: first two scans return no forbidden business usage. The backend scan may show request/private model references, but no public response field or logging statement; record each reviewed hit in the results document.

- [ ] **Step 6: Audit every Spec completion criterion**

In `frontend-backend-integration-results.md`, create a table with one row for each item in Spec section 14. Each row includes: requirement, authoritative evidence, result, and remaining limitation. A missing or indirect evidence row is `NOT COMPLETE` and prevents goal completion.

- [ ] **Step 7: Perform optional real-model smoke only when keys exist**

If both real-service keys are present, run one synthetic extraction and one synthetic embedding without storing secrets. If keys are absent, record `SKIPPED — optional, deterministic adapter coverage passed`; this does not block completion.

- [ ] **Step 8: Commit evidence and accurate startup instructions**

```bash
git add docs/validation/frontend-backend-integration-results.md README.md
git commit -m "docs(validation): record full stack integration evidence"
```

Only include `README.md` if it actually changed.

- [ ] **Step 9: Completion gate**

Re-run `git status --short` and inspect the final diff/commit list. Only after every audit row is `PASS` and no required bug remains may the goal be marked complete.
