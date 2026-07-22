from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded in the following order:
    1. Environment variables
    2. .env file
    3. Default values defined below
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----------------------------
    # Application
    # ----------------------------

    APP_NAME: str = "AgentDesk"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ----------------------------
    # API
    # ----------------------------

    API_PREFIX: str = "/api/v1"

    # ----------------------------
    # Database
    # ----------------------------

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/agentdesk"
    )

    # ----------------------------
    # LLM Providers
    # ----------------------------

    OPENAI_API_KEY: str = ""

    ANTHROPIC_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    # ----------------------------
    # Logging
    # ----------------------------

    LOG_LEVEL: str = "INFO"

    # ----------------------------
    # authentication
    # ----------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    The settings are loaded only once during the
    application's lifetime.
    """
    return Settings()


settings = get_settings()