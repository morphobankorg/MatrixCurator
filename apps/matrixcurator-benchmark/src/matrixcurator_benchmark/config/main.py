# src/benchmark/config/main.py
from pydantic import Field

from matrixcurator.utils.concurrency import RateLimitConfig
from matrixcurator.config.main import Settings

class BenchmarkSettings(Settings):
    documents_parquet_path: str = "apps/matrixcurator-benchmark/src/matrixcurator_benchmark/data/documents.parquet"
    character_states_parquet_path: str = "apps/matrixcurator-benchmark/src/matrixcurator_benchmark/data/character_states.parquet"
    sqlite_cache_path: str = "apps/matrixcurator-benchmark/src/matrixcurator_benchmark/data/vector_store.sqlite"
    langfuse_rate_limit: RateLimitConfig = Field(default_factory=lambda: RateLimitConfig(per_minute=90))


settings = BenchmarkSettings()
