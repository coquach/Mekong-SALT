"""Application settings management."""

from functools import lru_cache
import json
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import SecretStr, ValidationInfo, field_validator
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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mekong_salt"
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379/0"
    domain_event_signal_channel: str = "domain-events:wake"
    external_context_cache_ttl_seconds: int = 600
    weather_snapshot_freshness_minutes: int = 30
    risk_rule_version: str = "v1"
    open_meteo_weather_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_marine_base_url: str = "https://marine-api.open-meteo.com/v1/marine"
    iot_ingest_mode: Literal["http", "mqtt", "pubsub", "hybrid"] = "http"

    mqtt_enabled: bool = False
    mqtt_broker_url: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: SecretStr | None = None
    mqtt_client_id: str = "mekong-salt-backend"
    mqtt_topic_sensor_readings: str = "mekong/sensors/readings"
    mqtt_topic_device_status: str = "mekong/sensors/status"
    mqtt_topic_dead_letter: str = "mekong/sensors/readings/dlq"
    mqtt_qos: int = 1

    iot_dlq_archive_enabled: bool = True
    iot_dlq_archive_path: str = "artifacts/ingest_dlq_archive.jsonl"

    pubsub_enabled: bool = False
    pubsub_project_id: str | None = None
    pubsub_subscription_sensor_readings: str | None = None
    pubsub_topic_sensor_events: str | None = None
    pubsub_dead_letter_topic: str | None = None
    pubsub_emulator_host: str | None = None
    pubsub_max_delivery_attempts: int = 5
    pubsub_flow_max_messages: int = 100

    earth_engine_enabled: bool = False
    earth_engine_project_id: str | None = None
    earth_engine_service_account_email: str | None = None
    earth_engine_service_account_key_path: str | None = None
    earth_engine_default_dataset: str = "COPERNICUS/S2_SR_HARMONIZED"
    earth_engine_region_buffer_m: int = 3000

    llm_provider: Literal["gemini"] = "gemini"
    llm_use_vertex: bool = True
    vertex_ai_project: str | None = None
    vertex_ai_location: str = "us-central1"
    gemini_api_key: SecretStr | None = None
    gemini_model: Literal["gemini-2.5-pro"] = "gemini-2.5-pro"
    rag_use_vertex_vector_search: bool = True
    rag_enable_local_fallback: bool = True
    rag_static_corpus_provider: Literal["vector_search", "vertex_rag_engine_adapter"] = "vector_search"
    rag_static_retrieval_mode: Literal["vector", "local", "shadow"] = "vector"
    rag_shadow_primary_lane: Literal["vector", "local"] = "vector"
    rag_shadow_min_overlap_ratio: float = 0.2
    rag_static_direct_embedding_enabled: bool = True
    rag_embedding_model: str = "text-embedding-005"
    rag_retrieval_top_k: int = 8
    rag_static_local_limit: int = 4
    rag_memory_local_limit: int = 4
    rag_memory_vector_max_evidence: int = 4
    rag_memory_vector_timeout_seconds: float = 2.5
    rag_vector_neighbor_multiplier: int = 2
    rag_vector_neighbor_floor: int = 12
    rag_csv_reindex_ttl_days: int = 7
    vertex_vector_search_index: str | None = None
    vertex_vector_search_index_endpoint: str | None = None
    vertex_vector_search_deployed_index_id: str | None = None
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: int = 30

    active_monitoring_enabled: bool = True
    active_monitoring_mode: Literal["active"] = "active"
    active_monitoring_poll_seconds: int = 30
    active_monitoring_lock_ttl_seconds: int = 300
    active_monitoring_batch_size: int = 50
    active_monitoring_approval_timeout_minutes: int = 60
    active_monitoring_approval_timeout_action: Literal["none", "auto_reject"] = "auto_reject"
    active_monitoring_feedback_replan_max_attempts: int = 0
    reactive_auto_execute_enabled: bool = True
    zalo_notifications_enabled: bool = False
    zalo_delivery_mode: Literal["text", "template"] = "template"
    zalo_oa_access_token: SecretStr | None = None
    zalo_oa_recipient_phone_number: str | None = None
    zalo_oa_template_id: str | None = None
    zalo_oa_template_message_endpoint: str = "https://openapi.zalo.me/v3.0/oa/message/template"
    zalo_oa_message_endpoint: str = "https://openapi.zalo.me/v3.0/oa/message/cs"
    zalo_oa_timeout_seconds: int = 10

    email_notifications_enabled: bool = False
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_smtp_username: str | None = None
    email_smtp_password: SecretStr | None = None
    email_from_address: str | None = None
    email_use_tls: bool = True
    email_use_ssl: bool = False
    email_timeout_seconds: int = 10

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def normalize_cors_allowed_origins(cls, value: object) -> list[str]:
        """Accept JSON/comma-separated input and normalize origin formatting."""
        parsed_values: list[str]
        if value is None:
            parsed_values = []
        elif isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                parsed_values = []
            elif raw_value.startswith("["):
                loaded = json.loads(raw_value)
                if not isinstance(loaded, list):
                    raise ValueError("CORS_ALLOWED_ORIGINS JSON must be a list.")
                parsed_values = [str(item) for item in loaded]
            else:
                parsed_values = [item.strip() for item in raw_value.split(",")]
        elif isinstance(value, (list, tuple, set)):
            parsed_values = [str(item) for item in value]
        else:
            raise ValueError("CORS_ALLOWED_ORIGINS must be a list or string.")

        normalized: list[str] = []
        for origin in parsed_values:
            item = origin.strip()
            if not item:
                continue
            item = item.rstrip("/")
            if item not in normalized:
                normalized.append(item)
        return normalized

    @field_validator("cors_allowed_origins")
    @classmethod
    def ensure_dev_origins(
        cls,
        value: list[str],
        info: ValidationInfo,
    ) -> list[str]:
        """Ensure common local FE origins are available in development."""
        app_env = str(info.data.get("app_env", "development")).lower()
        if app_env != "development":
            return value

        local_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
        merged = list(value)
        for origin in local_origins:
            if origin not in merged:
                merged.append(origin)
        return merged

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

    @field_validator("zalo_oa_recipient_phone_number", mode="before")
    @classmethod
    def normalize_zalo_recipient_phone_number(cls, value: object) -> str | None:
        """Treat empty recipient phone numbers as disabled configuration."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("zalo_delivery_mode", mode="before")
    @classmethod
    def normalize_zalo_delivery_mode(cls, value: object) -> str:
        """Normalize the notification delivery mode."""
        normalized = str(value or "template").strip().lower()
        if normalized in {"text", "template"}:
            return normalized
        return "template"

    @field_validator("email_smtp_host", "email_smtp_username", "email_from_address", mode="before")
    @classmethod
    def normalize_email_text_settings(cls, value: object) -> str | None:
        """Treat empty email delivery settings as disabled configuration."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("email_smtp_password", mode="before")
    @classmethod
    def normalize_email_password(cls, value: object) -> SecretStr | None:
        """Treat empty email passwords as disabled configuration."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return SecretStr(text)

    @field_validator("llm_use_vertex", mode="before")
    @classmethod
    def enforce_vertex_mode(cls, _value: bool | None) -> bool:
        """Force Vertex mode for all Gemini plan generation."""
        return True

    @field_validator("gemini_model", mode="before")
    @classmethod
    def enforce_gemini_flash_model(cls, _value: str | None) -> str:
        """Force Gemini Pro 2.5 as the planning model."""
        return "gemini-2.5-pro"

    @field_validator("rag_static_corpus_provider", mode="before")
    @classmethod
    def normalize_static_corpus_provider(cls, value: str | None) -> str:
        """Normalize legacy provider names to explicit adapter naming."""
        normalized = str(value or "vector_search").strip().lower()
        if normalized == "vertex_rag_engine":
            return "vertex_rag_engine_adapter"
        if normalized in {"vector_search", "vertex_rag_engine_adapter"}:
            return normalized
        return "vector_search"



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()

