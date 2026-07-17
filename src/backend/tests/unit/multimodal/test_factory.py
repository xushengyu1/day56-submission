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


@pytest.mark.asyncio
async def test_real_mode_builds_mimo_v2_5_adapter() -> None:
    config = Settings(
        _env_file=None,
        ai_mode="real",
        mimo_api_key="synthetic-test-key",
    )

    adapter = build_multimodal_adapter(config)
    assert isinstance(adapter, OpenAICompatibleAdapter)
    try:
        assert adapter.multimodal_model == "mimo-v2.5"
        assert adapter.text_model == "mimo-v2.5"
    finally:
        await adapter.client.close()


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
