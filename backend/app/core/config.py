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
    llm_provider: str = "ollama"
    llm_base_url: str = "http://ollama:11434"
    llm_model: str = "qwen3:4b"
    llm_thinking_enabled: bool = False
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = "http://localhost:5173"
    auth_token_secret: str | None = None
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30
    field_encryption_key: str | None = None
    field_lookup_hmac_key: str | None = None
    field_key_version: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
