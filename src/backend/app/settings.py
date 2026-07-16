from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "test"
    database_url: str = "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
