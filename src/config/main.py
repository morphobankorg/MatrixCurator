__all__ = ["settings",]

import os
from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    The main application settings, loaded from environment variables and defaults.
    This class centralizes all configuration, including application behavior
    and the list of available AI models.
    """

    # --- Application Settings ---
    # These can be overridden by environment variables (e.g., LOG_LEVEL="DEBUG")
    MAX_WORKERS: int | None = None
    LOG_LEVEL: str = "INFO"

    # --- Model Configuration ---
    # These are defined with sensible defaults but could be overridden via an
    # environment variable if needed (e.g., by setting a JSON string for MODELS).
    MODELS: dict[str, str] = {
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 2.0 Flash": "gemini-2.0-flash",
    }
    DEFAULT_MODELS: dict[str, str] = {
        "extraction": "Gemini 2.5 Flash",
        "evaluation": "Gemini 2.5 Pro"
    }

    # --- Computed Properties ---
    # These fields are derived from the settings above and are read-only.

    @computed_field
    @property
    def max_workers(self) -> int:
        """
        The maximum number of concurrent workers. Falls back to a sensible
        default based on the number of CPU cores if not set.
        """
        if self.MAX_WORKERS is not None:
            return self.MAX_WORKERS
        # A common formula: number of cores + a buffer for I/O-bound tasks
        return min(32, (os.cpu_count() or 1) + 4)

    @computed_field
    @property
    def model_names(self) -> list[str]:
        """A list of the user-friendly model names."""
        return list(self.MODELS.keys())

    @computed_field
    @property
    def default_extraction_model(self) -> str:
        """The default user-friendly model name for extraction tasks."""
        return self.DEFAULT_MODELS["extraction"]

    @computed_field
    @property
    def default_evaluation_model(self) -> str:
        """The default user-friendly model name for evaluation tasks."""
        return self.DEFAULT_MODELS["evaluation"]

    @computed_field
    @property
    def default_extraction_idx(self) -> int:
        """The list index of the default extraction model, useful for UI defaults."""
        try:
            return self.model_names.index(self.default_extraction_model)
        except ValueError:
            return 0  # Fallback to the first model if the default is not in the list

    @computed_field
    @property
    def default_evaluation_idx(self) -> int:
        """The list index of the default evaluation model, useful for UI defaults."""
        try:
            return self.model_names.index(self.default_evaluation_model)
        except ValueError:
            return 0  # Fallback to the first model if the default is not in the list

    # --- Validation ---
    @model_validator(mode='after')
    def _check_defaults_are_valid_models(self) -> 'Settings':
        """Ensures that every default model is a valid key in the MODELS dict."""
        for task, model_name in self.DEFAULT_MODELS.items():
            if model_name not in self.MODELS:
                raise ValueError(
                    f"Configuration Error: The default model '{model_name}' for "
                    f"task '{task}' is not defined in the main MODELS list."
                )
        return self

    # --- Model Configuration ---
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore"  # Good practice to ignore extra env vars
    )

# The single, global instance of the settings class that the application will import and use.
settings = Settings()