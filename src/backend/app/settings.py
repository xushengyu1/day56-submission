from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "test"
    database_url: str = "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found"
    jwt_secret: str = "dev-only-change-me"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    id_hmac_key_v1: str = "synthetic-development-key"
    ai_mode: Literal["mock", "real"] = "mock"
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_api_key: str = ""
    mimo_multimodal_model: str = "mimo-v2.5"
    mimo_text_model: str = "mimo-v2.5"
    embedding_mode: Literal["mock", "dashscope"] = "mock"
    dashscope_api_key: str = ""
    embedding_model: str = "qwen3.7-text-embedding"
    embedding_dimension: int = 1024
    model_timeout_seconds: float = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
