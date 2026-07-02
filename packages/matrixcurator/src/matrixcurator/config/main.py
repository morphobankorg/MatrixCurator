# src/config/main.py
from enum import Enum
from pydantic_settings import SettingsConfigDict
from pydantic import Field
from typing import Optional
from lume import LoggingSettings
from contextvars import ContextVar

from matrixcurator.utils.concurrency import RateLimitConfig

__all__ = [
    "Settings",
    "settings",
    "ContextStrategy",
    "OrchestrationStrategy",
    "IntelligenceStrategy",
    "orchestration_strategy_var",
    "intelligence_strategy_var",
    "context_strategy_var",
]


class ContextStrategy(str, Enum):
    FULL_CONTEXT = "full_context"
    RETRIEVAL_AUGMENTED = "retrieval_augmented"


class OrchestrationStrategy(str, Enum):
    STATIC_ROUTING = "static_routing"
    DYNAMIC_ROUTING = "dynamic_routing"


class IntelligenceStrategy(str, Enum):
    PROMPT_ENGINEERING = "prompt_engineering"
    PROGRAMMATIC_OPTIMIZATION = "programmatic_optimization"


orchestration_strategy_var: ContextVar[Optional[OrchestrationStrategy]] = ContextVar("orchestration_strategy", default=None)
intelligence_strategy_var: ContextVar[Optional[IntelligenceStrategy]] = ContextVar("intelligence_strategy", default=None)
context_strategy_var: ContextVar[Optional[ContextStrategy]] = ContextVar("context_strategy", default=None)


class Settings(LoggingSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telemetry & Observability
    telemetry_opt_out: bool = False

    # Sentry
    sentry_dsn: Optional[str] = None

    # PostHog
    posthog_api_key: Optional[str] = None
    posthog_host: str = "https://app.posthog.com"

    # Langfuse
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # App Settings
    debug: bool = False
    sqlite_db_path: str = "sqlite.db"
    retrieval_backend: str = "sqlite"
    embedding_model: str = "gemini/gemini-embedding-2"

    # VLM Models
    vlm_model: str = "gemini/gemini-3.1-flash-lite"

    # Model Tiers
    model_tier_1: Optional[str] = None
    model_tier_2: Optional[str] = None
    model_tier_3: Optional[str] = None

    # Feature Flags (Architectural Strategies)
    context_strategy: ContextStrategy = ContextStrategy.FULL_CONTEXT
    orchestration_strategy: OrchestrationStrategy = (
        OrchestrationStrategy.DYNAMIC_ROUTING
    )
    intelligence_strategy: IntelligenceStrategy = (
        IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION
    )

    # Tool Rate Limits
    pymupdf_rate_limit: RateLimitConfig = Field(default_factory=lambda: RateLimitConfig(per_second=50))
    docling_rate_limit: RateLimitConfig = Field(default_factory=lambda: RateLimitConfig(per_second=5))
    docx_rate_limit: RateLimitConfig = Field(default_factory=lambda: RateLimitConfig(per_second=50))
    txt_rate_limit: RateLimitConfig = Field(default_factory=lambda: RateLimitConfig(per_second=50))

    @property
    def current_context_strategy(self) -> ContextStrategy:
        return context_strategy_var.get() or self.context_strategy

    @property
    def current_orchestration_strategy(self) -> OrchestrationStrategy:
        return orchestration_strategy_var.get() or self.orchestration_strategy

    @property
    def current_intelligence_strategy(self) -> IntelligenceStrategy:
        return intelligence_strategy_var.get() or self.intelligence_strategy

    def get_model_for_tier(self, requested_tier: int) -> str:
        """
        Returns the model string for the requested tier.
        If the requested tier is not configured, it falls back to the closest available tier.
        Raises ValueError if no tiers are configured.
        """
        tiers = {1: self.model_tier_1, 2: self.model_tier_2, 3: self.model_tier_3}

        if tiers.get(requested_tier):
            return tiers[requested_tier]

        # Fallback logic: find the closest configured tier
        available_tiers = {k: v for k, v in tiers.items() if v is not None}
        if not available_tiers:
            raise ValueError(
                "No model tiers are configured. Please set at least one model_tier in settings."
            )

        # Find the closest tier key
        closest_tier = min(
            available_tiers.keys(), key=lambda k: abs(k - requested_tier)
        )
        return available_tiers[closest_tier]


# Global settings instance
settings = Settings()
