from http import HTTPStatus
from types import SimpleNamespace

import dashscope  # type: ignore[import-untyped]
import pytest

from app.matching.dashscope_embedding import DashScopeEmbeddingAdapter
from app.matching.embedding import EmbeddingError


@pytest.mark.asyncio
async def test_dashscope_adapter_restores_input_order(monkeypatch) -> None:
    def fake_call(**kwargs):
        assert kwargs == {
            "model": "qwen3.7-text-embedding",
            "input": ["lost", "found"],
            "dimension": 1024,
            "api_key": "test-key",
        }
        return SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 1, "embedding": [0.2] * 1024},
                    {"text_index": 0, "embedding": [0.1] * 1024},
                ]
            },
        )

    monkeypatch.setattr(dashscope.TextEmbedding, "call", fake_call)
    adapter = DashScopeEmbeddingAdapter(
        model="qwen3.7-text-embedding",
        dimension=1024,
        api_key="test-key",
    )

    vectors = await adapter.embed(["lost", "found"])

    assert len(vectors) == 2
    assert vectors[0][0] == 0.1
    assert vectors[1][0] == 0.2
    assert all(len(vector) == 1024 for vector in vectors)


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(status_code=500, output={"embeddings": []}),
        SimpleNamespace(status_code=HTTPStatus.OK, output={}),
        SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 0, "embedding": [0.1] * 1024},
                    {"text_index": 0, "embedding": [0.2] * 1024},
                ]
            },
        ),
        SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 0, "embedding": [0.1] * 1024},
                ]
            },
        ),
        SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 0, "embedding": [0.1] * 1023},
                    {"text_index": 1, "embedding": [0.2] * 1024},
                ]
            },
        ),
        SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 0, "embedding": [float("inf")] * 1024},
                    {"text_index": 1, "embedding": [0.2] * 1024},
                ]
            },
        ),
        SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [
                    {"text_index": 0, "embedding": [True] * 1024},
                    {"text_index": 1, "embedding": [0.2] * 1024},
                ]
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_dashscope_adapter_rejects_invalid_responses(
    monkeypatch, response
) -> None:
    monkeypatch.setattr(
        dashscope.TextEmbedding,
        "call",
        lambda **_kwargs: response,
    )
    adapter = DashScopeEmbeddingAdapter(
        model="qwen3.7-text-embedding",
        dimension=1024,
        api_key="test-key",
    )

    with pytest.raises(EmbeddingError, match="^EMBEDDING_UNAVAILABLE$"):
        await adapter.embed(["private-input", "second-input"])


@pytest.mark.parametrize("texts", [[], [""], ["item"] * 21])
@pytest.mark.asyncio
async def test_dashscope_adapter_rejects_invalid_input(texts) -> None:
    adapter = DashScopeEmbeddingAdapter(
        model="qwen3.7-text-embedding",
        dimension=1024,
        api_key="test-key",
    )

    with pytest.raises(EmbeddingError, match="^EMBEDDING_INPUT_INVALID$"):
        await adapter.embed(texts)


@pytest.mark.asyncio
async def test_dashscope_adapter_does_not_echo_sdk_error_or_credentials(
    monkeypatch,
) -> None:
    def fail_call(**_kwargs):
        raise RuntimeError("test-key private-input raw-response")

    monkeypatch.setattr(dashscope.TextEmbedding, "call", fail_call)
    adapter = DashScopeEmbeddingAdapter(
        model="qwen3.7-text-embedding",
        dimension=1024,
        api_key="test-key",
    )

    with pytest.raises(EmbeddingError) as captured:
        await adapter.embed(["private-input"])

    assert str(captured.value) == "EMBEDDING_UNAVAILABLE"
    assert "test-key" not in str(captured.value)
    assert "private-input" not in str(captured.value)
