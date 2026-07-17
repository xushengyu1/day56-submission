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
