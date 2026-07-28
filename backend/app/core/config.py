from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UFC API"
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://ufc:ufc@localhost:5432/ufc"
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
