import json

import httpx
import pytest

from app.multimodal.openai_compatible import OpenAICompatibleAdapter
from app.multimodal.ports import ModelAdapterError


def _adapter(handler) -> OpenAICompatibleAdapter:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatibleAdapter(
        base_url="https://model.example.test",
        api_key="test-key",
        model="test-model",
        version="schema-v1",
        client=client,
    )


def test_adapter_parses_openai_message_json_without_exposing_raw_sensitive_data() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        content = json.dumps(
            {
                "item_type": "OTHER",
                "name_public": "黑色折叠伞",
                "description_public": "外观完整",
                "confidence": 0.9,
                "id_number_candidate": "110101200001010010",
            }
        )
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    result = _adapter(handler).extract_found_item("private/object", {})

    assert result.name_public == "黑色折叠伞"
    assert "110101200001010010" not in str(result.raw_result_redacted)


def test_adapter_retries_one_server_error_and_rejects_invalid_json() -> None:
    calls = 0

    def retry_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]})

    with pytest.raises(ModelAdapterError, match="MODEL_RESPONSE_INVALID"):
        _adapter(retry_handler).extract_found_item("private/object", {})

    assert calls == 2
