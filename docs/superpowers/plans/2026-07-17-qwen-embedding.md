# Qwen3.7 Text Embedding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace production hash embeddings with validated 1024-dimensional `qwen3.7-text-embedding` vectors while keeping tests offline and providing an idempotent existing-record re-embedding command.

**Architecture:** Business services depend on an asynchronous `EmbeddingPort`. A factory selects a deterministic hash adapter in tests and a DashScope SDK adapter in real mode; records persist the adapter model and dimension, and matching filters incompatible snapshots. A separate transactional service and CLI re-embed existing published records in batches of 20.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, DashScope SDK 1.26.3, SQLAlchemy asyncio, PostgreSQL/pgvector, Pytest.

## Global Constraints

- Real model is exactly `qwen3.7-text-embedding` with dimension `1024`.
- `DASHSCOPE_API_KEY` is environment-only and must never enter Git, logs, exceptions, tests, or evidence.
- Automated tests must not access the network or consume model quota.
- DashScope calls run outside the FastAPI event loop via `asyncio.to_thread`.
- Dense vectors only; no sparse vectors, reranking, task queues, or region auto-detection.
- Preserve untracked workspace files `images.zip` and `images/` unchanged.

---

## File Map

- `app/matching/embedding.py`: embedding port, stable error, normalized hash helper and mock adapter.
- `app/matching/dashscope_embedding.py`: DashScope call and strict response validation.
- `app/matching/embedding_factory.py`: explicit `mock`/`dashscope` adapter selection.
- `app/matching/service.py`: LOST embedding and compatible-candidate filtering.
- `app/items/service.py`: FOUND publication embedding.
- `app/matching/reembed.py`: idempotent batch update of published records.
- `scripts/reembed_records.py`: one-shot async command using the configured adapter.
- `app/settings.py`, `.env.example`, `pyproject.toml`: runtime configuration and pinned SDK dependency.
- `tests/unit/matching/`: adapter, factory, and response-security tests.
- `tests/integration/matching/`, `tests/integration/items/`: persisted snapshot, compatibility, and re-embedding tests.

---

### Task 1: Embedding port, DashScope adapter, and factory

**Files:**
- Modify: `src/backend/app/matching/embedding.py`
- Create: `src/backend/app/matching/dashscope_embedding.py`
- Create: `src/backend/app/matching/embedding_factory.py`
- Modify: `src/backend/app/settings.py`
- Modify: `src/backend/.env.example`
- Modify: `src/backend/pyproject.toml`
- Create: `src/backend/tests/unit/matching/test_dashscope_embedding.py`
- Create: `src/backend/tests/unit/matching/test_embedding_factory.py`
- Modify: `src/backend/tests/contract/test_embedding_contract.py`

**Interfaces:**
- Produces: `EmbeddingPort.embed(texts: list[str]) -> Awaitable[list[list[float]]]`.
- Produces: `EmbeddingError(code: str)` with safe stable codes.
- Produces: `HashEmbeddingAdapter(dimension: int)` with model `mock-hash-v1`.
- Produces: `DashScopeEmbeddingAdapter(model: str, dimension: int, api_key: str)`.
- Produces: `build_embedding_adapter(config: Settings = settings) -> EmbeddingPort`.

- [ ] **Step 1: Add failing adapter tests**

Install the SDK into the current development environment without changing production code:

```bash
cd src/backend
../../.venv/bin/python -m pip install 'dashscope==1.26.3'
```

Create tests that monkeypatch `dashscope.TextEmbedding.call` and never use the network:

```python
@pytest.mark.asyncio
async def test_dashscope_adapter_restores_order_and_validates_dimension(monkeypatch):
    def fake_call(**kwargs):
        assert kwargs["model"] == "qwen3.7-text-embedding"
        assert kwargs["dimension"] == 1024
        return SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={"embeddings": [
                {"text_index": 1, "embedding": [0.2] * 1024},
                {"text_index": 0, "embedding": [0.1] * 1024},
            ]},
        )

    monkeypatch.setattr(dashscope.TextEmbedding, "call", fake_call)
    adapter = DashScopeEmbeddingAdapter(
        model="qwen3.7-text-embedding", dimension=1024, api_key="test-key"
    )
    vectors = await adapter.embed(["lost", "found"])
    assert vectors[0][0] == 0.1
    assert vectors[1][0] == 0.2
```

Add parameterized failures for status 500, missing embeddings, duplicate/missing indexes, non-finite values, 1023 values, empty input, and 21 texts. Assert every raised message is only a stable code and does not include `test-key`, input text, or response payload.

- [ ] **Step 2: Run Red tests**

Run:

```bash
cd src/backend
../../.venv/bin/pytest tests/unit/matching/test_dashscope_embedding.py tests/unit/matching/test_embedding_factory.py -q
```

Expected: collection fails because the DashScope adapter and factory modules do not exist.

- [ ] **Step 3: Add configuration and dependency**

Pin `dashscope==1.26.3` in project dependencies. Replace embedding settings with:

```python
embedding_mode: Literal["mock", "dashscope"] = "mock"
dashscope_api_key: str = ""
embedding_model: str = "qwen3.7-text-embedding"
embedding_dimension: int = 1024
```

Add blank values to `.env.example`:

```dotenv
EMBEDDING_MODE=dashscope
DASHSCOPE_API_KEY=
EMBEDDING_MODEL=qwen3.7-text-embedding
EMBEDDING_DIMENSION=1024
```

Remove obsolete `EMBEDDING_BASE_URL` and `EMBEDDING_API_KEY` settings because this implementation uses the DashScope SDK.

- [ ] **Step 4: Implement the port and mock adapter**

Keep `_hash_vector` and `embed_public_text` as the deterministic implementation used by:

```python
class EmbeddingError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class EmbeddingPort(Protocol):
    model: str
    dimension: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class HashEmbeddingAdapter:
    dimension: int
    model: str = "mock-hash-v1"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise EmbeddingError("EMBEDDING_INPUT_INVALID")
        return embed_public_text(texts, dimension=self.dimension)
```

- [ ] **Step 5: Implement strict DashScope parsing**

`DashScopeEmbeddingAdapter.embed` must call the SDK through `asyncio.to_thread`, passing `model`, `input`, `dimension`, and `api_key`. Parse only mappings, require indexes exactly `0..len(texts)-1`, coerce numeric values to float, reject booleans/non-numbers/non-finite values, and require exactly 1024 values per vector. Convert SDK exceptions and invalid responses to `EmbeddingError("EMBEDDING_UNAVAILABLE")`; input-size failures use `EMBEDDING_INPUT_INVALID`.

The adapter must never include caught exception text or response content in its raised exception.

- [ ] **Step 6: Implement explicit factory validation**

```python
def build_embedding_adapter(config: Settings = settings) -> EmbeddingPort:
    if config.embedding_mode == "mock":
        return HashEmbeddingAdapter(dimension=config.embedding_dimension)
    if (
        config.embedding_model != "qwen3.7-text-embedding"
        or config.embedding_dimension != 1024
    ):
        raise EmbeddingError("EMBEDDING_CONFIG_INVALID")
    if not config.dashscope_api_key:
        raise EmbeddingError("EMBEDDING_API_KEY_MISSING")
    return DashScopeEmbeddingAdapter(
        model=config.embedding_model,
        dimension=config.embedding_dimension,
        api_key=config.dashscope_api_key,
    )
```

Factory tests must verify mock mode needs no Key, real mode rejects a blank Key, and real mode rejects any model or dimension other than the approved values.

- [ ] **Step 7: Install and run Green tests**

Run:

```bash
../../.venv/bin/python -m pip install -e '.[dev]'
../../.venv/bin/pytest tests/unit/matching/test_dashscope_embedding.py tests/unit/matching/test_embedding_factory.py tests/contract/test_embedding_contract.py -q
../../.venv/bin/ruff check app/matching tests/unit/matching tests/contract/test_embedding_contract.py
../../.venv/bin/mypy app/matching tests/unit/matching tests/contract/test_embedding_contract.py
```

Expected: all commands exit 0; no network request occurs.

- [ ] **Step 8: Commit and push Task 1**

```bash
git add src/backend/app/matching src/backend/app/settings.py src/backend/.env.example src/backend/pyproject.toml src/backend/tests/unit/matching src/backend/tests/contract/test_embedding_contract.py
git commit -m "feat(embedding): add validated dashscope adapter"
git push origin feature/backend
```

---

### Task 2: Use adapter snapshots in LOST, FOUND, and matching

**Files:**
- Modify: `src/backend/app/matching/service.py`
- Modify: `src/backend/app/items/service.py`
- Modify: `src/backend/tests/integration/matching/conftest.py`
- Modify: `src/backend/tests/integration/matching/test_candidate_scoring.py`
- Modify: `src/backend/tests/integration/items/test_found_other_publish.py`

**Interfaces:**
- Consumes: `EmbeddingPort`, `EmbeddingError`, `build_embedding_adapter` from Task 1.
- Produces: optional `embedding_adapter: EmbeddingPort | None = None` parameters on `create_lost_record` and `publish_found_record`.
- Produces: persisted `embedding`, `embedding_model`, and `embedding_dimensions` from one adapter response.

- [ ] **Step 1: Write failing service tests**

Define a local fake adapter in integration tests:

```python
class StaticEmbeddingAdapter:
    model = "qwen3.7-text-embedding"
    dimension = 1024

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * self.dimension for _ in texts]
```

Add assertions that LOST creation and FOUND publication with this adapter persist the model and dimension. Add one published FOUND with `embedding_model="mock-hash-v1"` and `embedding_dimensions=8`, generate candidates for a Qwen LOST, and assert no `CandidateMatch` references the incompatible FOUND.

Add an adapter that raises `EmbeddingError("EMBEDDING_UNAVAILABLE")`; assert service raises `DomainError("EMBEDDING_UNAVAILABLE")` before marking FOUND published or adding a LOST record.

- [ ] **Step 2: Run Red integration tests**

Run:

```bash
../../.venv/bin/pytest tests/integration/matching tests/integration/items/test_found_other_publish.py -q
```

Expected: failures show the services do not accept `embedding_adapter` and matching does not filter model/dimension.

- [ ] **Step 3: Add a safe embedding helper in each service**

Resolve `embedding_adapter or build_embedding_adapter()` once per operation. Await `adapter.embed([public_text])`, convert `EmbeddingError` to `DomainError("EMBEDDING_UNAVAILABLE") from None`, and only then mutate record status or add the new LOST record.

Persist:

```python
record.embedding = vectors[0]
record.embedding_model = adapter.model
record.embedding_dimensions = adapter.dimension
```

Do not read `settings.embedding_model` or `settings.embedding_dimension` when writing the snapshot.

- [ ] **Step 4: Filter incompatible candidates in SQL**

Extend the FOUND selection in `generate_candidates` with:

```python
ItemRecord.embedding_model == lost_record.embedding_model,
ItemRecord.embedding_dimensions == lost_record.embedding_dimensions,
```

Keep `_cosine` dimension validation as defense in depth. Update the matching fixture to seed mock FOUND embeddings with `settings.embedding_dimension` and model `mock-hash-v1`.

- [ ] **Step 5: Run focused and regression tests**

Run:

```bash
../../.venv/bin/pytest tests/integration/matching tests/integration/items -q
../../.venv/bin/pytest tests/contract tests/unit/matching -q
../../.venv/bin/ruff check app/items app/matching tests/integration/items tests/integration/matching
../../.venv/bin/mypy app/items app/matching tests/integration/items tests/integration/matching
```

Expected: all commands exit 0.

- [ ] **Step 6: Commit and push Task 2**

```bash
git add src/backend/app/items/service.py src/backend/app/matching/service.py src/backend/tests/integration/items src/backend/tests/integration/matching
git commit -m "feat(matching): persist compatible qwen embedding snapshots"
git push origin feature/backend
```

---

### Task 3: Idempotent existing-record re-embedding command

**Files:**
- Create: `src/backend/app/matching/reembed.py`
- Create: `src/backend/scripts/__init__.py`
- Create: `src/backend/scripts/reembed_records.py`
- Create: `src/backend/tests/integration/matching/test_reembed.py`

**Interfaces:**
- Consumes: `EmbeddingPort.embed`, `ItemRecord`, `RecordStatus`, and `session_factory`.
- Produces: `reembed_published_records(session: AsyncSession, adapter: EmbeddingPort, batch_size: int = 20) -> int`.
- Produces CLI: `python -m scripts.reembed_records` printing only `reembedded=<count>`.

- [ ] **Step 1: Write failing re-embedding tests**

Seed 21 published records marked `mock-hash-v1`/8 and use a counting Qwen adapter. Assert:

```python
updated = await reembed_published_records(session, adapter)
assert updated == 21
assert adapter.batch_sizes == [20, 1]
assert all(record.embedding_model == "qwen3.7-text-embedding" for record in records)
assert all(record.embedding_dimensions == 1024 for record in records)

second = await reembed_published_records(session, adapter)
assert second == 0
assert adapter.batch_sizes == [20, 1]
```

Also assert DRAFT and CLAIMED records remain unchanged because the command targets only `RecordStatus.PUBLISHED`.

- [ ] **Step 2: Run Red test**

Run:

```bash
../../.venv/bin/pytest tests/integration/matching/test_reembed.py -q
```

Expected: collection fails because `app.matching.reembed` does not exist.

- [ ] **Step 3: Implement batch selection and update**

Select published records where embedding is null, model differs, or dimension differs. Order by `ItemRecord.id` for deterministic batches. For each batch, build the same public text used by LOST/FOUND services, await one adapter call, validate returned count, then update all three snapshot fields. Reject `batch_size < 1` and `batch_size > 20` with `ValueError("batch_size must be between 1 and 20")`.

The function does not commit; transaction ownership belongs to its caller.

- [ ] **Step 4: Implement the explicit CLI transaction**

```python
async def main() -> None:
    adapter = build_embedding_adapter()
    async with session_factory() as session:
        async with session.begin():
            count = await reembed_published_records(session, adapter)
    print(f"reembedded={count}")


if __name__ == "__main__":
    asyncio.run(main())
```

The CLI must not print model responses, record text, or credentials.

- [ ] **Step 5: Run Green and idempotency tests**

Run:

```bash
../../.venv/bin/pytest tests/integration/matching/test_reembed.py tests/integration/matching -q
../../.venv/bin/ruff check app/matching/reembed.py scripts tests/integration/matching/test_reembed.py
../../.venv/bin/mypy app/matching/reembed.py scripts tests/integration/matching/test_reembed.py
```

Expected: all commands exit 0; re-embedding calls are exactly `[20, 1]` across both runs.

- [ ] **Step 6: Commit and push Task 3**

```bash
git add src/backend/app/matching/reembed.py src/backend/scripts src/backend/tests/integration/matching/test_reembed.py
git commit -m "feat(embedding): add idempotent qwen reembedding command"
git push origin feature/backend
```

---

### Task 4: Documentation, security scan, and final verification

**Files:**
- Create: `evidence/development-records/qwen-embedding.md`
- Modify: `docs/superpowers/plans/2026-07-17-qwen-embedding.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: reproducible setup and verification evidence without credentials.

- [ ] **Step 1: Run complete quality gates**

Run:

```bash
cd src/backend
../../.venv/bin/pytest -q
../../.venv/bin/ruff check .
../../.venv/bin/mypy .
../../.venv/bin/python -m compileall -q app scripts tests
../../.venv/bin/alembic check
cd ../..
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 2: Verify runtime dependencies and configuration**

Run:

```bash
docker compose up -d --wait postgres ai-mock
docker compose ps
cd src/backend
../../.venv/bin/python -m pip check
EMBEDDING_MODE=mock ../../.venv/bin/python -c 'from app.matching.embedding_factory import build_embedding_adapter; a=build_embedding_adapter(); print(a.model, a.dimension)'
```

Expected: containers are healthy, `pip check` reports no broken requirements, and the final command prints `mock-hash-v1 1024`.

- [ ] **Step 3: Scan tracked files and diffs for credential leakage**

Run:

```bash
git grep -nE 'sk-ws-|DASHSCOPE_API_KEY=[^[:space:]]+' -- . ':!docs/superpowers/plans/2026-07-17-qwen-embedding.md'
git diff --cached | rg -n 'sk-ws-|DASHSCOPE_API_KEY=.+$'
```

Expected: both commands return no matches. Do not place the full Key in the shell command, plan, evidence, or output.

Also inspect `git diff --cached` before every commit and confirm `.env.example` contains only `DASHSCOPE_API_KEY=`.

- [ ] **Step 4: Write evidence and usage instructions**

Record Red/Green commands, test counts, static checks, migration check, batching/idempotency result, and security scan in `evidence/development-records/qwen-embedding.md`. Document these operator commands without a concrete Key:

```bash
export EMBEDDING_MODE=dashscope
read -rsp 'DashScope API Key: ' DASHSCOPE_API_KEY
export DASHSCOPE_API_KEY
export EMBEDDING_MODEL=qwen3.7-text-embedding
export EMBEDDING_DIMENSION=1024
cd src/backend
../../.venv/bin/python -m scripts.reembed_records
```

State that the exposed Key must be revoked and replaced before use.

- [ ] **Step 5: Final commit and push**

```bash
git add docs/superpowers/plans/2026-07-17-qwen-embedding.md evidence/development-records/qwen-embedding.md
git commit -m "docs(embedding): record qwen migration verification"
git push origin feature/backend
```

- [ ] **Step 6: Verify clean handoff**

Run:

```bash
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/feature/backend
```

Expected: only the user's pre-existing untracked `images.zip` and `images/` remain; local and remote commit hashes match.
