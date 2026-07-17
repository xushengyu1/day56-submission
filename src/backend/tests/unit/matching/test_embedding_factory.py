from typing import Any

import pytest

from app.matching.dashscope_embedding import DashScopeEmbeddingAdapter
from app.matching.embedding import EmbeddingError, HashEmbeddingAdapter
from app.matching.embedding_factory import build_embedding_adapter
from app.settings import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, Any] = {
        "embedding_mode": "mock",
        "embedding_model": "qwen3.7-text-embedding",
        "embedding_dimension": 1024,
        "dashscope_api_key": "",
    }
    values.update(overrides)
    return Settings(**values)


def test_factory_uses_keyless_hash_adapter_in_mock_mode() -> None:
    adapter = build_embedding_adapter(_settings())

    assert isinstance(adapter, HashEmbeddingAdapter)
    assert adapter.model == "mock-hash-v1"
    assert adapter.dimension == 1024


def test_factory_builds_approved_dashscope_adapter() -> None:
    adapter = build_embedding_adapter(
        _settings(embedding_mode="dashscope", dashscope_api_key="test-key")
    )

    assert isinstance(adapter, DashScopeEmbeddingAdapter)
    assert adapter.model == "qwen3.7-text-embedding"
    assert adapter.dimension == 1024


@pytest.mark.parametrize(
    "overrides, code",
    [
        (
            {"embedding_mode": "dashscope", "dashscope_api_key": ""},
            "EMBEDDING_API_KEY_MISSING",
        ),
        (
            {
                "embedding_mode": "dashscope",
                "dashscope_api_key": "test-key",
                "embedding_model": "other-model",
            },
            "EMBEDDING_CONFIG_INVALID",
        ),
        (
            {
                "embedding_mode": "dashscope",
                "dashscope_api_key": "test-key",
                "embedding_dimension": 256,
            },
            "EMBEDDING_CONFIG_INVALID",
        ),
    ],
)
def test_factory_rejects_unsafe_real_configuration(
    overrides: dict[str, object], code: str
) -> None:
    with pytest.raises(EmbeddingError, match=f"^{code}$"):
        build_embedding_adapter(_settings(**overrides))
