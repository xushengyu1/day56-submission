# MiMo V2.5 Real Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route image extraction, verification-question generation, and claimant-answer verification through Xiaomi `mimo-v2.5` in real mode while retaining deterministic offline mock mode.

**Architecture:** Convert the existing multimodal port and its callers to async, replace the legacy custom HTTP payload with `AsyncOpenAI` Chat Completions, and select the adapter through one cached factory. Private local images are read at the route boundary and converted to an in-memory Base64 Data URL before the real adapter is called.

**Tech Stack:** Python 3.11+, FastAPI, OpenAI Python SDK 2.45.0, Pydantic, httpx MockTransport, pytest/pytest-asyncio, SQLAlchemy asyncio.

## Global Constraints

- Real API base URL is exactly `https://api.xiaomimimo.com/v1` by default.
- Image and text model defaults are exactly `mimo-v2.5`.
- `AI_MODE=mock` remains the default and never requires an API Key or network access.
- `MIMO_API_KEY` is read only from the environment and is never committed, logged, echoed, or written into test fixtures.
- Private images are converted to `data:image/...;base64,...` only in memory and are never persisted or included in errors.
- Chat Completions use `max_completion_tokens=1024`, the configured timeout, and at most one SDK retry.
- Existing `MATCH` confidence threshold `0.8` and all existing domain DTOs remain unchanged.
- Only `jpg`, `jpeg`, `png`, and `webp` image suffixes are accepted.
- User-owned untracked `images/` and `images.zip` remain untouched.

## Live Verification Adjustment

真实 API 联调确认 `mimo-v2.5` 默认思考模式会让推理内容计入 `max_completion_tokens`，可能导致结构化 JSON 被截断，因此所有调用固定发送 `thinking.type=disabled`。问题生成只让模型返回 `question_text` 和 `answer_key`；服务端确定性地分配内部维度、标记开放题，并替换任何包含参考答案的问题文本。该归一化不发起额外模型请求，题目数量和必填文本仍执行严格校验。

---

### Task 1: Make the multimodal contract and business callers asynchronous

**Files:**
- Modify: `src/backend/app/multimodal/ports.py`
- Modify: `src/backend/app/multimodal/mock.py`
- Modify: `src/backend/app/items/service.py`
- Modify: `src/backend/app/verification/service.py`
- Modify: `src/backend/tests/contract/test_extraction_contract.py`
- Modify: `src/backend/tests/contract/test_question_contract.py`
- Modify: `src/backend/tests/contract/test_verification_contract.py`
- Modify: `src/backend/tests/integration/verification/test_other_model_failure.py`

**Interfaces:**
- Consumes: Existing `ExtractionDraft`, `QuestionSetDraft`, `VerificationResult`, and `ModelAdapterError`.
- Produces: Async `MultimodalPort.extract_found_item`, `generate_questions`, and `verify_answers`; async-compatible mock and service callers used by every later task.

- [ ] **Step 1: Convert contract and failure tests to await the adapter**

Use `pytest.mark.asyncio` and await every mock operation. The extraction contract becomes:

```python
import pytest

from app.db.enums import ExtractionStatus, ItemType
from app.multimodal.mock import MockMultimodalAdapter


@pytest.mark.asyncio
async def test_extraction_contract_returns_valid_public_draft() -> None:
    draft = await MockMultimodalAdapter().extract_found_item(
        "fixture://umbrella.png", {"scenario": "umbrella"}
    )

    assert draft.status is ExtractionStatus.SUCCEEDED
    assert draft.item_type is ItemType.OTHER
    assert draft.name_public
    assert draft.description_public
    assert 0 <= draft.confidence <= 1
    assert draft.provider == "mock"
    assert "110101200001010010" not in str(draft.raw_result_redacted)
```

Replace the question contract body with:

```python
import pytest

from app.multimodal.mock import MockMultimodalAdapter
from app.verification.other import validate_question_set


@pytest.mark.asyncio
async def test_question_contract_is_compatible_with_t02_validation() -> None:
    questions = await MockMultimodalAdapter().generate_questions(
        "黑色折叠伞，底部有一道裂纹"
    )

    validation = validate_question_set(questions)

    assert validation.valid
    assert 2 <= len(questions.questions) <= 3
    assert all(question.is_open_ended for question in questions.questions)
```

Replace the verification contract body with:

```python
import pytest

from app.db.enums import QuestionResult
from app.multimodal.mock import MockMultimodalAdapter


@pytest.mark.asyncio
async def test_verification_contract_is_conservative_for_match_partial_and_conflict() -> None:
    adapter = MockMultimodalAdapter()
    questions = await adapter.generate_questions("黑色折叠伞，底部有一道裂纹")
    answers = {
        question.dimension: question.answer_key
        for question in questions.questions
    }

    matched = await adapter.verify_answers(questions, answers)
    partial = await adapter.verify_answers(
        questions, {next(iter(answers)): "不确定"}
    )
    conflict = await adapter.verify_answers(
        questions,
        {question.dimension: "完全不同" for question in questions.questions},
    )

    assert matched.result is QuestionResult.MATCH
    assert matched.confidence >= 0.8
    assert partial.result is QuestionResult.UNDETERMINED
    assert partial.confidence < 0.8
    assert conflict.result is QuestionResult.CONFLICT
```

Change the failure adapter to:

```python
class FailingAdapter(MockMultimodalAdapter):
    async def verify_answers(self, question_set, answers):
        raise ModelAdapterError("MODEL_UNAVAILABLE")
```

- [ ] **Step 2: Run the focused tests and verify the red state**

Run:

```bash
cd src/backend
pytest tests/contract/test_extraction_contract.py tests/contract/test_question_contract.py tests/contract/test_verification_contract.py tests/integration/verification/test_other_model_failure.py -q
```

Expected: contract tests fail with `TypeError` because the current mock methods return non-awaitable DTOs.

- [ ] **Step 3: Convert the port, mock, and all three service calls to async**

Define the protocol methods as:

```python
class MultimodalPort(Protocol):
    async def extract_found_item(
        self, image_data_url: str, context: Mapping[str, object]
    ) -> ExtractionDraft: ...

    async def generate_questions(
        self, hidden_description: str
    ) -> QuestionSetDraft: ...

    async def verify_answers(
        self, question_set: QuestionSetDraft, answers: Mapping[str, str]
    ) -> VerificationResult: ...
```

Change the three `MockMultimodalAdapter` method declarations from `def` to `async def` without changing their deterministic bodies. Update the service calls exactly as follows:

```python
draft = await adapter.extract_found_item(
    image_ref, {"record_id": str(record_id)}
)
```

```python
draft = await adapter.generate_questions(hidden_description)
```

```python
verification = await adapter.verify_answers(draft, answer_by_dimension)
```

- [ ] **Step 4: Run async contract and service tests**

Run:

```bash
cd src/backend
pytest tests/contract tests/integration/items/test_found_other_publish.py tests/integration/verification/test_other_claim_routing.py tests/integration/verification/test_other_model_failure.py -q
```

Expected: all selected tests pass; no `coroutine was never awaited` warnings appear.

- [ ] **Step 5: Commit the async contract**

```bash
git add src/backend/app/multimodal/ports.py src/backend/app/multimodal/mock.py src/backend/app/items/service.py src/backend/app/verification/service.py src/backend/tests/contract src/backend/tests/integration/verification/test_other_model_failure.py
git commit -m "refactor(multimodal): make adapter contract async"
```

---

### Task 2: Replace the legacy payload with the real OpenAI-compatible MiMo adapter

**Files:**
- Modify: `src/backend/pyproject.toml`
- Modify: `src/backend/app/multimodal/openai_compatible.py`
- Modify: `src/backend/tests/unit/multimodal/test_openai_compatible.py`

**Interfaces:**
- Consumes: Async `MultimodalPort` signatures from Task 1 and OpenAI-compatible Chat Completions.
- Produces: `OpenAICompatibleAdapter(base_url, api_key, multimodal_model, text_model, version, client=None, timeout_seconds=20)` with strict JSON parsing and stable error mapping.

- [ ] **Step 1: Add failing request-shape, parsing, privacy, and error tests**

Add `openai==2.45.0` to the main dependency list, install the editable backend, and replace the old synchronous tests with async SDK transport tests. Use this response helper and adapter helper:

```python
import json

import httpx
from openai import AsyncOpenAI
import pytest

from app.db.enums import QuestionResult
from app.multimodal.openai_compatible import OpenAICompatibleAdapter
from app.multimodal.ports import ModelAdapterError
from app.verification.other import QuestionDraft, QuestionSetDraft


def _completion(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "mimo-v2.5",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
        },
    )


def _adapter(handler) -> OpenAICompatibleAdapter:
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = AsyncOpenAI(
        api_key="synthetic-test-key",
        base_url="https://api.example.test/v1",
        http_client=http_client,
        max_retries=1,
    )
    return OpenAICompatibleAdapter(
        base_url="https://api.example.test/v1",
        api_key="synthetic-test-key",
        multimodal_model="mimo-v2.5",
        text_model="mimo-v2.5",
        version="openai-chat-completions-v1",
        client=client,
    )
```

The first test captures `json.loads(request.content)` and asserts:

```python
@pytest.mark.asyncio
async def test_extract_sends_openai_multimodal_messages_and_redacts_raw_data() -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return _completion(
            json.dumps(
                {
                    "item_type": "OTHER",
                    "name_public": "黑色折叠伞",
                    "description_public": "外观完整",
                    "confidence": 0.9,
                    "id_number_candidate": "110101200001010010",
                }
            )
        )

    adapter = _adapter(handler)
    try:
        result = await adapter.extract_found_item(
            "data:image/png;base64,c3ludGhldGlj", {"record_id": "record-1"}
        )
    finally:
        await adapter.client.close()

    assert requests[0]["model"] == "mimo-v2.5"
    assert requests[0]["max_completion_tokens"] == 1024
    user_content = requests[0]["messages"][1]["content"]
    assert user_content[0]["type"] == "image_url"
    assert user_content[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert result.name_public == "黑色折叠伞"
    assert "110101200001010010" not in str(result.raw_result_redacted)
```

Add the question and verification test:

```python
@pytest.mark.asyncio
async def test_text_operations_send_reference_answers_and_parse_fenced_json() -> None:
    requests: list[dict[str, object]] = []
    responses = iter(
        [
            _completion(
                """```json
                {"questions":[
                  {"question_text":"请描述伞柄底部细节。","answer_key":"一道裂纹","dimension":"handle","is_open_ended":true},
                  {"question_text":"请描述伞套内侧标记。","answer_key":"字母A","dimension":"cover","is_open_ended":true}
                ]}
                ```"""
            ),
            _completion(
                json.dumps(
                    {
                        "result": "MATCH",
                        "confidence": 0.95,
                        "reason_code": "ALL_KEY_ANSWERS_MATCH",
                    }
                )
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return next(responses)

    adapter = _adapter(handler)
    try:
        questions = await adapter.generate_questions(
            "伞柄底部有一道裂纹，伞套内侧写有字母A"
        )
        answers = {
            question.dimension: question.answer_key
            for question in questions.questions
        }
        result = await adapter.verify_answers(questions, answers)
    finally:
        await adapter.client.close()

    verification_text = requests[1]["messages"][1]["content"]
    assert "一道裂纹" in verification_text
    assert "字母A" in verification_text
    assert result.result is QuestionResult.MATCH
```

Add explicit failure tests:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "content", "expected_code", "expected_calls"),
    [
        (401, None, "MODEL_HTTP_ERROR", 1),
        (503, None, "MODEL_UNAVAILABLE", 2),
        (200, "not-json", "MODEL_RESPONSE_INVALID", 1),
    ],
)
async def test_adapter_maps_provider_failures_without_leaking_payloads(
    status_code: int,
    content: str | None,
    expected_code: str,
    expected_calls: int,
) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if status_code == 200:
            return _completion(content or "")
        return httpx.Response(status_code, json={"error": {"message": "synthetic"}})

    adapter = _adapter(handler)
    try:
        with pytest.raises(ModelAdapterError, match=expected_code) as caught:
            await adapter.extract_found_item(
                "data:image/png;base64,c2VjcmV0LWltYWdl", {}
            )
    finally:
        await adapter.client.close()

    assert calls == expected_calls
    assert "c2VjcmV0LWltYWdl" not in str(caught.value)
```

- [ ] **Step 2: Run the adapter tests and verify the red state**

Run:

```bash
cd src/backend
python -m pip install -e '.[dev]'
pytest tests/unit/multimodal/test_openai_compatible.py -q
```

Expected: tests fail because the current adapter is synchronous, accepts `model` instead of separate models, and sends legacy `operation/input` fields.

- [ ] **Step 3: Implement the async Chat Completions adapter**

Rewrite the adapter around these exact primitives:

```python
from __future__ import annotations

from collections.abc import Mapping
import json
import re

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.db.enums import ExtractionStatus, ItemType, QuestionResult
from app.multimodal.ports import ModelAdapterError
from app.multimodal.schemas import ExtractionDraft, VerificationResult
from app.verification.other import (
    QuestionDraft,
    QuestionSetDraft,
    validate_question_set,
)


_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)


def _json_object(content: str) -> dict[str, object]:
    match = _JSON_FENCE.match(content)
    payload = match.group(1) if match else content
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise TypeError
    return parsed


class OpenAICompatibleAdapter:
    provider = "xiaomi-mimo"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        multimodal_model: str,
        text_model: str,
        version: str,
        client: AsyncOpenAI | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.multimodal_model = multimodal_model
        self.text_model = text_model
        self.model = text_model
        self.version = version
        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            max_retries=1,
        )

    async def _call(
        self, model: str, messages: list[ChatCompletionMessageParam]
    ) -> dict[str, object]:
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=1024,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError):
            raise ModelAdapterError("MODEL_UNAVAILABLE") from None
        except APIStatusError as error:
            code = "MODEL_UNAVAILABLE" if error.status_code >= 500 else "MODEL_HTTP_ERROR"
            raise ModelAdapterError(code) from None

        try:
            content = completion.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                raise TypeError
            return _json_object(content)
        except (ValueError, TypeError, IndexError, AttributeError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
```

Implement the three async public methods with standard messages:

```python
async def extract_found_item(
    self, image_data_url: str, context: Mapping[str, object]
) -> ExtractionDraft:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are Xiaomi MiMo. Extract a safe public lost-item draft. "
                "Return only one JSON object with item_type, name_public, "
                "description_public, and confidence. item_type must be "
                "IDENTITY_DOCUMENT or OTHER, and confidence must be between 0 and 1. "
                "Do not reveal full identity numbers."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {
                    "type": "text",
                    "text": "Context: " + json.dumps(dict(context), ensure_ascii=False),
                },
            ],
        },
    ]
    parsed = await self._call(self.multimodal_model, messages)
    try:
        return ExtractionDraft(
            item_type=ItemType(parsed["item_type"]),
            name_public=str(parsed["name_public"]),
            description_public=str(parsed["description_public"]),
            confidence=self._float(parsed["confidence"]),
            provider=self.provider,
            model=self.multimodal_model,
            version=self.version,
            status=ExtractionStatus.SUCCEEDED,
            raw_result_redacted={"response_valid": True},
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
```

Implement `generate_questions` exactly as:

```python
async def generate_questions(self, hidden_description: str) -> QuestionSetDraft:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are Xiaomi MiMo. Return only one JSON object with a questions "
                "array containing 2 or 3 open-ended ownership-verification questions. "
                "Each item must contain question_text, answer_key, dimension, and "
                "is_open_ended. Never include an answer in its question text."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {"hidden_description": hidden_description}, ensure_ascii=False
            ),
        },
    ]
    parsed = await self._call(self.text_model, messages)
    try:
        raw_questions = parsed["questions"]
        if not isinstance(raw_questions, list):
            raise TypeError
        questions = tuple(
            QuestionDraft(
                question_text=str(item["question_text"]),
                answer_key=str(item["answer_key"]),
                dimension=str(item["dimension"]),
                is_open_ended=bool(item.get("is_open_ended", True)),
            )
            for item in raw_questions
            if isinstance(item, Mapping)
        )
        if len(questions) != len(raw_questions):
            raise TypeError
        draft = QuestionSetDraft(questions=questions)
    except (KeyError, TypeError, ValueError):
        raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
    if not validate_question_set(draft).valid:
        raise ModelAdapterError("MODEL_RESPONSE_INVALID")
    return draft
```

Implement `verify_answers` exactly as:

```python
async def verify_answers(
    self, question_set: QuestionSetDraft, answers: Mapping[str, str]
) -> VerificationResult:
    verification_payload = {
        "questions": [
            {
                "dimension": question.dimension,
                "question": question.question_text,
                "answer_key": question.answer_key,
                "claimant_answer": answers.get(question.dimension, ""),
            }
            for question in question_set.questions
        ]
    }
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are Xiaomi MiMo. Compare claimant answers with reference answers. "
                "Return only one JSON object with result, confidence, and reason_code. "
                "result must be MATCH, PARTIAL_MATCH, CONFLICT, or UNDETERMINED."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(verification_payload, ensure_ascii=False),
        },
    ]
    parsed = await self._call(self.text_model, messages)
    try:
        result = VerificationResult(
            result=QuestionResult(parsed["result"]),
            confidence=self._float(parsed["confidence"]),
            reason_code=str(parsed["reason_code"]),
            provider=self.provider,
            model=self.text_model,
            version=self.version,
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
    if result.result is QuestionResult.MATCH and result.confidence < 0.8:
        return result.model_copy(
            update={
                "result": QuestionResult.UNDETERMINED,
                "reason_code": "CONFIDENCE_TOO_LOW",
            }
        )
    return result
```

Retain `_float` exactly:

```python
@staticmethod
def _float(value: object) -> float:
    if not isinstance(value, (str, int, float)):
        raise TypeError
    return float(value)
```

- [ ] **Step 4: Run all multimodal unit and contract tests**

Run:

```bash
cd src/backend
pytest tests/unit/multimodal tests/contract/test_extraction_contract.py tests/contract/test_question_contract.py tests/contract/test_verification_contract.py -q
```

Expected: all selected tests pass, request bodies contain `messages`, and no request contains legacy top-level `operation` or `input`.

- [ ] **Step 5: Commit the real adapter**

```bash
git add src/backend/pyproject.toml src/backend/app/multimodal/openai_compatible.py src/backend/tests/unit/multimodal/test_openai_compatible.py
git commit -m "feat(multimodal): add async mimo chat adapter"
```

---

### Task 3: Add validated configuration and one adapter factory

**Files:**
- Modify: `src/backend/app/settings.py`
- Modify: `src/backend/.env.example`
- Create: `src/backend/app/multimodal/factory.py`
- Create: `src/backend/tests/unit/multimodal/test_factory.py`

**Interfaces:**
- Consumes: `Settings`, `MockMultimodalAdapter`, and the real adapter from Task 2.
- Produces: `build_multimodal_adapter(config: Settings) -> MultimodalPort` and cached `get_multimodal_adapter() -> MultimodalPort` for FastAPI dependency injection.

- [ ] **Step 1: Write factory configuration tests**

Create tests with explicit `_env_file=None` settings:

```python
import pytest

from app.multimodal.factory import build_multimodal_adapter
from app.multimodal.mock import MockMultimodalAdapter
from app.multimodal.openai_compatible import OpenAICompatibleAdapter
from app.multimodal.ports import ModelAdapterError
from app.settings import Settings


def test_mock_mode_needs_no_api_key() -> None:
    adapter = build_multimodal_adapter(Settings(_env_file=None, ai_mode="mock"))
    assert isinstance(adapter, MockMultimodalAdapter)


def test_real_mode_requires_api_key() -> None:
    config = Settings(_env_file=None, ai_mode="real", mimo_api_key="")
    with pytest.raises(ModelAdapterError, match="MIMO_API_KEY_MISSING"):
        build_multimodal_adapter(config)


def test_real_mode_builds_mimo_v2_5_adapter() -> None:
    config = Settings(
        _env_file=None,
        ai_mode="real",
        mimo_api_key="synthetic-test-key",
    )
    adapter = build_multimodal_adapter(config)
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.multimodal_model == "mimo-v2.5"
    assert adapter.text_model == "mimo-v2.5"
```

Add the invalid-model test:

```python
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mimo_multimodal_model", "legacy-model"),
        ("mimo_text_model", "legacy-model"),
    ],
)
def test_real_mode_rejects_unapproved_model(field: str, value: str) -> None:
    config = Settings(
        _env_file=None,
        ai_mode="real",
        mimo_api_key="synthetic-test-key",
        **{field: value},
    )
    with pytest.raises(ModelAdapterError, match="MODEL_CONFIG_INVALID"):
        build_multimodal_adapter(config)
```

- [ ] **Step 2: Run the factory tests and verify the red state**

Run:

```bash
cd src/backend
pytest tests/unit/multimodal/test_factory.py -q
```

Expected: collection fails because `app.multimodal.factory` does not exist.

- [ ] **Step 3: Update defaults and implement the factory**

Set these values in `Settings` and `.env.example`:

```text
AI_MODE=mock
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_API_KEY=
MIMO_MULTIMODAL_MODEL=mimo-v2.5
MIMO_TEXT_MODEL=mimo-v2.5
MODEL_TIMEOUT_SECONDS=20
```

Create the factory:

```python
from functools import lru_cache

from app.multimodal.mock import MockMultimodalAdapter
from app.multimodal.openai_compatible import OpenAICompatibleAdapter
from app.multimodal.ports import ModelAdapterError, MultimodalPort
from app.settings import Settings, settings


def build_multimodal_adapter(config: Settings = settings) -> MultimodalPort:
    if config.ai_mode == "mock":
        return MockMultimodalAdapter()
    if not config.mimo_api_key:
        raise ModelAdapterError("MIMO_API_KEY_MISSING")
    if {
        config.mimo_multimodal_model,
        config.mimo_text_model,
    } != {"mimo-v2.5"}:
        raise ModelAdapterError("MODEL_CONFIG_INVALID")
    return OpenAICompatibleAdapter(
        base_url=config.mimo_base_url,
        api_key=config.mimo_api_key,
        multimodal_model=config.mimo_multimodal_model,
        text_model=config.mimo_text_model,
        version="openai-chat-completions-v1",
        timeout_seconds=config.model_timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_multimodal_adapter() -> MultimodalPort:
    return build_multimodal_adapter(settings)
```

- [ ] **Step 4: Run configuration and factory tests**

Run:

```bash
cd src/backend
pytest tests/unit/multimodal/test_factory.py tests/unit/matching/test_embedding_factory.py -q
```

Expected: all selected tests pass, proving MiMo configuration does not change the existing Qwen embedding factory.

- [ ] **Step 5: Commit configuration and factory**

```bash
git add src/backend/app/settings.py src/backend/.env.example src/backend/app/multimodal/factory.py src/backend/tests/unit/multimodal/test_factory.py
git commit -m "feat(multimodal): select mimo adapter from settings"
```

---

### Task 4: Encode private images in memory and wire all three routes to the factory

**Files:**
- Create: `src/backend/app/multimodal/image_data.py`
- Modify: `src/backend/app/api/routes/found_records.py`
- Modify: `src/backend/app/api/routes/claims.py`
- Create: `src/backend/tests/unit/multimodal/test_image_data.py`
- Create: `src/backend/tests/unit/multimodal/test_route_dependencies.py`

**Interfaces:**
- Consumes: `LocalStorage.read`, async `MultimodalPort`, and `get_multimodal_adapter`.
- Produces: `encode_image_data_url(data: bytes, suffix: str) -> str`; real adapter injection for extraction, question generation, and answer verification routes.

- [ ] **Step 1: Write failing image encoding and route-dependency tests**

Create the image tests:

```python
import pytest

from app.multimodal.image_data import encode_image_data_url


@pytest.mark.parametrize(
    ("suffix", "media_type"),
    [
        (".jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        (".png", "image/png"),
        ("webp", "image/webp"),
    ],
)
def test_encode_image_data_url_uses_allowlisted_media_type(
    suffix: str, media_type: str
) -> None:
    result = encode_image_data_url(b"synthetic", suffix)
    assert result == f"data:{media_type};base64,c3ludGhldGlj"


@pytest.mark.parametrize(("data", "suffix"), [(b"", ".png"), (b"x", ".gif")])
def test_encode_image_data_url_rejects_empty_or_unsupported_input(
    data: bytes, suffix: str
) -> None:
    with pytest.raises(ValueError, match="IMAGE_DATA_INVALID"):
        encode_image_data_url(data, suffix)
```

Create this route inspection test:

```python
from fastapi.routing import APIRoute

from app.api.routes import claims, found_records
from app.multimodal.factory import get_multimodal_adapter


EXPECTED = (
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
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert get_multimodal_adapter in dependency_calls
```

- [ ] **Step 2: Run the new tests and verify the red state**

Run:

```bash
cd src/backend
pytest tests/unit/multimodal/test_image_data.py tests/unit/multimodal/test_route_dependencies.py -q
```

Expected: image test collection fails because `image_data.py` does not exist; route tests fail because both routers still hardcode `MockMultimodalAdapter`.

- [ ] **Step 3: Implement the allowlisted in-memory encoder**

Create:

```python
from base64 import b64encode


_MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def encode_image_data_url(data: bytes, suffix: str) -> str:
    extension = suffix.casefold().lstrip(".")
    media_type = _MEDIA_TYPES.get(extension)
    if not data or media_type is None:
        raise ValueError("IMAGE_DATA_INVALID")
    payload = b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{payload}"
```

- [ ] **Step 4: Replace hardcoded mocks and build the private-image Data URL**

Remove both route-level `MockMultimodalAdapter` instances. Add this dependency to the extraction and question handlers in `found_records.py` and the answer handler in `claims.py`:

```python
adapter: MultimodalPort = Depends(get_multimodal_adapter)
```

Pass that `adapter` to the existing service calls. Before `extract_found_record`, build the image argument without logging it:

```python
try:
    image_data_url = encode_image_data_url(
        _storage.read(asset.object_key), Path(asset.object_key).suffix
    )
except (OSError, ValueError):
    raise HTTPException(400, "IMAGE_UNAVAILABLE") from None

draft = await extract_found_record(
    session,
    record_id=record_id,
    actor_id=user.id,
    image_ref=image_data_url,
    adapter=adapter,
)
```

Imports come from `app.multimodal.factory`, `app.multimodal.image_data`, and `app.multimodal.ports`. Keep the existing `_storage = LocalStorage(Path("storage"))` and all ownership checks unchanged.

- [ ] **Step 5: Run image, route, and business-flow tests**

Run:

```bash
cd src/backend
pytest tests/unit/multimodal/test_image_data.py tests/unit/multimodal/test_route_dependencies.py tests/integration/items/test_found_other_publish.py tests/integration/verification/test_other_claim_routing.py tests/integration/verification/test_other_model_failure.py -q
```

Expected: all selected tests pass. Then run:

```bash
rg -n "MockMultimodalAdapter|_adapter" app/api/routes/found_records.py app/api/routes/claims.py
```

Expected: no matches.

- [ ] **Step 6: Commit image privacy and route wiring**

```bash
git add src/backend/app/multimodal/image_data.py src/backend/app/api/routes/found_records.py src/backend/app/api/routes/claims.py src/backend/tests/unit/multimodal/test_image_data.py src/backend/tests/unit/multimodal/test_route_dependencies.py
git commit -m "feat(api): route multimodal flows through mimo"
```

---

### Task 5: Run full verification and a secret-safe live MiMo smoke test

**Files:**
- Verify only; no repository file is modified by this task.

**Interfaces:**
- Consumes: Completed real adapter, factory, route wiring, and the user's rotated or explicitly approved temporary MiMo Key entered through a hidden terminal prompt.
- Produces: Test evidence in command output showing all automated checks and all three live adapter operations succeed without exposing secrets or private payloads.

- [ ] **Step 1: Run all automated verification**

Run:

```bash
docker compose up -d db
cd src/backend
python -m pip install -e '.[dev]'
pytest -q
python -m ruff check app tests
python -m mypy app
python -m compileall -q app tests
cd ../..
git diff --check
```

Expected: every command exits zero. Pytest reports the full suite passing; Ruff and Mypy report no errors; compileall and `git diff --check` print nothing.

- [ ] **Step 2: Scan tracked content for leaked credentials**

Run:

```bash
git grep -nE 'sk-[A-Za-z0-9._-]{16,}' -- . || true
```

Expected: no output.

- [ ] **Step 3: Run all three real operations with hidden Key input**

From `src/backend`, start an interactive Python process that calls `getpass.getpass("MIMO_API_KEY: ")`; do not place the Key in the shell command, environment history, source file, or output. In the process:

```python
import asyncio
from base64 import b64decode
import getpass

from app.multimodal.image_data import encode_image_data_url
from app.multimodal.openai_compatible import OpenAICompatibleAdapter


async def main() -> None:
    key = getpass.getpass("MIMO_API_KEY: ")
    adapter = OpenAICompatibleAdapter(
        base_url="https://api.xiaomimimo.com/v1",
        api_key=key,
        multimodal_model="mimo-v2.5",
        text_model="mimo-v2.5",
        version="openai-chat-completions-v1",
        timeout_seconds=60,
    )
    image = encode_image_data_url(
        b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        ),
        ".png",
    )
    try:
        extraction = await adapter.extract_found_item(image, {"smoke": True})
        questions = await adapter.generate_questions(
            "黑色折叠伞，伞柄底部有一道细小裂纹，伞套内侧写有字母A"
        )
        answers = {
            question.dimension: question.answer_key
            for question in questions.questions
        }
        verification = await adapter.verify_answers(questions, answers)
        print(
            {
                "model": extraction.model,
                "extraction_valid": bool(extraction.name_public),
                "question_count": len(questions.questions),
                "verification_result": verification.result.value,
            }
        )
    finally:
        await adapter.client.close()


asyncio.run(main())
```

Expected: output contains model `mimo-v2.5`, `extraction_valid: True`, a question count of 2 or 3, and a valid verification enum. Output contains no Key, Data URL, hidden prompt, answer keys, or raw provider response.

- [ ] **Step 4: Confirm the branch is clean except for user-owned untracked files**

Run:

```bash
git status --short --branch
git log --oneline -5
```

Expected: branch tracks `origin/feature/backend`; only the pre-existing untracked `images/` and `images.zip` remain; the implementation commits from Tasks 1–4 are present.
