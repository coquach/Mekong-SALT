"""Application settings management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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

    llm_provider: Literal["gemini"] = "gemini"
    llm_use_vertex: bool = True
    vertex_ai_project: str | None = None
    vertex_ai_location: str = "us-central1"
    gemini_api_key: SecretStr | None = None
    gemini_model: Literal["gemini-2.5-flash"] = "gemini-2.5-flash"
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: int = 30

    active_monitoring_enabled: bool = True
    active_monitoring_mode: Literal["dry_run", "active"] = "active"
    active_monitoring_poll_seconds: int = 30
    active_monitoring_lock_ttl_seconds: int = 300
    active_monitoring_batch_size: int = 50
    reactive_auto_execute_enabled: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Accept Neon/Postgres URLs and convert them for SQLAlchemy asyncpg."""
        if not value:
            return value

        url = str(value)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        parsed = urlsplit(url)
        query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))

        # Neon URLs often include libpq options. asyncpg expects "ssl=require"
        # and does not need channel_binding in the SQLAlchemy URL.
        sslmode = query_pairs.pop("sslmode", None)
        query_pairs.pop("channel_binding", None)
        if sslmode and "ssl" not in query_pairs:
            query_pairs["ssl"] = "require"

        # Neon pooler hosts run behind PgBouncer, so disable asyncpg prepared
        # statement caching unless the operator explicitly configured it.
        hostname = parsed.hostname or ""
        if "-pooler." in hostname and "prepared_statement_cache_size" not in query_pairs:
            query_pairs["prepared_statement_cache_size"] = "0"

        return urlunsplit(parsed._replace(query=urlencode(query_pairs)))

    @field_validator("llm_provider", mode="before")
    @classmethod
    def enforce_llm_provider(cls, _value: str | None) -> str:
        """Force Gemini as the only supported planning provider."""
        return "gemini"

    @field_validator("llm_use_vertex", mode="before")
    @classmethod
    def enforce_vertex_mode(cls, _value: bool | None) -> bool:
        """Force Vertex mode for all Gemini plan generation."""
        return True

    @field_validator("gemini_model", mode="before")
    @classmethod
    def enforce_gemini_flash_model(cls, _value: str | None) -> str:
        """Force Gemini Flash 2.5 as the planning model."""
        return "gemini-2.5-flash"



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()

