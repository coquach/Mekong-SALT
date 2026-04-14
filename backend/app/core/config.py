"""Application settings management."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Mekong-SALT Backend"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mekong_salt"
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379/0"
    external_context_cache_ttl_seconds: int = 600
    weather_snapshot_freshness_minutes: int = 30
    risk_rule_version: str = "v1"
    open_meteo_weather_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_marine_base_url: str = "https://marine-api.open-meteo.com/v1/marine"

    llm_provider: Literal["mock", "gemini", "ollama"] = "mock"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: int = 30



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()

