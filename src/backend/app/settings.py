from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "test"
    database_url: str = "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found"
    jwt_secret: str = "dev-only-change-me"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    id_hmac_key_v1: str = "synthetic-development-key"
    ai_mode: Literal["mock", "real"] = "real"
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_api_key: str = "sk-cjn578ymgm0jbayfp2o7t78lm9sutge3hjokyebbk5b31zs3"
    mimo_multimodal_model: str = "mimo-v2.5"
    mimo_text_model: str = "mimo-v2.5"
    embedding_mode: Literal["mock", "dashscope"] = "dashscope"
    dashscope_base_url: str = (
        "https://llm-gfhd2inat6dsbort.cn-beijing.maas.aliyuncs.com/api/v1"
    )
    dashscope_api_key: str = "sk-ws-H.EDYMRII.7Ujj.MEQCICo6ReOxCQUV_NKdC0P6cjbW1jbH7ek3mb7KfzA034rTAiBhd9GiYwn3tZ5LQ-ONzhCAQ7aJ5xdaRvL7tk_503kxqw"
    embedding_model: str = "qwen3.7-text-embedding"
    embedding_dimension: int = 1024
    question_model: str = "qwen3.7-plus"
    question_base_url: str = ""
    question_api_key: str = ""
    model_timeout_seconds: float = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
