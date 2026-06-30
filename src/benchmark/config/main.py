# src/benchmark/config/main.py
from pydantic_settings import BaseSettings


class BenchmarkSettings(BaseSettings):
    documents_parquet_path: str = "src/benchmark/data/documents.parquet"
    character_states_parquet_path: str = "src/benchmark/data/character_states.parquet"
    parsed_cache_dir: str = ".cache/documents"
    sqlite_cache_path: str = ".cache/vector_store.sqlite"


settings = BenchmarkSettings()
