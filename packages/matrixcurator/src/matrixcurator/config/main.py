# src/config/main.py
from enum import Enum
from pydantic_settings import SettingsConfigDict
from typing import Optional
from python_logging.config import LoggingSettings
from python_logging.main import setup_logging

__all__ = [
    "Settings", 
    "settings", 
    "ContextStrategy", 
    "OrchestrationStrategy", 
    "IntelligenceStrategy"
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

class Settings(LoggingSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
    
    # Model Tiers
    model_tier_1: Optional[str] = None
    model_tier_2: Optional[str] = None
    model_tier_3: Optional[str] = None

    # Feature Flags (Architectural Strategies)
    context_strategy: ContextStrategy = ContextStrategy.FULL_CONTEXT
    orchestration_strategy: OrchestrationStrategy = OrchestrationStrategy.DYNAMIC_ROUTING
    intelligence_strategy: IntelligenceStrategy = IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION

    def get_model_for_tier(self, requested_tier: int) -> str:
        """
        Returns the model string for the requested tier.
        If the requested tier is not configured, it falls back to the closest available tier.
        Raises ValueError if no tiers are configured.
        """
        tiers = {
            1: self.model_tier_1,
            2: self.model_tier_2,
            3: self.model_tier_3
        }
        
        if tiers.get(requested_tier):
            return tiers[requested_tier]
            
        # Fallback logic: find the closest configured tier
        available_tiers = {k: v for k, v in tiers.items() if v is not None}
        if not available_tiers:
            raise ValueError("No model tiers are configured. Please set at least one model_tier in settings.")
            
        # Find the closest tier key
        closest_tier = min(available_tiers.keys(), key=lambda k: abs(k - requested_tier))
        return available_tiers[closest_tier]

# Global settings instance
settings = Settings()

# Initialize global logging state
setup_logging(settings)
