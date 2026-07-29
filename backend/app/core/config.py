from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UFC API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://ufc:ufc@localhost:5432/ufc"
    llm_api_key: str | None = None
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
