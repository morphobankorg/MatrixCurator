# src/config/main.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telemetry & Observability
    TELEMETRY_OPT_OUT: bool = False
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # PostHog
    POSTHOG_API_KEY: Optional[str] = None
    POSTHOG_HOST: str = "https://app.posthog.com"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    # OpenTelemetry / Structlog
    otel_exporter_otlp_endpoint: Optional[str] = None
    otel_exporter_otlp_logs_endpoint: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # LLM Providers
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # App Settings
    DEBUG: bool = False
    DEFAULT_MODEL: str = "gemini/gemini-1.5-pro"
    FALLBACK_MODEL: str = "gemini/gemini-1.5-flash"

settings = Settings()
