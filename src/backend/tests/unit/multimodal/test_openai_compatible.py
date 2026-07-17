import json
from collections.abc import Callable

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


def _adapter(
    handler: Callable[[httpx.Request], httpx.Response],
) -> OpenAICompatibleAdapter:
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
    assert requests[0]["thinking"] == {"type": "disabled"}
    messages = requests[0]["messages"]
    assert isinstance(messages, list)
    user_content = messages[1]["content"]
    assert user_content[0]["type"] == "image_url"
    assert user_content[0]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )
    assert result.name_public == "黑色折叠伞"
    assert "110101200001010010" not in str(result.raw_result_redacted)


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

    messages = requests[1]["messages"]
    assert isinstance(messages, list)
    verification_text = messages[1]["content"]
    assert "一道裂纹" in verification_text
    assert "字母A" in verification_text
    assert result.result is QuestionResult.MATCH


@pytest.mark.asyncio
async def test_question_generation_assigns_internal_dimensions() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(
            json.dumps(
                {
                    "questions": [
                        {
                            "question_text": "请描述伞柄底部细节。",
                            "answer_key": "一道裂纹",
                            "dimension": "handle",
                            "is_open_ended": True,
                        },
                        {
                            "question_text": "请描述伞套内侧标记。",
                            "answer_key": "字母A",
                            "is_open_ended": True,
                        },
                    ]
                }
            )
        )

    adapter = _adapter(handler)
    try:
        questions = await adapter.generate_questions("合成隐藏描述")
    finally:
        await adapter.client.close()

    assert [question.dimension for question in questions.questions] == [
        "question_1",
        "question_2",
    ]


@pytest.mark.asyncio
async def test_question_generation_normalizes_unsafe_model_fields() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(
            json.dumps(
                {
                    "questions": [
                        {
                            "question_text": "请描述伞柄底部特征。",
                            "answer_key": "一道裂纹",
                            "dimension": "duplicate",
                            "is_open_ended": False,
                        },
                        {
                            "question_text": "伞套内侧是否写有字母A？",
                            "answer_key": "字母A",
                            "dimension": "duplicate",
                            "is_open_ended": False,
                        },
                    ]
                }
            )
        )

    adapter = _adapter(handler)
    try:
        questions = await adapter.generate_questions("合成隐藏描述")
    finally:
        await adapter.client.close()

    assert [question.dimension for question in questions.questions] == [
        "question_1",
        "question_2",
    ]
    assert all(question.is_open_ended for question in questions.questions)
    assert questions.questions[1].question_text == "请描述只有物主知道的第2项隐蔽特征。"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {
            "item_type": "OTHER",
            "name_public": None,
            "description_public": "外观完整",
            "confidence": 0.9,
        },
        {
            "item_type": "OTHER",
            "name_public": "黑色折叠伞",
            "description_public": [],
            "confidence": 0.9,
        },
        {
            "item_type": "OTHER",
            "name_public": "黑色折叠伞",
            "description_public": "外观完整",
            "confidence": True,
        },
    ],
)
async def test_extraction_rejects_coercible_provider_fields(
    payload: dict[str, object],
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(json.dumps(payload))

    adapter = _adapter(handler)
    try:
        with pytest.raises(ModelAdapterError, match="MODEL_RESPONSE_INVALID"):
            await adapter.extract_found_item(
                "data:image/png;base64,c3ludGhldGlj", {}
            )
    finally:
        await adapter.client.close()


@pytest.mark.asyncio
async def test_question_generation_rejects_non_string_text_fields() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(
            json.dumps(
                {
                    "questions": [
                        {"question_text": None, "answer_key": "一道裂纹"},
                        {"question_text": "请描述伞套标记。", "answer_key": ["A"]},
                    ]
                }
            )
        )

    adapter = _adapter(handler)
    try:
        with pytest.raises(ModelAdapterError, match="MODEL_RESPONSE_INVALID"):
            await adapter.generate_questions("合成隐藏描述")
    finally:
        await adapter.client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"result": "MATCH", "confidence": True, "reason_code": "MATCHED"},
        {"result": "MATCH", "confidence": 0.9, "reason_code": None},
    ],
)
async def test_verification_rejects_coercible_provider_fields(
    payload: dict[str, object],
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(json.dumps(payload))

    adapter = _adapter(handler)
    questions = QuestionSetDraft(
        questions=(
            QuestionDraft("请描述伞柄底部细节。", "一道裂纹", "question_1"),
            QuestionDraft("请描述伞套内侧标记。", "字母A", "question_2"),
        )
    )
    try:
        with pytest.raises(ModelAdapterError, match="MODEL_RESPONSE_INVALID"):
            await adapter.verify_answers(questions, {})
    finally:
        await adapter.client.close()


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
        return httpx.Response(
            status_code, json={"error": {"message": "synthetic"}}
        )

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


@pytest.mark.asyncio
async def test_low_confidence_match_is_conservatively_undetermined() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(
            json.dumps(
                {
                    "result": "MATCH",
                    "confidence": 0.6,
                    "reason_code": "WEAK_MATCH",
                }
            )
        )

    adapter = _adapter(handler)
    questions = QuestionSetDraft(
        questions=(
            QuestionDraft("请描述伞柄底部细节。", "一道裂纹", "handle"),
            QuestionDraft("请描述伞套内侧标记。", "字母A", "cover"),
        )
    )
    try:
        result = await adapter.verify_answers(
            questions, {"handle": "一道裂纹", "cover": "字母A"}
        )
    finally:
        await adapter.client.close()

    assert result.result is QuestionResult.UNDETERMINED
    assert result.reason_code == "CONFIDENCE_TOO_LOW"
