from app.matching.dashscope_embedding import DashScopeEmbeddingAdapter
from app.matching.embedding import (
    EmbeddingError,
    EmbeddingPort,
    HashEmbeddingAdapter,
)
from app.settings import Settings, settings


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
